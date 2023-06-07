import cherrypy
import paho.mqtt.client as PahoMQTT
import sqlite3
import json
import time
import threading


CATALOG_IP_ADDR = "127.0.0.1"
CATALOG_PORT = 8080

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
        self._base_topic = "/tiot/g03/cat"

        # Initialize MQTT
        self._mqtt_client = PahoMQTT.Client(self._client_id, clean_session=False)
        self._mqtt_client.on_message = self.callback_on_MQTT_message
        self._mqtt_client.on_connect = self.callback_on_MQTT_connect

        self._mqtt_client.connect(self._broker_hostname, self._broker_port)
        self._mqtt_client.loop_start()

        self._subscribed_topics = []
        for item in ["devices", "services", "users"]:
            for operation in ["sub", "upd"]:
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


    
    def callback_on_MQTT_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker")



    def callback_delete_old(self):
        print_err_handler = self.ErrorHandler()

        # Delete devices with timestamp higher than _max_timestamp
        while True:
            timestamp = int(time.time())
            
            for type in ["device", "service"]:
                items_list = self.get_all_items(type, print_err_handler)

                for item in items_list:
                    item_id = item[0]

                    item_timestamp = self.get_timestamp(type, item_id, print_err_handler)
                    if (timestamp - item_timestamp) > self._max_timestamp:
                        self.delete_item(type, item_id, print_err_handler)
            
            time.sleep(self._delay_check_timestamp)



    def callback_on_MQTT_message(self, paho_mqtt, userdata, msg):
        print(f"MQTT: message received on {msg.topic}: {msg.payload}")

        # Get the payload and convert in to dictionary and check topic
        try:
            input_str = msg.payload.decode("utf-8")     # to convert from bytes to text, otherwise payload is like "b'text"
            input_dict = json.loads(input_str)

            topic_elem = msg.topic.split("/")
            type = topic_elem[4].removesuffix("s")
            operation = topic_elem[5]

            # Cannot be defined before, since the topic is unknown
            mqtt_err_handler = self.MqttErrorHandler(
                topic= f'{self._base_topic}/{type}s/{input_dict["id"]}',
                mqtt_client= self._mqtt_client
            )

        except KeyError as exc:
            print(f"ERROR: Missing or wrong key in input JSON: {exc}")
            return
        except ValueError as exc:
            print(f"ERROR: Error in input JSON to dictionary conversion: {exc}")
            return
        except Exception as exc:
            print(f"ERROR: An exception occurred: {exc}")
            return

        # Perform subscription or refresh
        if operation == "sub":
            self.insert_item(
                json_dict= input_dict,
                type= type,
                timestamp= int(time.time()),
                err_handler= mqtt_err_handler
            )
        elif operation == "ref":
            self.update_item(
                json_dict= input_dict,
                type= type,
                timestamp= int(time.time()),
                err_handler= mqtt_err_handler
            )

        # Publish response message
        self._mqtt_client.publish(
            topic= f"{self._base_topic}/{type}s/{input_dict['id']}",
            payload= self.json_dict_to_str({"e": 0}, mqtt_err_handler),
            qos= 2
        )

        print(f"MQTT: message sent on {self._base_topic}/{type}s/{input_dict['id']}: {self.json_dict_to_str({'in': {'e': 0}}, mqtt_err_handler)}")



    def GET(self, *uri, **params):      # retrieve
        rest_err_handler = self.RestErrorHandler()

        # Give possibility to ask for Catalog info about subscription
        if (len(uri) == 0):
            output_dict = {
                "ep": {
                    "r": {
                        "hn": [{"v": CATALOG_IP_ADDR}],
                        "pt": [{"v": CATALOG_PORT}],
                        "r": [{"v": "/devices"}, {"v": "/users"}, {"v": "/services"}],
                        "c": [{"v": "/devices/sub"}, {"v": "/users/sub"}, {"v": "/services/sub"}],
                        "u": [{"v": "/devices/upd"}, {"v": "/users/upd"}, {"v": "/services/upd"}],
                        "d": [{"v": "/devices/#"}, {"v": "/users/#"}, {"v": "/services/#"}]
                    },
                    "m": {
                        "bt": [{"v": self._base_topic}],
                        "p": [{"v": "/devices/#"}, {"v": "/users/#"}, {"v": "/services/#"}],
                        "s": [{"v": "/devices/sub"}, {"v": "/users/sub"}, {"v": "/services/sub"},
                              {"v": "/devices/upd"}, {"v": "/users/upd"}, {"v": "/services/upd"}]
                    }
                }
            }
            return self.json_dict_to_str(output_dict, rest_err_handler)

        # Give possibility to ask for MQTT broker
        if (len(uri) == 1 and uri[0] == "MQTTbroker"):
            output_dict = {
                "ep": {
                    "r": {
                        "hn": [{"v": self._broker_hostname}],
                        "pt": [{"v": self._broker_port}]
                    },
                    "m": {
                        "bt": [{"v": self._base_topic}]
                    }
                }
            }
            return self.json_dict_to_str(output_dict, rest_err_handler)
        
        # Check path correctness
        if not (1 <= len(uri) <= 2 and uri[0] in ["devices", "users", "services"]):
            raise cherrypy.HTTPError(404, "GET available on \"type\" or \"type/item_id\" (type = \"devices\", \"users\" or \"services\")")

        type = uri[0].removesuffix("s")

        if len(uri) == 2:
            return self.get_item(type, uri[1], rest_err_handler)

        output_dict = []
        items_list = self.get_all_items(type, rest_err_handler)

        for item in items_list:
            output_dict.append(self.get_item(type, item[0], rest_err_handler))

        return self.json_dict_to_str(output_dict, rest_err_handler)


    def POST(self, *uri, **params):     # create
        rest_err_handler = self.RestErrorHandler()

        # Check path correctness
        if not (len(uri) == 2 and uri[0] in ["devices", "users", "services"] and uri[1] == "sub"):
            raise cherrypy.HTTPError(404, "POST available on \"type/sub\" (type = \"devices\", \"users\" or \"services\")")
        
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
            timestamp= int(time.time()),
            err_handler= rest_err_handler
        )
        
        return f"Operation on {uri[0].removesuffix('s')}:{input_dict['id']} correctly performed"


    def PUT(self, *uri, **params):      # update
        rest_err_handler = self.RestErrorHandler()

        # Check path correctness
        if not (len(uri) == 2 and uri[0] in ["devices", "services"] and uri[1] == "upd"):
            raise cherrypy.HTTPError(404, "PUT available on \"type/upd\" (type = \"devices\" or \"services\")")
        
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
            timestamp= int(time.time()),
            err_handler= rest_err_handler
        )
        
        return f"Operation on {uri[0].removesuffix('s')}:{input_dict['id']} correctly performed"


    def DELETE(self, *uri, **params):   # delete
        rest_err_handler = self.RestErrorHandler()

        # Check path correctness
        if not (len(uri) == 2 and uri[0] in ["devices", "users", "services"]):
            raise cherrypy.HTTPError(404, "DELETE available on \"type/item_id\" (type = \"devices\", \"users\" or \"services\")")

        # Delete the item from the database
        try:
            self.delete_item(
                type= uri[0].removesuffix("s"),
                item_id= uri[1],
                err_handler= rest_err_handler
            )

        except Exception as exc:
            raise cherrypy.HTTPError(500, f"An exception occurred: {exc}")
        
        return f"Operation on {uri[0].removesuffix('s')}:{uri[1]} correctly performed"
            


    def insert_item(self, json_dict, type, timestamp, err_handler):
        # Add the item in main tables and referenced ones
        try:
            item_id = json_dict["id"]

            # Check if it's already present
            if self.is_present(type, item_id, err_handler):
                raise cherrypy.HTTPError(400, f"Item {type}:{item_id} already present in the catalog (insert)")
            
            if type == "device":
                self.insert_device(
                    device_id= item_id,
                    timestamp= timestamp,
                    end_points_dict= json_dict["ep"],
                    resources_list= json_dict["in"]["r"],
                    err_handler= err_handler
                )
            elif type == "user":
                self.insert_user(
                    user_id= item_id,
                    name= json_dict["in"]["n"],
                    surname= json_dict["in"]["s"],
                    emails_list= json_dict["in"]["e"],
                    err_handler= err_handler
                )
            elif type == "service":
                self.insert_service(
                    service_id= item_id,
                    timestamp= timestamp,
                    end_points_dict= json_dict["ep"],
                    description= json_dict["in"]["d"],
                    err_handler= err_handler 
                )

        except KeyError as exc:
            err_handler.notify(400, f"Missing or wrong key in JSON file: {exc}")
            return
        except Exception as exc:
            err_handler.notify(500, f"An exception occurred: {exc}")
            return
        

    def update_item(self, json_dict, type, timestamp, err_handler):
        try:
            item_id = json_dict["id"]

            # If it's not present (probably elapsed timestamp), add the device
            if not self.is_present(type, item_id, err_handler):
                self.insert_item(json_dict, type, timestamp, err_handler)

            else:
                # If info stored different from the one received, delete entry and re-add it to the catalog
                stored_data_str = self.json_dict_to_str(self.get_item(type, item_id, err_handler), err_handler)
                if stored_data_str != json.dumps(json_dict):
                    self.delete_item(type, item_id, err_handler)
                    self.insert_item(json_dict, type, timestamp, err_handler)

                # Otherwise simply update the timestamp
                else:
                    self.update_timestamp(type, item_id, timestamp, err_handler)
        
        except KeyError as exc:
            err_handler.notify(400, f"Missing or wrong key in JSON file: {exc}")
            return
        except Exception as exc:
            err_handler.notify(500, f"An exception occurred: {exc}")
            return
        


    def get_all_items(self, type, err_handler):
        query = f"""
                SELECT {type}_id
                FROM {type}s;
                """
        result = self.execute_query(query, err_handler, is_select=True)

        return result
    

    def get_item(self, type, item_id, err_handler):
        if not self.is_present(type, item_id, err_handler):
            err_handler.notify(400, f"Item {type}:{item_id} not present in the catalog (get)")
            return

        if type == "device":
            return self.get_device(item_id, err_handler)
        elif type == "user":
            return self.get_user(item_id, err_handler)
        elif type == "service":
            return self.get_service(item_id, err_handler)



    def is_present(self, type, item_id, err_handler):
        query = f"""
                SELECT *
                FROM {type}s
                WHERE {type}_id = '{item_id}';
                """
        result = self.execute_query(query, err_handler, is_select=True)
        
        if len(result) == 0:
            return False
        return True



    def delete_item(self, type, item_id, err_handler):
        if not self.is_present(type, item_id, err_handler):
            err_handler.notify(400, f"Item {type}:{item_id} not present in the catalog (get)")
            return

        if type == "device":
            self.delete_item_referenced_tables(type, item_id, "device_end_points", err_handler)
            self.delete_item_referenced_tables(type, item_id, "device_resources", err_handler)
        elif type == "user":
            self.delete_item_referenced_tables(type, item_id, "user_emails", err_handler)
        elif type == "service":
            self.delete_item_referenced_tables(type, item_id, "service_end_points", err_handler)

        query = f"""
                DELETE FROM {type}s
                WHERE {type}_id = '{item_id}';
                """
        self.execute_query(query, err_handler)
        

    
    def insert_device(self, device_id, timestamp, end_points_dict, resources_list, err_handler):
        query = f"""
                INSERT INTO devices(device_id, timestamp)
                VALUES('{device_id}', {timestamp});
                """
        self.execute_query(query, err_handler)

        self.insert_end_points(
            type= "device",
            item_id= device_id,
            end_points_dict= end_points_dict,
            err_handler= err_handler
        )

        try:
            for resource in resources_list:
                query = f"""
                        INSERT INTO device_resources(device_id, resource)
                        VALUES('{device_id}', '{resource["n"]}');
                        """
                self.execute_query(query, err_handler)
        
        except KeyError as exc:
            err_handler.notify(400, f"Missing or wrong key in JSON file: {exc}")
            return
        except Exception as exc:
            err_handler.notify(500, f"An exception occurred: {exc}")
            return


    def insert_user(self, user_id, name, surname, emails_list, err_handler):
        query = f"""
                INSERT INTO users(user_id, name, surname)
                VALUES('{user_id}', '{name}', '{surname}');
                """
        self.execute_query(query, err_handler)

        try:
            for email in emails_list:
                query = f"""
                        INSERT INTO user_emails(user_id, email)
                        VALUES('{user_id}', '{email["v"]}');
                        """
                self.execute_query(query, err_handler)
        
        except KeyError as exc:
            err_handler.notify(400, f"Missing or wrong key in JSON file: {exc}")
            return
        except Exception as exc:
            err_handler.notify(500, f"An exception occurred: {exc}")
            return


    def insert_service(self, service_id, timestamp, end_points_dict, description, err_handler):
        query = f"""
                INSERT INTO services(service_id, description, timestamp)
                VALUES(''{service_id}', '{description}', {timestamp});
                """
        self.execute_query(query, err_handler)

        self.insert_end_points(
            type= "service",
            item_id= service_id,
            end_points_dict= end_points_dict,
            err_handler= err_handler
        )


    def insert_end_points(self, type, item_id, end_points_dict, err_handler):
        try:
            for protocol in end_points_dict:
                for method in end_points_dict[protocol]:
                    for end_point in end_points_dict[protocol][method]:
                        query = f"""
                                INSERT INTO {type}_end_points({type}_id, end_point, protocol, method)
                                VALUES('{item_id}', '{end_point["v"]}', '{protocol}', '{method}');
                                """
                        self.execute_query(query, err_handler)
        
        except KeyError as exc:
            err_handler.notify(400, f"Missing or wrong key in JSON file: {exc}")
            return
        except Exception as exc:
            err_handler.notify(500, f"An exception occurred: {exc}")
            return
        


    def get_device(self, device_id, err_handler):
        output_dict = {}
        output_dict["id"] = device_id
        output_dict["ep"] = self.get_end_points("device", device_id, err_handler)
        output_dict["in"] = {}

        query = f"""
                SELECT resource
                FROM device_resources
                WHERE device_id = '{device_id}';
                """
        result = self.execute_query(query, err_handler, is_select=True)

        for row in result:
            resource = row[0]

            if "resources" not in output_dict["in"]:
                output_dict["in"]["r"] = []
            output_dict["in"]["r"].append({"n": resource})

        return self.json_dict_to_str(output_dict, err_handler)


    def get_user(self, user_id, err_handler):
        output_dict = {}
        output_dict["id"] = user_id
        output_dict["in"] = {}

        query = f"""
                SELECT name, surname
                FROM users
                WHERE user_id = '{user_id}';
                """
        result = self.execute_query(query, err_handler, is_select=True)

        output_dict["in"]["n"] = result[0]
        output_dict["in"]["s"] = result[1]

        query = f"""
                SELECT email
                FROM user_emails
                WHERE user_id = '{user_id}';
                """
        result = self.execute_query(query, err_handler, is_select=True)

        for row in result:
            email = row[0]

            if "emails" not in output_dict["in"]:
                output_dict["in"]["e"] = []
            output_dict["in"]["e"].append({"v": email})

        return self.json_dict_to_str(output_dict, err_handler)


    def get_service(self, service_id, err_handler):
        output_dict = {}
        output_dict["id"] = service_id
        output_dict["ep"] = self.get_end_points("service", service_id, err_handler)
        output_dict["in"] = {}

        query = f"""
                SELECT description
                FROM services
                WHERE service_id = '{service_id}';
                """
        result = self.execute_query(query, err_handler, is_select=True)

        output_dict["in"]["d"] = result[0]

        return self.json_dict_to_str(output_dict, err_handler)
        

    def get_end_points(self, type, item_id, err_handler):
        res_dict = {}
        query = f"""
                SELECT end_point, protocol, method
                FROM {type}_end_points
                WHERE {type}_id = '{item_id}';
                """
        result = self.execute_query(query, err_handler, is_select=True)

        for row in result:
            end_point = row[0]
            protocol = row[1]
            method = row[2]
            
            if protocol not in res_dict:
                res_dict[protocol] = {}
            if method not in res_dict[protocol]:
                res_dict[protocol][method] = []

            res_dict[protocol][method].append({"v": end_point})

        return res_dict



    def get_timestamp(self, type, item_id, err_handler):
        query = f"""
                SELECT timestamp
                FROM {type}s
                WHERE {type}_id = '{item_id}';
                """
        result = self.execute_query(query, err_handler, is_select=True)

        return result[0][0]
    

    def update_timestamp(self, type, item_id, timestamp, err_handler):
        query = f"""
                UPDATE {type}s
                SET timestamp = {timestamp}
                WHERE {type}_id = '{item_id}';
                """
        self.execute_query(query, err_handler)



    def delete_item_referenced_tables(self, type, item_id, table, err_handler):
        query = f"""
                DELETE FROM {table}
                WHERE {type}_id = '{item_id}';
                """
        self.execute_query(query, err_handler)



    def execute_query(self, query, err_handler, is_select = False):
        connection = None
        cursor = None

        try:
            connection = sqlite3.connect(self._db_name)
        except sqlite3.Error as err:
            print(err)
            err_handler.notify(500, "Error in connection to the database")
            return

        try:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
        except sqlite3.Error as err:
            print(err)
            err_handler.notify(500, f"Error in querying the database\nQuery:\n{query}")
            return

        if is_select:
            output = cursor.fetchall()
        else:
            output = cursor.rowcount
            if output < 0:
                err_handler.notify(500, f"Error in database transaction\nQuery:\n{query}")
                return

        cursor.close()
        connection.close()
        
        return output



    def json_dict_to_str(self, json_dict, err_handler):
        try:
            json_str = json.dumps(json_dict)
        except ValueError as exc:
            err_handler.notify(500, f"Error in dictionary to output JSON conversion: {exc}")
            return
        except Exception as exc:
            err_handler.notify(500, f"An exception occurred: {exc}")
            return
        
        return json_str
    


    class ErrorHandler():
        
        def notify(self, param, msg):
            print(f"ERROR: an error occured: [{param}] {msg}")
        

    class MqttErrorHandler(ErrorHandler):
        def __init__(self, topic, mqtt_client):
            self._topic = topic
            self._mqtt_client = mqtt_client

        def notify(self, param, msg):
            super().notify(param, msg)
            self._mqtt_client.publish(
                topic= self._topic,
                payload= json.dumps({"in": {"e": 1, "m": f"{msg}"}}),
                qos= 2
            )


    class RestErrorHandler(ErrorHandler):
        
        def notify(self, param, msg):
            super().notify(param, msg)
            raise cherrypy.HTTPError(param, msg)




if __name__=='__main__':
    conf={
        '/':{
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }
    
    cherrypy.tree.mount(Catalog(), '/', conf)

    cherrypy.config.update({'server.socket_host': CATALOG_IP_ADDR})
    cherrypy.config.update({'server.socket_port': CATALOG_PORT})

    cherrypy.engine.start()
    cherrypy.engine.block()