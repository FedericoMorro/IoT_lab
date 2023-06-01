import requests
import json

ip_addr = "127.0.0.1"
port = 8080

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

        return
    

    def _generate_payload(self) -> dict:
        pl = {
            "id": self.device_id,
            "end_points": {
                "REST": self.rest_endpoints,
                "MQTT": self.mqtt_endpoints
            },
            "info": {
                "resources": self.resources
            }
        }

        return pl
    
    
    def publish(self):
        payload = self._generate_payload()
        requests.post(f"http://{ip_addr}:{port}/devices/subscription", data = json.dumps(payload))

        return


    def update(self):
        payload = self._generate_payload()
        requests.put(f"http://{ip_addr}:{port}/devices/refresh", data = json.dumps(payload))

        return