import cherrypy
import json


class TemperatureLogger(object):
    exposed = True


    def POST(self, *uri, **params):
        output = ""

        # Check path correctness and (if so) save into the log
        if len(uri) == 1 and uri[0] == "log":
            # Read input json and convert it to dictionary
            try:
                input_str = cherrypy.request.body.read()
                if len(input_str) == 0:
                    raise cherrypy.HTTPError(400, "Empty POST")

                payload = json.loads(input_str)

            except ValueError as exc:
                raise cherrypy.HTTPError(400, f"Error in json file conversion: {exc}")
            
            except Exception as exc:
                raise cherrypy.HTTPError(400, f"Error in json file: {exc}")
            
            # Add the dictionary to the list
            if "log" not in cherrypy.session:
                cherrypy.session["log"] = list()
            
            try:
                cherrypy.session["log"].append(payload)
                output = "[DEBUG] New log element correctly stored"
            except Exception as exc:
                print("[DEBUG - ERROR] appending request in log")

            print(output)

            
        else:
            raise cherrypy.HTTPError(404, "Only \"/log\" is implemented yet")
        
        return output


    def GET(self, *uri, **params):
        # Home page
        if len(uri) == 0:
            return output

        # Check path correctness and (if so) perform conversion
        if len(uri) == 1 and uri[0] == "log":
            if cherrypy.session.get("log") is None:
                print("[DEBUG] Session 'log' is none")
                return ""
            
            # Convert log to json file
            try:
                output = json.dumps(cherrypy.session.get("log"))
            except ValueError as exc:
                raise cherrypy.HTTPError(400, f"Error in json file conversion: {exc}")
            except Exception as exc:
                raise cherrypy.HTTPError(500, f"Failed JSON output conversion: {exc}")
        
        else:
            raise cherrypy.HTTPError(404, "Only \"log\" is implemented yet")
        
        return output


if __name__=="__main__":
    conf={
        '/':{
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }
    
    cherrypy.tree.mount(TemperatureLogger(), '/', conf)

    cherrypy.config.update({'server.socket_host': '192.168.255.123'}) # to be modified
    cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.engine.start()
    cherrypy.engine.block()