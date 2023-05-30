## Device JSON
```JSON
{
    "type": "device",
    "id": "device_id",
    "REST": [
        {"uri": "127.0.0.1:8080/0"},
        {"uri": "127.0.0.1:8080/1"}
    ],
    "MQTT": [
        {"topic": "/IoT_lab/group3/device/0"}
    ],
    "resources": [
        {"name": "temperature"},
        {"name": "humidity"},
        {"name": "motion_sensor"}
    ]
}
```


## User JSON
```JSON
{
    "type": "user",
    "id": "user_id",
    "name": "Mario",
    "surname": "Rossi",
    "emails": [
        {"email": "mario.rossi@gmail.com"}
    ]
}
```


## Service JSON
```JSON
{
    "type": "service",
    "id": "service_id",
    "description": "",
    "REST": [
        {"uri": "127.0.0.1:8080/0"},
        {"uri": "127.0.0.1:8080/1"}
    ],
    "MQTT": [
        {"topic": "/IoT_lab/group3/service/0"}
    ]
}
```