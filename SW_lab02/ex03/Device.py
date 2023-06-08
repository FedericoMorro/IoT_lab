import requests
import json
import time
from threading import Thread

ip_addr = "127.0.0.1"
port = 8080

REFRESH_TIME = 60

class Device():
    def __init__(
        self,
        device_id: str,
        rest_endpoints: list,
        mqtt_endpoints: list,
        resource: list
    ):
        self.device_id = device_id
        self.rest_endpoints = rest_endpoints
        self.mqtt_endpoints = mqtt_endpoints
        self.resources = resource

        self.publish()

        self._thread = Thread(target= self.update)
        self._thread.start()

        return
    

    def _generate_payload(self) -> dict:
        pl = {
            "id": self.device_id,
            "ep": {
                "r": self.rest_endpoints,
                "m": self.mqtt_endpoints
            },
            "rs": self.resources
        }

        return pl
    
    
    def publish(self):
        payload = self._generate_payload()
        requests.post(f"http://{ip_addr}:{port}/devices/sub", data = json.dumps(payload))

        return


    def update(self):
        while True:
            time.sleep(REFRESH_TIME)
            
            payload = self._generate_payload()
            requests.put(f"http://{ip_addr}:{port}/devices/upd", data = json.dumps(payload))
