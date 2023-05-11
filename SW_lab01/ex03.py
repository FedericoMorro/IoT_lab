import cherrypy
import json
import time


class TemperatureConverter(object):
    exposed = True

    def convert(self, val, original_unit, target_unit) -> float:
        zero_C_in_K = 273.15
        multiply_const_C_to_F = 9/5
        offset_C_to_F = 32

        original_unit = original_unit.upper()
        target_unit = target_unit.upper()

        # Check input units
        if original_unit not in ['C', 'K', 'F']:
            raise cherrypy.HTTPError(400, f"Original unit not recognized ({original_unit}), expected: \"C\", \"K\" or \"F\"")
        if target_unit not in ['C', 'K', 'F']:
            raise cherrypy.HTTPError(400, f"Target unit not recognized ({target_unit}), expected: \"C\", \"K\" or \"F\"")
        
        if original_unit == target_unit:
            raise cherrypy.HTTPError(400, "The original unit and the target unit are the same")     # explain why bad request
        
        # Check input value
        try:
            val = float(val)
        except ValueError:
            raise cherrypy.HTTPError(400, f"Error in value type ({val}), expected: int or float")
        except Exception as exc:
            raise cherrypy.HTTPError(400, f"An exception occured: {exc}")
        
        # Convert all in Celsius
        if original_unit == 'K':
            val = val - zero_C_in_K
        elif original_unit == 'F':
            val = (val - offset_C_to_F) / multiply_const_C_to_F

        # Convert to target unit (if different from Celsius)
        if target_unit == 'K':
            val = val + zero_C_in_K
        elif target_unit == 'F':
            val = (val * multiply_const_C_to_F) + offset_C_to_F

        return val


    def POST(self, *uri, **params):
        output = "Exercise 03, SW lab 01"

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

        # Check input keys correctness
        if ("values" not in payload or "originalUnit" not in payload or "targetUnit" not in payload):
            raise cherrypy.HTTPError(400, "Requested keys not found, expected: \"value\", \"originalUnit\" and \"targetUnit\"")
        
        # Convert list of values
        result_vals = []
        for value in payload["values"]:
            result_vals.append(self.convert(value, payload["originalUnit"], payload["targetUnit"]))

        # Add fields to dict
        payload["targetValues"] = result_vals
        payload["timestamp"] = int(time.time())

        # Convert to json file
        try:
            output = json.dumps(payload)
        except ValueError as exc:
            raise cherrypy.HTTPError(400, f"Error in json file conversion: {exc}")
        except Exception as exc:
            raise cherrypy.HTTPError(500, f"Failed JSON output conversion: {exc}")
    
        return output


if __name__=="__main__":
    conf={
        '/':{
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }
    
    cherrypy.tree.mount(TemperatureConverter(), '/', conf)

    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.engine.start()
    cherrypy.engine.block()