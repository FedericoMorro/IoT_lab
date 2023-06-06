import MQTT_Device

def _rest_endpoints_gathering(type: str) -> list:
    tmp_rest_ep_n = int(input(f"How many REST {type} endpoints does the device have? "))
    tmp_rest_ep_list = list()

    for i in range(0, tmp_rest_ep_n, 1):
        tmp_device_rest_ep = input(f"Insert the REST {type} device endpoint: ")
        tmp_rest_ep_list.append({"value": tmp_device_rest_ep})

    return tmp_rest_ep_list


def _mqtt_endpoints_gathering(type: str) -> list:
    tmp_mqtt_ep_n = int(input(f"How many MQTT {type} endpoints does the device have? "))
    tmp_mqtt_ep_list = list()

    for i in range(0, tmp_mqtt_ep_n, 1):
        tmp_device_mqtt_ep = input(f"Insert the MQTT {type} device endpoint: ")
        tmp_mqtt_ep_list.append({"value": tmp_device_mqtt_ep})

    return tmp_mqtt_ep_list


def _values_gathering(id) -> MQTT_Device:
    rest_eps = {
        "GET": _rest_endpoints_gathering("GET"),
        "POST": _rest_endpoints_gathering("POST"),
        "PUT": _rest_endpoints_gathering("PUT"),
        "DELETE": _rest_endpoints_gathering("DELETE")
    }

    mqtt_eps = {
        "subscriber": _mqtt_endpoints_gathering("subscriber"),
        "publisher": _mqtt_endpoints_gathering("publisher")
    }

    resrc_list = list()
    resrc_n = int(input("How many types of resources type does the device have? "))
    for i in range(0, resrc_n, 1):
        tmp_device_resource = input("Insert the device resource type: ")
        resrc_list.append({"name": tmp_device_resource})

    tmp_device = MQTT_Device(
        id,
        rest_eps,
        mqtt_eps,
        resrc_list
    )

    return tmp_device

def insert_dev() -> MQTT_Device:
    print("Insert a new device")
    
    tmp_device_id = input("Insert the device id: ")

    return _values_gathering(tmp_device_id)


def update_dev(id) -> MQTT_Device:
    return _values_gathering(id)


def main():
    device: MQTT_Device

    while True:
        sel = input("Would you like to creating a new device? (y / n): ")
        if sel == 'y':
            device = insert_dev()
        elif sel == 'n':
            sel = input("Would you like to update the previously inserted values? (y / n)")
            
            if sel == 'y':
                print("Update the device (re-insert every field)")
                device = update_dev(device.device_id)
            elif sel == 'n':
                continue
            else:
                print("Wrong character selected. Use 'y' for 'yes' and 'n' for 'no'.")
        else:
            print("Wrong character selected. Use 'y' for 'yes' and 'n' for 'no'.")



if __name__ == '__main__':
    main()