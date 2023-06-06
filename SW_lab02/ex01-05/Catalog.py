import cherrypy
import paho.mqtt.client as PahoMQTT
import sqlite3
import json
import time
import threading

DB_NAME = "db_catalog.db"
DB_TABLES = ["devices", "device_end_points", "device_resources",
             "users", "user_emails",
             "services", "service_end_points"]


class Catalog():

    exposed = True

    def __init__(self):
        self._max_timestamp = 120
        self._delay_check_timestamp = 60

        self._db_name = DB_NAME

        self._client_id = "IoT_lab_group3_Catalog"
        self._broker_hostname = "test.mosquitto.org"
        self._broker_port = 1883
        self._base_topic = "/IoT_lab/group3/catalog"

        # Initialize MQTT
        self._mqtt_client = PahoMQTT.Client(self._client_id, clean_session=False)
        self._mqtt_client.on_message = self.callback_on_MQTT_message

        self._mqtt_client.connect(self._broker_hostname, self._broker_port)
        self._mqtt_client.loop_start()

        self._subscribed_topics = []
        for item in ["devices", "services", "users"]:
            for operation in ["subscription", "refresh"]:
                self._subscribed_topics.append((f"{self._base_topic}/{item}/{operation}", 2))
        self._mqtt_client.subscribe(self._subscribed_topics)

        # Initialize thread
        self._thread = threading.Thread(target=self.callback_delete_old)
        self._thread.start()


    def __del__(self):
        self._mqtt_client.unsubscribe(self._subscribed_topics)
        self._mqtt_client.loop_stop()
        self._mqtt_client.disconnect()

        self._thread.join()



    def callback_delete_old(self):
        # Delete devices with timestamp higher than _max_timestamp
        while True:
            timestamp = int(time.time())
            
            for type in ["device", "service"]:
                items_list = self.get_all_items(type)

                for item in items_list:
                    item_id = item[0]

                    item_timestamp = self.get_timestamp(type, item_id)
                    if (timestamp - item_timestamp) > self._max_timestamp:
                        self.delete_item(type, item_id)
            
            time.sleep(self._delay_check_timestamp)



    def callback_on_MQTT_message(self, paho_mqtt, userdata, msg):
        # Get the payload and convert in to dictionary
        try:
            input_str = msg.payload.decode("utf-8")     # to convert from bytes to text, otherwise payload is like "b'text"
            input_dict = json.loads(input_str)

        except ValueError as exc:
            self._mqtt_client.publish(
                topic= f"{self._base_topic}/{type}s/{input_dict['id']}",
                payload= self.json_dict_to_str({"err": 1, "msg": f"Error in input JSON to dictionary conversion: {exc}"}),
                qos= 2
            )
        except Exception as exc:
            self._mqtt_client.publish(
                topic= f"{self._base_topic}/{type}s/{input_dict['id']}",
                payload= self.json_dict_to_str({"err": 1, "msg": f"An exception occurred: {exc}"}),
                qos= 2
            )
        
        # Check topic
        topic_elem = msg.topic.split("/")
        type = topic_elem[3].removesuffix("s")
        operation = topic_elem[4]

        # Perform subscription or refresh
        if operation == "subscription":
            self.insert_item(
                json_dict= input_dict,
                type= type,
                timestamp= int(time.time())
            )
        elif operation == "refresh":
            self.update_item(
                json_dict= input_dict,
                type= type,
                timestamp= int(time.time())
            )

        # Publish response message
        self._mqtt_client.publish(
            topic= f"{self._base_topic}/{type}s/{input_dict['id']}",
            payload= self.json_dict_to_str({"err": 0}),
            qos= 2
        )



    def GET(self, *uri, **params):      # retrieve
        # Give possibility to ask for MQTT broker
        if (len(uri) == 1 and uri[0] == "MQTTbroker"):
            output_dict = {"hostname": self._mqtt_broker_hostname, "port": self._mqtt_broker_port, "base_topic": self._base_topic}
            return self.json_dict_to_str(output_dict)
        
        # Check path correctness
        if not (1 <= len(uri) <= 2 and uri[0] in ["devices", "users", "services"]):
            raise cherrypy.HTTPError(404, "GET available on \"type\" or \"type/item_id\" (type = \"devices\", \"users\" or \"services\")")

        type = uri[0].removesuffix("s")

        if len(uri) == 2:
            return self.get_item(type, uri[1])

        output_dict = []
        items_list = self.get_all_items(type)

        for item in items_list:
            output_dict.append(self.get_item(type, item[0]))

        return self.json_dict_to_str(output_dict)


    def POST(self, *uri, **params):     # create
        # Check path correctness
        if not (len(uri) == 2 and uri[0] in ["devices", "users", "services"] and uri[1] == "subscription"):
            raise cherrypy.HTTPError(404, "POST available on \"type/subscription\" (type = \"devices\", \"users\" or \"services\")")
        
        # Get payload and convert it to JSON
        try:
            input_str = cherrypy.request.body.read()
            if len(input_str) == 0:
                raise cherrypy.HTTPError(400, "Empty POST")
        
            input_dict = json.loads(input_str)

        except ValueError as exc:
            raise cherrypy.HTTPError(400, f"Error in input JSON to dictionary conversion: {exc}")
        except Exception as exc:
            raise cherrypy.HTTPError(500, f"An exception occurred: {exc}")

        # Add the new item to the database
        self.insert_item(
            json_dict= input_dict,
            type= uri[0].removesuffix("s"),
            timestamp= int(time.time())
        )
        
        return f"Operation on {uri[0].removesuffix('s')}:{input_dict['id']} correctly performed"


    def PUT(self, *uri, **params):      # update
        # Check path correctness
        if not (len(uri) == 2 and uri[0] in ["devices", "services"] and uri[1] == "refresh"):
            raise cherrypy.HTTPError(404, "PUT available on \"type/refresh\" (type = \"devices\" or \"services\")")
        
        # Get payload and convert it to JSON
        try:
            input_str = cherrypy.request.body.read()
            if len(input_str) == 0:
                raise cherrypy.HTTPError(400, "Empty POST")
        
            input_dict = json.loads(input_str)

        except ValueError as exc:
            raise cherrypy.HTTPError(400, f"Error in input JSON to dictionary conversion: {exc}")
        except Exception as exc:
            raise cherrypy.HTTPError(500, f"An exception occurred: {exc}")

        # Update item
        self.update_item(
            json_dict= input_dict,
            type= uri[0].removesuffix("s"),
            timestamp= int(time.time())
        )
        
        return f"Operation on {uri[0].removesuffix('s')}:{input_dict['id']} correctly performed"


    def DELETE(self, *uri, **params):   # delete
        # Check path correctness
        if not (len(uri) == 2 and uri[0] in ["devices", "users", "services"]):
            raise cherrypy.HTTPError(404, "DELETE available on \"type/item_id\" (type = \"devices\", \"users\" or \"services\")")

        # Delete the item from the database
        try:
            self.delete_item(
                type= uri[0].removesuffix("s"),
                item_id= uri[1]
            )

        except Exception as exc:
            raise cherrypy.HTTPError(500, f"An exception occurred: {exc}")
        
        return f"Operation on {uri[0].removesuffix('s')}:{uri[1]} correctly performed"
            


    def insert_item(self, json_dict, type, timestamp):
        # Add the item in main tables and referenced ones
        try:
            item_id = json_dict["id"]

            # Check if it's already present
            if self.is_present(type, item_id):
                raise cherrypy.HTTPError(400, f"Item {type}:{item_id} already present in the catalog (insert)")
            
            if type == "device":
                self.insert_device(
                    device_id= item_id,
                    timestamp= timestamp,
                    end_points_dict= json_dict["end_points"],
                    resources_list= json_dict["info"]["resources"]
                )
            elif type == "user":
                self.insert_user(
                    user_id= item_id,
                    name= json_dict["info"]["name"],
                    surname= json_dict["info"]["surname"],
                    emails_list= json_dict["info"]["emails"]
                )
            elif type == "service":
                self.insert_service(
                    service_id= item_id,
                    timestamp= timestamp,
                    end_points_dict= json_dict["end_points"],
                    description= json_dict["info"]["description"] 
                )

        except KeyError as exc:
            raise cherrypy.HTTPError(400, f"Missing or wrong key in JSON file: {exc}")
        except Exception as exc:
            raise cherrypy.HTTPError(500, f"An exception occurred: {exc}")
        

    def update_item(self, json_dict, type, timestamp):
        try:
            item_id = json_dict["id"]

            # If it's not present (probably elapsed timestamp), add the device
            if not self.is_present(type, item_id):
                self.insert_item(json_dict, type, timestamp)

            else:
                # If info stored different from the one received, delete entry and re-add it to the catalog
                stored_data_str = self.json_dict_to_str(self.get_item(type, item_id))
                if stored_data_str != json.dumps(json_dict):
                    self.delete_item(type, item_id)
                    self.insert_item(json_dict, type, timestamp)

                # Otherwise simply update the timestamp
                else:
                    self.update_timestamp(type, item_id, timestamp)
        
        except KeyError as exc:
            raise cherrypy.HTTPError(400, f"Missing or wrong key in JSON file: {exc}")
        except Exception as exc:
            raise cherrypy.HTTPError(500, f"An exception occurred: {exc}")
        


    def get_all_items(self, type):
        query = f"""
                SELECT {type}_id
                FROM {type}s;
                """
        result = self.execute_query(query, is_select=True)

        return result
    

    def get_item(self, type, item_id):
        if not self.is_present(type, item_id):
            raise cherrypy.HTTPError(400, f"Item {type}:{item_id} not present in the catalog (get)")

        if type == "device":
            return self.get_device(item_id)
        elif type == "user":
            return self.get_user(item_id)
        elif type == "service":
            return self.get_service(item_id)



    def is_present(self, type, item_id):
        query = f"""
                SELECT *
                FROM {type}s
                WHERE {type}_id = '{item_id}';
                """
        result = self.execute_query(query, is_select=True)
        
        if len(result) == 0:
            return False
        return True



    def delete_item(self, type, item_id):
        if type == "device":
            self.delete_item_referenced_tables(type, item_id, "device_end_points")
            self.delete_item_referenced_tables(type, item_id, "device_resources")
        elif type == "user":
            self.delete_item_referenced_tables(type, item_id, "user_emails")
        elif type == "service":
            self.delete_item_referenced_tables(type, item_id, "service_end_points")

        query = f"""
                DELETE FROM {type}s
                WHERE {type}_id = '{item_id}';
                """
        self.execute_query(query)
        

    
    def insert_device(self, device_id, timestamp, end_points_dict, resources_list):
        query = f"""
                INSERT INTO devices(device_id, timestamp)
                VALUES('{device_id}', {timestamp});
                """
        self.execute_query(query)

        self.insert_end_points(
            type= "device",
            item_id= device_id,
            end_points_dict= end_points_dict
        )

        try:
            for resource in resources_list:
                query = f"""
                        INSERT INTO device_resources(device_id, resource)
                        VALUES('{device_id}', '{resource["name"]}');
                        """
                self.execute_query(query)
        
        except KeyError as exc:
            raise cherrypy.HTTPError(400, f"Missing or wrong key in JSON file: {exc}")
        except Exception as exc:
            raise cherrypy.HTTPError(500, f"An exception occurred: {exc}")


    def insert_user(self, user_id, name, surname, emails_list):
        query = f"""
                INSERT INTO users(user_id, name, surname)
                VALUES('{user_id}', '{name}', '{surname}');
                """
        self.execute_query(query)

        try:
            for email in emails_list:
                query = f"""
                        INSERT INTO user_emails(user_id, email)
                        VALUES('{user_id}', '{email["value"]}');
                        """
                self.execute_query(query)
        
        except KeyError as exc:
            raise cherrypy.HTTPError(400, f"Missing or wrong key in JSON file: {exc}")
        except Exception as exc:
            raise cherrypy.HTTPError(500, f"An exception occurred: {exc}")


    def insert_service(self, service_id, timestamp, end_points_dict, description):
        query = f"""
                INSERT INTO services(service_id, description, timestamp)
                VALUES(''{service_id}', '{description}', {timestamp});
                """
        self.execute_query(query)

        self.insert_end_points(
            type= "service",
            item_id= service_id,
            end_points_dict= end_points_dict
        )


    def insert_end_points(self, type, item_id, end_points_dict):
        try:
            for protocol in end_points_dict:
                for method in end_points_dict[protocol]:
                    for end_point in end_points_dict[protocol][method]:
                        query = f"""
                                INSERT INTO {type}_end_points({type}_id, end_point, protocol, method)
                                VALUES('{item_id}', '{end_point["value"]}', '{protocol}', '{method}');
                                """
                        self.execute_query(query)
        
        except KeyError as exc:
            raise cherrypy.HTTPError(400, f"Missing or wrong key in JSON file: {exc}")
        except Exception as exc:
            raise cherrypy.HTTPError(500, f"An exception occurred: {exc}")
        


    def get_device(self, device_id):
        output_dict = {}
        output_dict["id"] = device_id
        output_dict["end_points"] = self.get_end_points("device", device_id)
        output_dict["info"] = {}

        query = f"""
                SELECT resource
                FROM device_resources
                WHERE device_id = '{device_id}';
                """
        result = self.execute_query(query, is_select=True)

        for row in result:
            resource = row[0]

            if "resources" not in output_dict["info"]:
                output_dict["info"]["resources"] = []
            output_dict["info"]["resources"].append({"name": resource})

        return self.json_dict_to_str(output_dict)


    def get_user(self, user_id):
        output_dict = {}
        output_dict["id"] = user_id
        output_dict["info"] = {}

        query = f"""
                SELECT name, surname
                FROM users
                WHERE user_id = '{user_id}';
                """
        result = self.execute_query(query, is_select=True)

        output_dict["info"]["name"] = result[0]
        output_dict["info"]["surname"] = result[1]

        query = f"""
                SELECT email
                FROM user_emails
                WHERE user_id = '{user_id}';
                """
        result = self.execute_query(query, is_select=True)

        for row in result:
            email = row[0]

            if "emails" not in output_dict["info"]:
                output_dict["info"]["emails"] = []
            output_dict["info"]["emails"].append({"value": email})

        return self.json_dict_to_str(output_dict)


    def get_service(self, service_id):
        output_dict = {}
        output_dict["id"] = service_id
        output_dict["end_points"] = self.get_end_points("service", service_id)
        output_dict["info"] = {}

        query = f"""
                SELECT description
                FROM services
                WHERE service_id = '{service_id}';
                """
        result = self.execute_query(query, is_select=True)

        output_dict["info"]["description"] = result[0]

        return self.json_dict_to_str(output_dict)
        

    def get_end_points(self, type, item_id):
        res_dict = {}
        query = f"""
                SELECT end_point, protocol, method
                FROM {type}_end_points
                WHERE {type}_id = '{item_id}';
                """
        result = self.execute_query(query, is_select=True)

        for row in result:
            end_point = row[0]
            protocol = row[1]
            method = row[2]
            
            if protocol not in res_dict:
                res_dict[protocol] = {}
            if method not in res_dict[protocol]:
                res_dict[protocol][method] = []

            res_dict[protocol][method].append({"value": end_point})

        return res_dict



    def get_timestamp(self, type, item_id):
        query = f"""
                SELECT timestamp
                FROM {type}s
                WHERE {type}_id = '{item_id}';
                """
        result = self.execute_query(query, is_select=True)

        return result[0][0]
    

    def update_timestamp(self, type, item_id, timestamp):
        query = f"""
                UPDATE {type}s
                SET timestamp = {timestamp}
                WHERE {type}_id = '{item_id}';
                """
        self.execute_query(query)



    def delete_item_referenced_tables(self, type, item_id, table):
        query = f"""
                DELETE FROM {table}
                WHERE {type}_id = '{item_id}';
                """
        self.execute_query(query)



    def execute_query(self, query, is_select = False):
        connection = None
        cursor = None

        try:
            connection = sqlite3.connect(self._db_name)
        except sqlite3.Error as err:
            print(err)
            raise cherrypy.HTTPError(500, "Error in connection to the database")

        try:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
        except sqlite3.Error as err:
            print(err)
            raise cherrypy.HTTPError(500, f"Error in querying the database\nQuery:\n{query}")

        if is_select:
            output = cursor.fetchall()
        else:
            output = cursor.rowcount
            if output <= 0:
                raise cherrypy.HTTPError(500, f"Error in database transaction\nQuery:\n{query}")

        cursor.close()
        connection.close()
        
        return output



    def json_dict_to_str(self, json_dict):
        try:
            json_str = json.dumps(json_dict)
        except ValueError as exc:
            raise cherrypy.HTTPError(500, f"Error in dictionary to output JSON conversion: {exc}")
        except Exception as exc:
            raise cherrypy.HTTPError(500, f"An exception occurred: {exc}")
        
        return json_str





if __name__=='__main__':
    conf={
        '/':{
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }
    
    cherrypy.tree.mount(Catalog(), '/', conf)

    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.engine.start()
    cherrypy.engine.block()