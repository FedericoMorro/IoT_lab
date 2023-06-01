import requests

class Device():
    def __init__(
        self,
        device_id: str,
        rest_endpoints: list,
        mqtt_endpoints: list,
        resource: list
    ):
        self.device_id = device_id
        self.rest_endpoints.append(rest_endpoints)
        self.mqtt_endpoints.append(mqtt_endpoints)
        self.resources.append(resource)

        return
    
    
    def publish(self):
        pass


    def update(self):
        pass