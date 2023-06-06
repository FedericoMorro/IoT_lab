import paho.mqtt.client as PahoMQTT
import requests as req
import json

ip_addr = "127.0.0.1"
port = 8080

class Service():
    def __init__(
        self,
        service_id: str,
        rest_endpoints: list,
        mqtt_endpoints: list,
        resource: list
    ):
        self.service_id = service_id
        self.rest_endpoints = rest_endpoints
        self.mqtt_endpoints = mqtt_endpoints
        self.resources = resource

        self.publish()

        return
    

    def _mqtt_init():
        r = req.get(f"{ip_addr}:{port}/MQTTbroker")
        return json.loads(r.text)
    

    def _generate_payload(self) -> dict:
        pl = {
            "id": self.service_id,
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
        req.post(f"http://{ip_addr}:{port}/services/subscription", data = json.dumps(payload))

        return


    def update(self):
        payload = self._generate_payload()
        req.put(f"http://{ip_addr}:{port}/services/refresh", data = json.dumps(payload))

        return