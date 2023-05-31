## Device JSON
```JSON
{
    "id": "device_id",
    "end_points": {
        "REST": [
            {"value": "127.0.0.1:8080/0"},
            {"value": "127.0.0.1:8080/1"}
        ],
        "MQTT": [
            {"value": "/IoT_lab/group3/device/0"}
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
    "id": "user_id",
    "info": {
        "name": "Mario",
        "surname": "Rossi",
        "emails": [
            {"value": "mario.rossi@gmail.com"}
        ]
    }
}
```


## Service JSON
```JSON
{
    "id": "service_id",
     "end_points": {
        "REST": [
            {"value": "127.0.0.1:8080/0"},
            {"value": "127.0.0.1:8080/1"}
        ],
        "MQTT": [
            {"value": "/IoT_lab/group3/device/0"}
        ]
    },
    "info": {
        "description": ""
    }
}
```