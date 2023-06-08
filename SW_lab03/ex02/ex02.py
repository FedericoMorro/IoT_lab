import time
from threading import Thread
import paho.mqtt.client as PahoMQTT
import requests
import json

refresh_time = 60

CATALOG_URI = "http://192.0.0.1:8080"

class Service():

    def __init__(self):
        self._service_id = "IoT_lab_group3_service_subscriber"

        self._catalog_uri = CATALOG_URI

        self._broker_hostname = ""
        self._broker_port = -1
        self._catalog_base_topic = ""

        self._mqtt_client = PahoMQTT.Client(self._service_id, clean_session= False)
        self._mqtt_client.on_connect = self.callback_mqtt_on_connect
        self._mqtt_client.on_message = self.callback_mqtt_on_message

        self.get_mqtt_broker()

        self._mqtt_client.connect(self._broker_hostname, self._broker_port)
        self._mqtt_client.loop_start()

        self._subscribed_topics_type = []
        self.get_temperature_topics()

        for topic_type in self._subscribed_topics_type:
            self._mqtt_client.subscribe(topic_type[0], qos= 2)

        self._REFRESH_DELAY = 60
        self._thread = Thread(target = self.thread_refresh_catalog_subscription)
        self._thread.start()



    def __del__(self):
        for topic_type in self._subscribed_topics_type:
            self._mqtt_client.unsubscribe(topic_type[0])
        self._mqtt_client.loop_stop()



    def callback_mqtt_on_connect(self, client, userdata, flags, rc):
        print("Connected to the mqtt broker")


    def callback_mqtt_on_message(self, paho_mqtt, userdata, msg):
        input_str = msg.payload.decode("utf-8")
        input_dict = json.loads(input_str)

        print(f"MQTT message received on topic: {msg.topic}")

        for data in input_dict["e"]:
            if data["n"] == "temperature":
                print(f'Timestamp: {data["t"]}: {data["v"]} {data["u"]}')


    
    def thread_refresh_catalog_subscription(self):
        is_first = True

        while True:

            if is_first:
                self.refresh_catalog_subscription(is_first= True)
                is_first = False

            self.refresh_catalog_subscription()

            time.sleep(self._REFRESH_DELAY)


    def refresh_catalog_subscription(self, is_first=False):
        payload_dict = {}
        payload_dict["id"] = self._service_id
        payload_dict["ep"]["m"]["s"] = []
        payload_dict["rs"] = []
        payload_dict["in"]["d"] = "Read temperature from sensors"

        for topic_type in self._subscribed_topics_type:
            payload_dict["ep"]["m"]["s"].append({"v": topic_type[0], "t": topic_type[1]})

        payload_str = self.json_dict_to_str(payload_dict)

        if is_first:
            requests.post(f"{self._catalog_uri}/services/sub", data= payload_str)
        else:
            requests.put(f"{self._catalog_uri}/services/upd", data= payload_str)



    def get_mqtt_broker(self):
        try:
            payload = requests.get(self._catalog_uri)

            input_dict = json.loads(payload)

            self._broker_hostname = input_dict["ep"]["m"]["hn"][0]["v"]
            self._broker_port = input_dict["ep"]["m"]["pt"][0]["v"]
            self._catalog_base_topic = input_dict["ep"]["m"]["bt"][0]["v"]

        except KeyError as exc:
            print(f"Missing or wrong key in JSON file: {exc}")
        except ValueError as exc:
            print(f"Error in input JSON to dictionary conversion: {exc}")
        except Exception as exc:
            print(f"An exception occurred: {exc}")


    def get_temperature_topics(self):
        try:
            # Get all devices subscripted to the Catalog
            payload = requests.get(self._catalog_uri + "/devices")

            input_dict = json.loads(payload)

            # Loop over devices
            for device in input_dict:
                
                # Search if the device has the temperature resource and get the type
                ep_type = ""
                has_temp = False
                for resource in device["rs"]:
                    if resource["n"] == "temperature":
                        ep_type = resource["v"]
                        has_temp = True

                # If so, find the end_point which corresponds to the type found in the resources
                if has_temp:
                    for mqtt_endpoint in device["ep"]["m"]["p"]:
                        if mqtt_endpoint["t"] == ep_type:
                            self._subscribed_topics_type.append((mqtt_endpoint["v"], mqtt_endpoint["t"]))

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
    s = Service()
    


if __name__ == '__main__':
    main()