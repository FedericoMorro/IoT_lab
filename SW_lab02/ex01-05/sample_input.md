```JSON
{
    "id": "device0",
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

```JSON
{
    "id": "device1",
    "end_points": {
        "REST": [
            {"value": "127.0.0.1:8080/0"}
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




```JSON
{
    "id": "user0",
    "info": {
        "name": "Mario",
        "surname": "Rossi",
        "emails": [
            {"value": "mario.rossi@gmail.com"}
        ]
    }
}
```

```JSON
{
    "id": "mario.bianchi@gmail.com",
    "info": {
        "name": "Mario",
        "surname": "Bianchi",
        "emails": [
            {"value": "mario.bianchi@gmail.com"}
        ]
    }
}
```



```JSON
{
    "id": "service0",
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

```JSON
{
    "id": "service1",
     "end_points": {
        "REST": [
            {"value": "127.0.0.1:8080/0"},
            {"value": "127.0.0.1:8080/1"}
        ]
    },
    "info": {
        "description": ""
    }
}
```