import requests as req
import json
import paho.mqtt.client as PahoMQTT

from threading import Thread
from time import time


# Base Topic
BASE_TOPIC = "/tiot/g03/ctrl"

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

        # Temperature
        self._temperature = 0

        # Fan information
        self._min_fan_speed = 124   # -> if lower the fan does not move
        self._max_fan_speed = 255

        # Air conditioning and heating system information
        self._ac_intensity = 0
        self._ht_intensity = 0

        # LED information
        self._min_led_intensity = 0
        self._max_led_intensity = 255

        # topic for update thresholds: /tiot/g03/ctrl/t/<ac|ht>/<a|p>/<min|max>
        self._thresholds = {
            "name": "thresholds",
            "ep": f"{BASE_TOPIC}/t/+/+/+",
            "ac": {
                "a": {
                    "min": {
                        "ep": f"{BASE_TOPIC}/t/ac/a/min",
                        "t": "mi_aa",
                        "v": 20
                    },
                    "max": {
                        "ep": f"{BASE_TOPIC}/t/ac/a/max",
                        "t": "ma_aa",
                        "v": 25
                    }
                },
                "p": {
                    "min": {
                        "ep": f"{BASE_TOPIC}/t/ac/p/min",
                        "t": "mi_ap",
                        "v": 25
                    },
                    "max": {
                        "ep": f"{BASE_TOPIC}/t/ac/p/max",
                        "t": "ma_ap",
                        "v": 30
                    }
                }
            },
            "ht": {
                "a": {
                    "min": {
                        "ep": f"{BASE_TOPIC}/t/ht/a/min",
                        "t": "mi_ha",
                        "v": 20
                    },
                    "max": {
                        "ep": f"{BASE_TOPIC}/t/ht/a/max",
                        "t": "ma_ha",
                        "v": 25
                    }
                },
                "p": {
                    "min": {
                        "ep": f"{BASE_TOPIC}/t/ht/p/min",
                        "t": "mi_hp",
                        "v": 25
                    },
                    "max": {
                        "ep": f"{BASE_TOPIC}/t/ht/p/max",
                        "t": "ma_hp",
                        "v": 30
                    }
                }
            }
        }

        # PIR
        self._pir_presence = 0
        self._pir_timeout_info = {
            "ep": f"{BASE_TOPIC}/p",
            "t": "p",
            "v": 10
        }
        self._pir_time = time.time()
        self._pir_timeout_thread = Thread(target = self._check_pir_timeout)

        # Microphone
        self._mic_presence = 0

        self._service_id = "IoT_Lab_G3_Controller"
        self._mqtt_ep = {
            "s": [],
            "p": []
        }
        self._resources = [
            {"n": "set_min_ac_absence", "t": "mi_aa"},
            {"n": "set_max_ac_absence", "t": "ma_aa"},
            {"n": "set_min_ac_presence", "t": "mi_ap"},
            {"n": "set_max_ac_presence", "t": "ma_ap"},
            {"n": "set_min_ht_absence", "t": "mi_ha"},
            {"n": "set_max_ht_absence", "t": "ma_ha"},
            {"n": "set_min_ht_presence", "t": "mi_hp"},
            {"n": "set_max_ht_presence", "t": "ma_hp"},
            {"n": "set_pir_timeout", "t": "p_to"}
        ]
        self._info = {
            "d": "Arduino Controller"
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

        # Get arduino resources
        self._arduino_data = {
            "pub": {
                "temperature": {
                    "type": "",
                    "topics": [],
                    "func": self._temperature_callback
                },
                "pir_presence": {
                    "type": "",
                    "topics": [],
                    "func": self._pir_callback
                },
                "mic_presence": {
                    "type": "",
                    "topics": [],
                    "func": self._mic_callback
                }
            },
            "sub": {
                "air_cond": {
                    "type": "",
                    "topics": []
                },
                "heating": {
                    "type": "",
                    "topics": []
                },
                "lcd": {
                    "type": "",
                    "topics": []
                }
            }
        }
        self._get_arduino_data()

        self._subscribed_topics = []
        self._topic_subscribe()


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
    

    def _get_arduino_data(self):
        payload = req.get(f"{CATALOG_URI}/devices")

        devices_list = self._json_dict_to_str(payload.text)

        arduino = None
        for device in devices_list:
            if device["id"] == ARDUINO_ID:
                arduino = device
                break                       # supposing just one arduino

        tries = 10
        while arduino == None and tries:
            print("Arduino not found in the devices list, waiting 5s and retry")
            print(f"{tries} tries remaining")

            time.sleep(5)

            payload = req.get(f"{CATALOG_URI}/devices")

            devices_list = self._json_dict_to_str(payload.text)

            arduino = None
            for device in devices_list:
                if device["id"] == ARDUINO_ID:
                    arduino = device
                    break                   # supposing just one arduino

            tries -= 1

        if arduino == None:
            print("Exiting...")
            exit(1)

        # Given resources names, find associated types and mqtt end_point
        for resource in arduino["rs"]:
            name = resource["n"]

            # Add mqtt end_point on which arduino publishes
            if name in self._arduino_data["pub"]:
                type = resource["t"]
                self._arduino_data["pub"][name]["type"] = type

                self._arduino_data["pub"][name]["topics"] = []
                for topic in arduino["ep"]["m"]["p"]:
                    if topic["t"] == type:
                        self._arduino_data["pub"][name]["topics"].append(topic["v"])

            # Add mqtt end_point on which arduino is subscribed
            if name in self._arduino_data["sub"]:
                type = resource["t"]
                self._arduino_data["sub"][name]["type"] = type

                self._arduino_data["sub"][name]["topics"] = []
                for topic in arduino["ep"]["m"]["s"]:
                    if topic["t"] == type:
                        self._arduino_data["sub"][name]["topics"].append(topic["v"])


    def _topic_subscribe(self):
        self._subscribed_topics.append(self._thresholds["ep"])

        for name in self._arduino_data["pub"]:
            for topic in self._arduino_data["pub"][name]["topics"]:
                self._subscribed_topics.append(topic)
                
        self._mqtt_client.subscribe(self._subscribed_topics)
        

    def _callback_mqtt_on_message(self, paho_mqtt, userdata, msg):
        print(f"MQTT: message received on {msg.topic}: {msg.payload}")

        try:
            input_str = msg.payload.decode("utf-8")     # to convert from bytes to text, otherwise payload is like "b'text"
            input_dict = json.loads(input_str)

            topic_elem = msg.topic.split("/")
            if topic_elem[3] == "ctrl":
                if topic_elem[4] == "t":
                    self._update_thresholds(topic_elem, input_dict)
                elif topic_elem[4] == "p":
                    self._update_pir_timeout(input_dict)
                
            if topic_elem[3] == ARDUINO_ID:
                for pl in input_dict["e"]:
                    for name in self._arduino_data["pub"]:
                        if name == pl["n"]:
                            self._arduino_data["pub"][name]["func"]()

        except KeyError as exc:
            print(f"ERROR: Missing or wrong key in input JSON: {exc}")
            return
        
        except ValueError as exc:
            print(f"ERROR: Error in input JSON to dictionary conversion: {exc}")
            return
        
        except Exception as exc:
            print(f"ERROR: An exception occurred: {exc}")
            return


    def _update_thresholds(self, topic, pl):
        for i in pl["e"]:
            try:
                temp = i["v"]
                unit = i["u"]

                if temp != "C":
                    temp = self._convert_temp_to_celsius(temp, unit)

                self._thresholds[topic[5]][topic[6]][topic[7]]["v"] = temp
                self._temperature_callback()

            except KeyError as exc:
                print(f"ERROR: Missing or wrong key in input JSON: {exc}")
                return
            
            except ValueError as exc:
                print(f"ERROR: Error in input JSON to dictionary conversion: {exc}")
                return
            
            except Exception as exc:
                print(f"ERROR: An exception occurred: {exc}")
                return


    def _convert_temp_to_celsius(self, val, original_unit) -> float:
        zero_C_in_K = 273.15
        multiply_const_C_to_F = 9/5
        offset_C_to_F = 32

        original_unit = original_unit.upper()
        target_unit = target_unit.upper()
        
        val = float(val)
        
        # Convert all in Celsius
        if original_unit == 'K':
            val = val - zero_C_in_K
        elif original_unit == 'F':
            val = (val - offset_C_to_F) / multiply_const_C_to_F

        return val


    def _update_pir_timeout(self, pl):
        try:
            for i in pl["e"]:
                time = i["v"]
                unit = i["u"]

                if unit != "s":
                    time = self._convert_time_to_s(time, unit, "s")
                    
                    if time == None:
                        return
                
                self._pir_timeout_info["v"] = time

        except KeyError as exc:
            print(f"ERROR: Missing or wrong key in input JSON: {exc}")
            return
            
        except ValueError as exc:
            print(f"ERROR: Error in input JSON to dictionary conversion: {exc}")
            return
        
        except Exception as exc:
            print(f"ERROR: An exception occurred: {exc}")
            return
        
    
    def _convert_time_to_s(self, time, starting_unit):
        if starting_unit == "ms":
            return (time / 1000)
        elif starting_unit == "min":
            return (time * 60)
        else:
            return None
            

    def _temperature_callback(self, val):
        self._temperature = val

        if self._pir_presence or self._mic_presence:
            self._ac_pwm_value(self._thresholds["ac"]["p"]["min"], self._thresholds["ac"]["p"]["max"])
            self._ht_pwm_value(self._thresholds["ht"]["p"]["min"], self._thresholds["ht"]["p"]["max"])
        else:
            self._ac_pwm_value(self._thresholds["ac"]["a"]["min"], self._thresholds["ac"]["a"]["max"])
            self._ht_pwm_value(self._thresholds["ht"]["a"]["min"], self._thresholds["ht"]["a"]["max"])


    def _ac_pwm_value(self, min, max):
        if self._temperature < min:
            self._mqtt_pub(0)
            return
        
        if self._temperature >= max:
            self._mqtt_pub(1)
        else:
            ac_percentage = (self._temperature - min) / (max - min)

        self._ac_intensity = ac_percentage * (self._max_fan_speed - self._min_fan_speed) + self._min_fan_speed
        self._mqtt_pub("air_cond", self._ac_intensity)


    def _ht_pwm_value(self, min, max):
        if self._temperature < min:
            self._mqtt_pub(0)
            return
        
        if self._temperature >= max:
            self._mqtt_pub(1)
        else:
            ht_percentage = (max - self._temperature) / (max - min)

        self._ht_intensity = ht_percentage * (self._max_led_intensity - self._min_led_intensity) + self._min_led_intensity
        self._mqtt_pub()

    
    def _mqtt_pub(self, n, val):
        pl = self._senml_encode(n, val)
        
        for name in self._arduino_data["sub"]:
            if name == n:
                for topic in self._arduino_data["sub"][name]["topics"]:
                    self._mqtt_client.publish(topic, pl, qos = 2)


    def _pir_callback(self, presence):
        self._pir_presence = presence
        self._pir_time = time.time()

        self._temperature_callback()


    def _mic_callback(self, presence):
        self._mic_presence = presence

        self._temperature_callback()


    def _check_timeout_presence(self):
        while True:
            if self._pir_presence and (time.time() - self._pir_time > self._PIR_TIMEOUT):
                self._pir_presence = 0

                self._ac_pwm_value()
                self._ht_pwm_value()


    def _json_dict_to_str(self, json_dict):
        try:
            json_str = json.dumps(json_dict)
            
            return json_str
        
        except ValueError as exc:
            print(f"Error in dictionary to output JSON conversion: {exc}")
        except Exception as exc:
            print(f"An exception occurred: {exc}")

    
    def _senml_encode(self, res_type, val):
        payload_dict = {}
        payload_dict["bn"] = "controller"
        payload_dict["e"] = []
        payload_dict["e"].append({
            "n": res_type,
            "t": int(time.time()),
            "v": val,
            "u": ""
        })

        return self.json_dict_to_str(payload_dict)