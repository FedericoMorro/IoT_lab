import requests as req
import json
import paho.mqtt.client as PahoMQTT

from threading import Thread
from time import time


# Server (Catalog) IP and port
CATALOG_IP = "127.0.0.1"
CATALOG_PORT = 8080

catalog_uri = f"http://{CATALOG_IP}:{CATALOG_PORT}"


class Controller():
    def __init__(self):
        """
        - Basic attributes creation
        - Connection to Catalog
        - Retreive Catalog data
        """

        self._service_id = "IoT_Lab_G3_Controller"
        self._rest_ep = {
            "r": [],
            "c": [],
            "u": [],
            "d": []
        }
        self._mqtt_ep = {
            "s": [],
            "p": []
        }
        self._info = {
            "d": "IoT Devices Controller"
        }

        self._cat_info = self._get_catalog()
        self._mqtt_broker = {
            "hn": self._cat_info["ep"]["m"]["hn"],
            "pt": self._cat_info["ep"]["m"]["pt"],
            "bt": self._cat_info["ep"]["m"]["bt"]
        }

        self._mqtt_client = PahoMQTT.Client(self._service_id, clean_session = False)
        self._mqtt_client.on_message = self._callback_mqtt_on_message

        self._sub_upd_thread = Thread(target = self._subscribe())
        self._sub_upd_thread.start()

        self._mqtt_client.connect(self._mqtt_broker["hn"], self._mqtt_broker["pt"])
        self._mqtt_client.loop_start()


    @property
    def payload(self):
        pl = {
            "id": self._service_id,
            "ep": {
                "r": self._rest_ep,
                "m": self._mqtt_ep
            },
            "in": self._info
        }

        return pl
    

    def _get_catalog(self):
        reply = req.get(catalog_uri)
        try:
            get_output = json.loads(reply.text)
            return get_output
        
        except ValueError as exc:
            print(f"ERROR: Error in input JSON to dictionary conversion: {exc}")
            return
        
        except Exception as exc:
            print(f"ERROR: An exception occurred: {exc}")
            return
    

    def _callback_mqtt_on_message(self, paho_mqtt, userdata, msg):
        print(f"MQTT: message received on {msg.topic}: {msg.payload}")

        try:
            input_str = msg.payload.decode("utf-8")     # to convert from bytes to text, otherwise payload is like "b'text"
            input_dict = json.loads(input_str)

            topic_elem = msg.topic.split("/")
            type = topic_elem[4] # check index

            if type == "temp":
                self._compute_hs_ac()
            elif type == "pir":
                self._update_presence()

        except KeyError as exc:
            print(f"ERROR: Missing or wrong key in input JSON: {exc}")
            return
        except ValueError as exc:
            print(f"ERROR: Error in input JSON to dictionary conversion: {exc}")
            return
        except Exception as exc:
            print(f"ERROR: An exception occurred: {exc}")
            return


    # TODO: check and finish this function -> better integration with Catalog?
    def _subscribe(self):
        req.post(catalog_uri, data = json.dumps(self.payload))

        while True:
            time.sleep(60)
            req.put(catalog_uri, data = json.dumps(self.payload))


    def _compute_hs_ac(self):
        pass

    def _update_presence(self):
        pass