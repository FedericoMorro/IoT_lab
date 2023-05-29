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
        self._db_name = DB_NAME
        self._max_timestamp = 120

        self._loop()


    def _loop(self):
        while True:
            
            # TODO: check if timestamps are too old and delete them
            
            time.sleep(60)


    def GET(self, *uri, **params):      # retrieve
        pass


    def POST(self, *uri, **params):     # create
        pass


    def PUT(self, *uri, **params):      # update
        pass


    def DELETE(self, *uti, **params):   # delete
        pass


    def _execute_query(self, query):
        connection = None
        cursor = None

        try:
            connection = sqlite3.connect(self._db_name)
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