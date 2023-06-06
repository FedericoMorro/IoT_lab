# Subscribe and refresh

## Device JSON
```JSON
{
    "id": "device_id",
    "end_points": {
        "REST": {
            "GET": [
                {"value": "127.0.0.1:8080/0"},
                {"value": "127.0.0.1:8080/1"}
            ],
            "PUT": [
                {"value": "127.0.0.1:8080/2"}
            ]
        },
        "MQTT": {
            "subscriber": [
                {"value": "/IoT_lab/group3/device/0"}
            ],
            "publisher": [
                {"value": "/IoT_lab/group3/device/1"},
                {"value": "/IoT_lab/group3/device/2"}
            ]
        }
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
        "REST": {
            "GET": [
                {"value": "127.0.0.1:8080/0"},
                {"value": "127.0.0.1:8080/1"}
            ],
            "PUT": [
                {"value": "127.0.0.1:8080/2"}
            ]
        },
        "MQTT": {
            "subscriber": [
                {"value": "/IoT_lab/group3/service/0"}
            ],
            "publisher": [
                {"value": "/IoT_lab/group3/service/1"},
                {"value": "/IoT_lab/group3/service/2"}
            ]
        }
    },
    "info": {
        "description": ""
    }
}
```



# MQTT response

```JSON
{
    "err": 0/1
    "msg": "error_message"
}
```



# REST response
No need of a JSON file
- On failure an HTTP error is raised
- On success the code 200 is returned + a confirmation string