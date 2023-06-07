import time
from threading import Thread
import paho.mqtt.client as PahoMQTT
import requests
import json

refresh_time = 60

ip_addr = "127.0.0.1"
port = 8080

class Service():

    def __init__(self):
        self._service_id = "IoT_lab_group3_service_subscriber"

        self._catalog_uri = "http://192.0.0.1:8080"

        self._broker_hostname = ""
        self._broker_port = -1        

        self._payload = {
            "id": "service_temp_id",
            "ep": {
                "r": {
                    "r": [
                    ],
                    "u": [
                    ]
                },
                "m": {
                    "s": [
                    ],
                    "p": [
                    ]
                }
            },
            "in": {
                "d": "sub/temp"
            }
        }

        self._mqtt_client = PahoMQTT.Client(self._service_id, clean_session= False)
        self._mqtt_client.on_connect = self.callback_mqtt_on_connect
        self._mqtt_client.on_message = self.callback_mqtt_on_message

        self._thread = Thread(target = self.subscribe)
        self._thread.start()

        self.get_mqtt_broker()

        self._mqtt_client.connect(self._broker_hostname, self._broker_port)
        self._mqtt_client.loop_start()

        self.get_temperature_topics()

        self._subscribed_topics = []


    def __del__(self):
        self._mqtt_client.unsubscribe(self._subscribed_topics)
        self._mqtt_client.loop_stop()


    def subscribe(self):
        self._mqtt_client.subscribe(f"{self._mqtt_data['ep']['m']['bt'][0]['v']}/services/{self._service_id}", 2)

        self._mqtt_client.publish(
            topic = f"{self._mqtt_data['ep']['m']['bt'][0]['v']}/services/sub",
            payload = f"{json.dumps(self._payload)}",
            qos = 2
        )

        while True:
            time.sleep(refresh_time)

            self._mqtt_client.publish(
                topic = f"{self._mqtt_data['ep']['m']['bt'][0]['v']}/services/upd",
                payload = f"{json.dumps(self._payload)}",
                qos = 2
            )
        

    def callback_mqtt_on_connect(self, client, userdata, flags, rc):
        print("Connected to the mqtt broker")


    def callback_mqtt_on_message(self, paho_mqtt, userdata, msg):
        input_str = msg.payload.decode("utf-8")
        input_dict = json.loads(input_str)

        for data in input_dict["e"]:
            if data["n"] == "temperature":
                print(f'Timestamp: {data["t"]}: {data["v"]} {data["u"]}')



    def get_mqtt_broker(self):
        try:
            payload = requests.get(self._catalog_uri + "/MQTTbroker")

            input_dict = json.loads(payload)

            self._broker_hostname = input_dict["ep"]["r"]["hn"][0]["v"]
            self._broker_port = input_dict["ep"]["r"]["pt"][0]["v"]

        except KeyError as exc:
            print(f"Missing or wrong key in JSON file: {exc}")
        except ValueError as exc:
            print(f"Error in input JSON to dictionary conversion: {exc}")
        except Exception as exc:
            print(f"An exception occurred: {exc}")


    def get_temperature_topics(self):
        try:
            payload = requests.get(self._catalog_uri + "/devices")

            input_dict = json.loads(payload)

            for device in input_dict:

                has_temp = False
                for resource in device["in"]["r"]:
                    if resource["n"] == "pub/temp":
                        has_temp = True

                if has_temp:
                    for endpoint in device["ep"]["m"]["p"]:
                        if endpoint["v"].find("temp") != -1:
                            self._subscribed_topics.append(endpoint["v"])

        except KeyError as exc:
            print(f"Missing or wrong key in JSON file: {exc}")
        except ValueError as exc:
            print(f"Error in input JSON to dictionary conversion: {exc}")
        except Exception as exc:
            print(f"An exception occurred: {exc}")



    def json_dict_to_str(self, json_dict):
        try:
            json_str = json.dumps(json_dict)
        except ValueError as exc:
            print(f"Error in dictionary to output JSON conversion: {exc}")
        except Exception as exc:
            print(f"An exception occurred: {exc}")
        
        return json_str




def main():
    pass
    


if __name__ == '__main__':
    main()