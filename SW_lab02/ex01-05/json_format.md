# JSON format

- identifier -> id
- end_points -> ep
  - rest -> r
    - (hostname -> hn)
    - (port -> pt)
    - get (read) -> r
    - post (create) -> c
    - put (update) -> u
    - delete -> d
      - value -> v
      - type -> t
  - mqtt -> m
    - (broker_hostname -> hn)
    - (broker_port -> pt)
    - (base_topic -> bt)
    - subscriber -> s
    - publisher -> p
      - value -> v
      - type -> t
- resources -> rs
  - name -> n
  - type -> t
- info -> in
  - description -> d
  - error -> e
  - message -> m
  - name -> n
  - surname -> s
  - emails -> e
    - value -> v

In end_points, if hn,pt or bt are specified, the other attributes are relative


## Catalog JSON
```JSON
{
    "ep": {
        "m": {
            "hn": [{"v": self._broker_hostname, "t": ""}],
            "pt": [{"v": self._broker_port, "t": ""}],
            "bt": [{"v": self._base_topic, "t": ""}]
        }
    }
}
```


## Subscribe and update

### Device JSON
```JSON
{
    "id": "device_id",
    "ep": {
        "r": {
            "r": [
                {"v": "127.0.0.1:8080/0", "t": "temp"},
                {"v": "127.0.0.1:8080/1", "t": "hum"}
            ],
            "c": [
                {"v": "127.0.0.1:8080/2", "t": "mot"}
            ]
        },
        "m": {
            "s": [
                {"v": "/IoT_lab/group3/device/0", "t": "mot"}
            ],
            "p": [
                {"v": "/IoT_lab/group3/device/1", "t": "temp"},
                {"v": "/IoT_lab/group3/device/2", "t": "hum"}
            ]
        }
    },
    "rs": [
        {"n": "temperature", "t": "temp"},
        {"n": "humidity", "t": "hum"},
        {"n": "motion_sensor", "t": "mot"}
    ]
}
```

### User JSON
```JSON
{
    "id": "user_id",
    "in": {
        "n": "Mario",
        "s": "Rossi",
        "e": [
            {"v": "mario.rossi@gmail.com"}
        ]
    }
}
```

### Service JSON
```JSON
{
    "id": "service_id",
    "ep": {
        "r": {
            "r": [
                {"v": "127.0.0.1:8080/0", "t": "temp"},
                {"v": "127.0.0.1:8080/1", "t": "hum"}
            ],
            "c": [
                {"v": "127.0.0.1:8080/2", "t": "mot"}
            ]
        },
        "m": {
            "s": [
                {"v": "/IoT_lab/group3/device/0", "t": "mot"}
            ],
            "p": [
                {"v": "/IoT_lab/group3/device/1", "t": "temp"},
                {"v": "/IoT_lab/group3/device/2", "t": "hum"}
            ]
        }
    },
    "rs": [
        {"n": "temperature", "t": "temp"},
        {"n": "humidity", "t": "hum"},
        {"n": "motion_sensor", "t": "mot"}
    ],
    "in": {
        "d": ""
    }
}
```


## MQTT response JSON
```JSON
{
    "in": {
        "e": 0/1,
        "m": "error_message"
    }
}
```


## REST response
No need of a JSON file
- On failure an HTTP error is raised
- On success the code 200 is returned + a confirmation string