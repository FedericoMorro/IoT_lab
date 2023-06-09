import requests as req
import json
import paho.mqtt.client as PahoMQTT

from threading import Thread
from time import time


# Arudino ID
ARDUINO_ID = "ard"


# Server (Catalog) IP and port
CATALOG_IP = "127.0.0.1"
CATALOG_PORT = 8080

CATALOG_URI = f"http://{CATALOG_IP}:{CATALOG_PORT}"

CATALOG_SUB_TIMEOUT = 60


class Controller():
    def __init__(self):
        """
        - Basic attributes creation
        - Connection to Catalog
        - Retreive Catalog data
        """

        # Basic service data
        self._service_id = "IoT_Lab_G3_Controller"
        self._mqtt_ep = {
            "s": [],
            "p": []
        }
        self._resources = [
            {"n": "set_min_ac_presence", "t": "mi_ap"},
            {"n": "set_max_ac_presence", "t": "ma_ap"},
            {"n": "set_min_ac_absence", "t": "mi_aa"},
            {"n": "set_max_ac_absence", "t": "ma_aa"},
            {"n": "set_min_ht_presence", "t": "mi_hp"},
            {"n": "set_max_ht_presence", "t": "ma_hp"},
            {"n": "set_min_ht_absence", "t": "mi_ha"},
            {"n": "set_max_ht_absence", "t": "ma_ha"},
            {"n": "set_pir_timeout", "t": "p_to"}
        ]
        self._info = {
            "d": "IoT Devices Controller"
        }

        self._cat_info = self._get_catalog()
        self._mqtt_broker = {
            "hn": self._cat_info["ep"]["m"]["hn"],
            "pt": self._cat_info["ep"]["m"]["pt"],
            "bt": self._cat_info["ep"]["m"]["bt"]
        }

        # MQTT init and Catalog subscription
        self._mqtt_client = PahoMQTT.Client(self._service_id, clean_session = False)
        self._mqtt_client.on_message = self._callback_mqtt_on_message

        self._sub_upd_thread = Thread(target = self._catalog_subscribe())
        self._sub_upd_thread.start()

        self._mqtt_client.connect(self._mqtt_broker["hn"], self._mqtt_broker["pt"])
        self._mqtt_client.loop_start()

        self._arduino_resources = {
            "pub": {
                "temperature": {}, "pir_presence": {}, "mic_presence": {}
            },
            "sub": {
                "air_cond": {}, "heating": {}, "lcd": {}
            }
        }
        # Get arduino resources
        self._get_arduino_resources()

        # Temperature
        self._temperature = 0

        # Fan information
        self._min_fan_speed = 124   # -> if lower the fan does not move
        self._max_fan_speed = 255

        # Air conditioning information
        self._ac_intensity = 0
        self._min_ac_absence = 20
        self._max_ac_absence = 25
        self._min_ac_presence = 25
        self._max_ac_presence = 30

        # LED information
        self._min_led_intensity = 0
        self._max_led_intensity = 255

        # Heating system information
        self._ht_intensity = 0
        self._min_ht_absence = 20
        self._max_ht_absence = 25
        self._min_ht_presence = 25
        self._max_ht_presence = 30

        # PIR
        self._pir_presence = 0
        self._PIR_TIMEOUT = 10  # seconds
        self._pir_time = time.time()
        self._pir_timeout_thread = Thread(target = self._check_pir_timeout)

        # Microphone
        self._mic_presence = 0

    @property
    def payload(self):
        pl = {
            "id": self._service_id,
            "ep": {
                "m": self._mqtt_ep
            },
            "rs": self._resources,
            "in": self._info
        }

        return pl
    

    def _get_catalog(self):
        reply = req.get(CATALOG_URI)
        try:
            get_output = json.loads(reply.text)
            return get_output
        
        except ValueError as exc:
            print(f"ERROR: Error in input JSON to dictionary conversion: {exc}")
            return
        
        except Exception as exc:
            print(f"ERROR: An exception occurred: {exc}")
            return


    def _catalog_subscribe(self):
        req.post(f"{CATALOG_URI}/services/sub", data = json.dumps(self.payload))

        while True:
            time.sleep(CATALOG_SUB_TIMEOUT)
            req.put(f"{CATALOG_URI}/services/upd", data = json.dumps(self.payload))
    

    def _get_arduino_resources(self):
        payload = req.get(f"{CATALOG_URI}/devices")

        devices_list = self._json_dict_to_str(payload.text)

        arduino = None
        for device in devices_list:
            if device["id"] == ARDUINO_ID:
                arduino = device

        if arduino == None:
            print(f"Arduino not found in the devices list")
            exit(1)
        
        # Given resources names, find associated types and mqtt end_point
        for resource in arduino["rs"]:
            res_name = resource["n"]

            if res_name in self._arduino_resources["pub"]:
                self._arduino_resources["pub"][res_name]["type"] = resource["t"]
                self._arduino_resources["pub"][res_name]["topics"] = []

            if res_name in self._arduino_resources["sub"]:
                self._arduino_resources["sub"][res_name]["type"] = resource["t"]
                self._arduino_resources["sub"][res_name]["topics"] = []


    def _callback_mqtt_on_message(self, paho_mqtt, userdata, msg):
        print(f"MQTT: message received on {msg.topic}: {msg.payload}")

        try:
            input_str = msg.payload.decode("utf-8")     # to convert from bytes to text, otherwise payload is like "b'text"
            input_dict = json.loads(input_str)

            # topic_elem = msg.topic.split("/")
            for data in input_dict["e"]:
                type = data["n"]        # check index

                if type == "temperature":
                    self._temperature_callback(data["v"])   # pass as argument the temperature
                elif type == "pir_presence":
                    self._pir_callback(data["v"])           # pass as argument the pir value
                elif type == "mic_presence":
                    self._mic_callback(data["v"])           # pass as argument the mic presence value
                elif type == "min_ac_absence_threshold":
                    self._min_ac_absence_threshold_callback(data["v"])
                elif type == "max_ac_absence_threshold":
                    self._max_ac_absence_threshold_callback(data["v"])
                elif type == "min_ac_presence_threshold":
                    self._min_ac_presence_threshold_callback(data["v"])
                elif type == "max_ac_presence_threshold":
                    self._max_ac_presence_threshold_callback(data["v"])
                elif type == "min_ht_absence_threshold":
                    self._min_ht_absence_threshold_callback(data["v"])
                elif type == "max_ht_absence_threshold":
                    self._max_ht_absence_threshold_callback(data["v"])
                elif type == "min_ht_presence_threshold":
                    self._min_ht_presence_threshold_callback(data["v"])
                elif type == "max_ht_presence_threshold":
                    self._max_ht_presence_threshold_callback(data["v"])

        except KeyError as exc:
            print(f"ERROR: Missing or wrong key in input JSON: {exc}")
            return
        except ValueError as exc:
            print(f"ERROR: Error in input JSON to dictionary conversion: {exc}")
            return
        except Exception as exc:
            print(f"ERROR: An exception occurred: {exc}")
            return


    def _temperature_callback(self, val):
        self._temperature = val

        if self._pir_presence or self._mic_presence:
            self._ac_pwm_value(self._min_ac_presence, self._max_ac_presence)
            self._ht_pwm_value(self._min_ht_presence, self._max_ht_presence)
        else:
            self._ac_pwm_value(self._min_ac_absence, self._max_ac_absence)
            self._ht_pwm_value(self._min_ht_absence, self._max_ht_absence)


    def _ac_pwm_value(self, min, max):
        if self._temperature < min:
            self._mqtt_ac_pwm(0)
            return
        
        if self._temperature >= max:
            self._mqtt_ac_pwm(1)
        else:
            ac_percentage = (self._temperature - min) / (max - min)

        self._ac_intensity = ac_percentage * (self._max_fan_speed - self._min_fan_speed) + self._min_fan_speed
        self._mqtt_ac_pwm()

    
    def _mqtt_ac_pwm(self):
        pass


    def _ht_pwm_value(self, min, max):
        if self._temperature < min:
            self._mqtt_ht_pwm(0)
            return
        
        if self._temperature >= max:
            self._mqtt_ht_pwm(1)
        else:
            ht_percentage = (max - self._temperature) / (max - min)

        self._ht_intensity = ht_percentage * (self._max_led_intensity - self._min_led_intensity) + self._min_led_intensity
        self._mqtt_ht_pwm()


    def _mqtt_ht_pwm(self):
        pass


    def _pir_callback(self, presence):
        self._pir_presence = presence
        self._pir_time = time.time()


    def _mic_callback(self, presence):
        self._mic_callback = presence


    def _check_timeout_presence(self):
        while True:
            if self._pir_presence and (time.time() - self._pir_time > self._PIR_TIMEOUT):
                self._pir_presence = 0

                self._ac_pwm_value()
                self._ht_pwm_value()

    
    def _min_ac_absence_threshold_callback(self, val):
        self._min_ac_absence = val


    def _max_ac_absence_threshold_callback(self, val):
        self._max_ac_absence = val
    
    
    def _min_ac_presence_threshold_callback(self, val):
        self._min_ac_presence = val


    def _max_ac_presence_threshold_callback(self, val):
        self._max_ac_presence = val


    def _min_ht_absence_threshold_callback(self, val):
        self._min_ht_absence = val


    def _max_ht_absence_threshold_callback(self, val):
        self._max_ht_absence = val


    def _min_ht_presence_threshold_callback(self, val):
        self._min_ht_presence = val


    def _max_ht_presence_threshold_callback(self, val):
        self._max_ht_presence = val



    def _json_dict_to_str(self, json_dict):
        try:
            json_str = json.dumps(json_dict)
            
            return json_str
        
        except ValueError as exc:
            print(f"Error in dictionary to output JSON conversion: {exc}")
        except Exception as exc:
            print(f"An exception occurred: {exc}")