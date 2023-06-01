import time
from threading import Thread
import Device


REFRESH_TIME = 60


def insert_dev() -> Device:
    print("Insert a new device")
    
    tmp_device_id = input("Insert the device id: ")

    rest_ep_list = list()
    rest_ep_n = int(input("How many REST endpoints does the device have? "))
    for i in range(0, rest_ep_n, 1):
        tmp_device_rest_ep = input("Insert the REST device endpoint: ")
        rest_ep_list.append({"value": tmp_device_rest_ep})

    mqtt_ep_list = list()
    mqtt_ep_n = int(input("How many MQTT endpoints does the device have? "))
    for i in range(0, mqtt_ep_n, 1):
        tmp_device_mqtt_ep = input("Insert the MQTT device endpoint: ")
        mqtt_ep_list.append({"value": tmp_device_mqtt_ep})

    resrc_list = list()
    resrc_n = int(input("How many types of resources type does the device have? "))
    for i in range(0, resrc_n, 1):
        tmp_device_resource = input("Insert the device resource type: ")
        resrc_list.append({"name": tmp_device_resource})

    tmp_device = Device(
        tmp_device_id,
        rest_ep_list,
        mqtt_ep_list,
        resrc_list
    )
    
    return tmp_device


def refresh(device: Device):
    while True:
        device.update()
        time.sleep(REFRESH_TIME)


def main():
    device: Device
    Thread(target = refresh, args = (device))

    while True:
        sel = input("Would you like to creating a new device? (y / n): ")
        if sel == 'y':
            device = insert_dev()
        elif sel == 'n':
            continue
        else:
            print("Wrong character selected. Use 'y' for 'yes' and 'n' for 'no'.")



if __name__ == '__main__':
    main()