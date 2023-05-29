import cherrypy
import paho.mqtt.client as PahoMQTT
import sqlite3
import json


class Catalog():
    exposed = True


    def __init__(self):
        pass


    def GET(self, *uri, **params):      # retrieve
        pass


    def POST(self, *uri, **params):     # create
        pass


    def PUT(self, *uri, **params):      # update
        pass


    def DELETE(self, *uti, **params):   # delete
        pass




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