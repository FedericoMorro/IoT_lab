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
        if not (len(uri) == 1 and uri[0] == "register"):
            cherrypy.HTTPError(404, "Only POST on \"register\" is implemented")
        
        # Get payload and convert it to JSON
        try:
            input_str = cherrypy.request.body.read()
            if len(input_str) == 0:
                cherrypy.HTTPError(400, "Empty POST")
        
            input_dict = json.loads(input_str)

        except ValueError as exc:
            cherrypy.HTTPError(400, f"Error in JSON to dictionary conversion: {exc}")
        except Exception as exc:
            cherrypy.HTTPError(400, f"An exception occurred: {exc}")

        # Add the new item to the database
        try:
            type = input_dict["type"]
            timestamp = time.time()
            
            # Add the item in main tables and referenced ones
            if type == "device":
                query = f"""
                INSERT INTO devices(device_id, timestamp)
                VALUES({input_dict["id"]}, {timestamp});
                """
                self._execute_query(query)

            elif type == "user":
                query = f"""
                INSERT INTO users(user_id, name, surname)
                VALUES({input_dict["id"]}, {input_dict["info"]["name"]}, {input_dict["info"]["surname"]});
                """
                self._execute_query(query)

            elif type == "service":
                query = f"""
                INSERT INTO services(service_id, description, timestamp)
                VALUES({input_dict["id"]}, {input_dict["info"]["description"]}, {timestamp})
                """
                self._execute_query(query)

            else:
                cherrypy.HTTPError(400, f"Unknown item type: {type}")

        except KeyError as exc:
            cherrypy.HTTPError(400, f"Missing or wrong key in JSON file: {exc}")
        except Exception as exc:
            cherrypy.HTTPError(400, f"An exception occurred: {exc}")


    def PUT(self, *uri, **params):      # update
        pass


    def DELETE(self, *uri, **params):   # delete
        pass


    def _execute_query(self, query):
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
        except sqlite3.Error as err:
            print(err)
            cherrypy.HTTPError(500, f"Error in querying the database\nQuery:\n{query}")

        return cursor.fetchall()




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