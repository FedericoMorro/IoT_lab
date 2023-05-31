import cherrypy
import paho.mqtt.client as PahoMQTT
import sqlite3
import json
import time

DB_NAME = "/SW_lab02/ex01/db_catalog.db"
DB_TABLES = ["devices", "device_end_points", "device_resources",
             "users", "user_emails",
             "services", "service_end_points"]


class Catalog():
    exposed = True


    def __init__(self):
        self._max_timestamp = 120 * 60
        self._delay_check_timestamp = 60 * 60

        self._loop()


    def _loop(self):
        while True:
            
            # TODO: check if timestamps are too old and delete them
            
            time.sleep(self._delay_check_timestamp)


    def GET(self, *uri, **params):      # retrieve
        pass


    def POST(self, *uri, **params):     # create
        
        # Check path correctness
        if not (len(uri) == 2 and uri[0] in ["devices", "users", "services"] and uri[1] == "subscription"):
            cherrypy.HTTPError(404, "POST available on \"type/subscription\" (type = \"devices\", \"users\" or \"services\")")
        
        # Get payload and convert it to JSON
        try:
            input_str = cherrypy.request.body.read()
            if len(input_str) == 0:
                cherrypy.HTTPError(400, "Empty POST")
        
            input_dict = json.loads(input_str)

        except ValueError as exc:
            cherrypy.HTTPError(400, f"Error in JSON to dictionary conversion: {exc}")
        except Exception as exc:
            cherrypy.HTTPError(500, f"An exception occurred: {exc}")

        # Add the new item to the database
        try:
            type = uri[0]
            timestamp = time.time()
            
            # Add the item in main tables and referenced ones
            if type == "device":
                self._insert_device(
                    device_id= input_dict["id"],
                    timestamp= timestamp,
                    end_points_dict= input_dict["end_points"],
                    resources_list= input_dict["info"]["resources"]
                )

            elif type == "user":
                self._insert_user(
                    user_id= input_dict["id"],
                    name= input_dict["info"]["name"],
                    surname= input_dict["info"]["surname"],
                    emails_list= input_dict["info"]["emails"]
                )

            elif type == "service":
                self._insert_service(
                    service_id= input_dict["id"],
                    timestamp= timestamp,
                    end_points_dict= input_dict["end_points"],
                    description= input_dict["info"]["description"] 
                )

            else:
                cherrypy.HTTPError(400, f"Unknown item type: {type}")

        except KeyError as exc:
            cherrypy.HTTPError(400, f"Missing or wrong key in JSON file: {exc}")
        except Exception as exc:
            cherrypy.HTTPError(500, f"An exception occurred: {exc}")


    def PUT(self, *uri, **params):      # update
        pass


    def DELETE(self, *uri, **params):   # delete
        pass



    def _execute_query(self, query, is_select = False):
        connection = None
        cursor = None

        try:
            connection = sqlite3.connect(DB_NAME)
        except sqlite3.Error as err:
            print(err)
            cherrypy.HTTPError(500, "Error in connection to the database")

        try:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
        except sqlite3.Error as err:
            print(err)
            cherrypy.HTTPError(500, f"Error in querying the database\nQuery:\n{query}")

        if is_select:
            output = cursor.fetchall()
        else:
            output = cursor.rowcount()
            if output <= 0:
                cherrypy.HTTPError(500, f"Error in database transaction\nQuery:\n{query}")

        cursor.close()
        connection.close()
        
        return output
            


    def _insert_device(self, device_id, timestamp, end_points_dict, resources_list):
        query = f"""
                INSERT INTO devices(device_id, timestamp)
                VALUES({device_id}, {timestamp});
                """
        self._execute_query(query)

        try:
            for type in end_points_dict:
                for end_point in end_points_dict[type]:
                    query = f"""
                            INSERT INTO device_end_points(device_id, end_point, type)
                            VALUES({device_id}, {end_point["value"]}, {type});
                            """
                    self._execute_query(query)
        
        except KeyError as exc:
            cherrypy.HTTPError(400, f"Missing or wrong key in JSON file: {exc}")
        except Exception as exc:
            cherrypy.HTTPError(500, f"An exception occurred: {exc}")

        try:
            for resource in resources_list:
                query = f"""
                        INSERT INTO device_resources(device_id, resource)
                        VALUES({device_id}, {resource["name"]});
                        """
                self._execute_query(query)
        
        except KeyError as exc:
            cherrypy.HTTPError(400, f"Missing or wrong key in JSON file: {exc}")
        except Exception as exc:
            cherrypy.HTTPError(500, f"An exception occurred: {exc}")


    def _insert_user(self, user_id, name, surname, emails_list):
        query = f"""
                INSERT INTO users(user_id, name, surname)
                VALUES({user_id}, {name}, {surname});
                """
        self._execute_query(query)

        try:
            for email in emails_list:
                query = f"""
                        INSERT INTO user_emails(user_id, email)
                        VALUES({user_id}, {email["value"]});
                        """
                self._execute_query(query)
        
        except KeyError as exc:
            cherrypy.HTTPError(400, f"Missing or wrong key in JSON file: {exc}")
        except Exception as exc:
            cherrypy.HTTPError(500, f"An exception occurred: {exc}")


    def _insert_service(self, service_id, timestamp, end_points_dict, description):
        query = f"""
                INSERT INTO services(service_id, description, timestamp)
                VALUES({service_id}, {description}, {timestamp});
                """
        self._execute_query(query)

        try:
            for type in end_points_dict:
                for end_point in end_points_dict[type]:
                    query = f"""
                            INSERT INTO service_end_points(service_id, end_point, type)
                            VALUES({service_id}, {end_point["value"]}, {type});
                            """
                    self._execute_query(query)
        
        except KeyError as exc:
            cherrypy.HTTPError(400, f"Missing or wrong key in JSON file: {exc}")
        except Exception as exc:
            cherrypy.HTTPError(500, f"An exception occurred: {exc}")





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