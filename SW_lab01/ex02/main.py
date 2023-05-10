import cherrypy
import json


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


    def GET(self, *uri, **params):
        output = "Exercise 01, SW lab 01"
        converted_value = 0.0

        # Home page
        if len(uri) == 0:
            return output

        # Check path correctness and (if so) perform conversion
        if len(uri) > 0 and uri[0] == "converter":
            # Check parameters correctness
            if len(uri) != 4:
                raise cherrypy.HTTPError(400, "Insufficient number of parameters, expected: 3")

            converted_value = self.convert(uri[1], uri[2], uri[3])
        else:
            raise cherrypy.HTTPError(404, "Only \"/converter\" is implemented yet")

        # Create json
        output = f"""
        {{
	        "original": {{
		        "value": {float(uri[1])},
		        "unit": \"{uri[2]}\"
	        }},
	        "converted": {{
		        "value": {converted_value},
		        "unit": \"{uri[3]}\"
	        }}
        }}
        """

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