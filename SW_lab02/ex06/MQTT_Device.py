import paho.mqtt.client as PahoMQTT
import requests as req
import json

import time
from threading import Thread

refresh_time = 60

ip_addr = "127.0.0.1"
port = 8080

class MQTT_Device():
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

        self._client_id = "Python_MQTT_Device"

        self._mqtt_data = self._mqtt_init()     # {"hostname": ..., "port": ...}

        self._mqtt_client = PahoMQTT.Client(self._client_id, clean_session=False)
        self._mqtt_client.on_message = self._callback_on_MQTT_message

        self._mqtt_client.connect(self._mqtt_data["hostname"], self._mqtt_data["port"])
        self._mqtt_client.loop_start()

        self._thread = Thread(target = self.subscribe)
        self._thread.start()

        return
    

    def __del__(self):
        self._mqtt_client.unsubscribe(self._subscribed_topics)
        self._mqtt_client.loop_stop()
        self._mqtt_client.disconnect()

        self._thread.join()


    def _callback_on_MQTT_message(self):
        pass
    

    def _mqtt_init(self):
        r = req.get(f"http://{ip_addr}:{port}/MQTTbroker")
        return json.loads(r.text)
    

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


    def subscribe(self):
        self._mqtt_client.subscribe(f"{self._mqtt_data['base_topic']}/devices/{self.device_id}", 2)

        self._mqtt_client.publish(
            topic = f"{self._mqtt_data['base_topic']}/devices/subscription",
            payload = f"{self._generate_payload()}",
            qos = 2
        )

        while True:
            time.sleep(refresh_time)

            self._mqtt_client.publish(
                topic = f"{self._mqtt_data['base_topic']}/devices/refresh",
                payload = f"{self._generate_payload()}",
                qos = 2
            )
