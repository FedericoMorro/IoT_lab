import cherrypy
import json


class Converter(object):
    exposed = True


    def convert(self, val, original_unit, target_unit) -> str:
        if original_unit == target_unit:
            raise cherrypy.HTTPError(400, "Bad request") # explain why bad request


    def GET(self, *uri, **params):
        output = "Exercise 01, SW lab 01"

        if (len(uri) == 0):
            return "Software Laboratory #1"

        if (len(params) != 3):
            raise cherrypy.HTTPError(400, "Bad request")
        elif (not("value" in params and "originalUnit" in params and "targetUnit" in params)):
            raise cherrypy.HTTPError(400, "Bad request")

        if (len(uri) == 1 and uri[0] == "converter"):
            output = self.convert(self, params["value"], params["originalUnit"], params["targetUnit"])
        else:
            raise cherrypy.HTTPError(400, "Bad request")

        return output


if __name__=="__main__":
    conf={
        '/':{
            'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
            'tool.session.on':True
        }
    }
    
    cherrypy.quickstart(Converter(),'/',conf)