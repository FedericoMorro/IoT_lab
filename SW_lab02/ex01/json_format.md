## Device JSON
```JSON
{
    "type": "device",
    "id": "device_id",
    "end_points": {
        "REST": [
            {"uri": "127.0.0.1:8080/0"},
            {"uri": "127.0.0.1:8080/1"}
        ],
        "MQTT": [
            {"topic": "/IoT_lab/group3/device/0"}
        ]
    },
    "info": {
        "resources": [
            {"name": "temperature"},
            {"name": "humidity"},
            {"name": "motion_sensor"}
        ]
    }
}
```


## User JSON
```JSON
{
    "type": "user",
    "id": "user_id",
    "info": {
        "name": "Mario",
        "surname": "Rossi",
        "emails": [
            {"email": "mario.rossi@gmail.com"}
        ]
    }
}
```


## Service JSON
```JSON
{
    "type": "service",
    "id": "service_id",
    "end_points": {
        "REST": [
            {"uri": "127.0.0.1:8080/0"},
            {"uri": "127.0.0.1:8080/1"}
        ],
        "MQTT": [
            {"topic": "/IoT_lab/group3/device/0"}
        ]
    },
    "info": {
        "description": ""
    }
}
```