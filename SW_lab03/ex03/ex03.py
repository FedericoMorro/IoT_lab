import time
from threading import Thread
import paho.mqtt.client as PahoMQTT
import requests
import json


CATALOG_URI = "http://192.168.151.123:8080"


class PublisherService():

    def __init__(self):
        self._service_id = "IoT_lab_group3_service_publisher"

        self._catalog_uri = CATALOG_URI

        self._broker_hostname = ""
        self._broker_port = -1
        self._catalog_base_topic = ""

        self._mqtt_client = PahoMQTT.Client(self._service_id, clean_session= False)
        self._mqtt_client.on_connect = self.callback_mqtt_on_connect
        self._mqtt_client.on_message = self.callback_mqtt_on_message

        self.get_mqtt_broker()

        print(f"Try to connect to MQTT broker {self._broker_hostname}:{self._broker_port}")
        self._mqtt_client.connect(self._broker_hostname, self._broker_port)
        self._mqtt_client.loop_start()

        self._REFRESH_DELAY = 60
        self._thread_sub = Thread(target = self.thread_refresh_catalog_subscription)
        self._thread_sub.start()

        self._publisher_topics_type_device = []
        self.get_led_topics()

        self._CHANGE_LED_STATUS_DELAY = 15
        self._led_status = 0
        self._thread_led = Thread(target= self.publish_led_status)
        self._thread_led.start()


    def __del__(self):
        self._mqtt_client.loop_stop()



    def callback_mqtt_on_connect(self, client, userdata, flags, rc):
        print("Connected to the mqtt broker")


    def callback_mqtt_on_message(self, paho_mqtt, userdata, msg):
        print(f"MQTT message received on topic: {msg.topic}")



    def publish_led_status(self):
        
        while True:
            self._led_status = 1 - self._led_status

            for topic_type_device in self._publisher_topics_type_device:
                topic = topic_type_device[0]
                res_type = topic_type_device[1]
                device_id = topic_type_device[2]
                payload = self.payload_led_sen_ml(self._led_status, res_type, device_id)

                self._mqtt_client.publish(topic, payload, qos= 2)

                print(f"Published MQTT message on: {topic} : {payload}")

            time.sleep(self._CHANGE_LED_STATUS_DELAY)

    
    def payload_led_sen_ml(self, led_status, res_type, device_id):
        payload_dict = {}
        payload_dict["bn"] = device_id
        payload_dict["e"] = []
        payload_dict["e"].append({
            "n": res_type,
            "t": int(time.time()),
            "v": led_status,
            "u": ""
        })

        return self.json_dict_to_str(payload_dict)


    
    def thread_refresh_catalog_subscription(self):
        # Subscribe
        requests.post(f"{self._catalog_uri}/services/sub", data= self.payload_catalog_subscription())

        while True:
            time.sleep(self._REFRESH_DELAY)

            # Refresh subscription
            requests.put(f"{self._catalog_uri}/services/upd", data= self.payload_catalog_subscription())
            


    def payload_catalog_subscription(self):
        payload_dict = {}
        payload_dict["id"] = self._service_id
        payload_dict["ep"] = {}
        payload_dict["rs"] = []
        payload_dict["in"] = {"d": "Set led status"}

        return self.json_dict_to_str(payload_dict)            



    def get_mqtt_broker(self):
        try:
            payload = requests.get(self._catalog_uri)

            input_dict = json.loads(payload.text)

            self._broker_hostname = input_dict["ep"]["m"]["hn"][0]["v"]
            self._broker_port = input_dict["ep"]["m"]["pt"][0]["v"]
            self._catalog_base_topic = input_dict["ep"]["m"]["bt"][0]["v"]

        except KeyError as exc:
            print(f"Missing or wrong key in JSON file: {exc}")
        except ValueError as exc:
            print(f"Error in input JSON to dictionary conversion: {exc}")
        except Exception as exc:
            print(f"An exception occurred: {exc}")


    def get_led_topics(self):
        try:
            # Get all devices subscripted to the Catalog
            payload = requests.get(self._catalog_uri + "/devices")

            input_dict = json.loads(payload.text)

            # Loop over devices
            for device in input_dict:
                
                # Search if the device has the temperature resource and get the type
                ep_type = ""
                has_temp = False
                for resource in device["rs"]:
                    if resource["n"] == "led":
                        ep_type = resource["t"]
                        has_temp = True

                # If so, find the end_point which corresponds to the type found in the resources
                if has_temp:
                    for mqtt_endpoint in device["ep"]["m"]["s"]:
                        if mqtt_endpoint["t"] == ep_type:
                            self._publisher_topics_type_device.append((mqtt_endpoint["v"], mqtt_endpoint["t"], device["id"]))

        except KeyError as exc:
            print(f"Missing or wrong key in JSON file: {exc}")
        except ValueError as exc:
            print(f"Error in input JSON to dictionary conversion: {exc}")
        except Exception as exc:
            print(f"An exception occurred: {exc}")



    def json_dict_to_str(self, json_dict):
        try:
            json_str = json.dumps(json_dict)
            
            return json_str
        
        except ValueError as exc:
            print(f"Error in dictionary to output JSON conversion: {exc}")
        except Exception as exc:
            print(f"An exception occurred: {exc}")




def main():
    s = PublisherService()
    


if __name__ == '__main__':
    main()