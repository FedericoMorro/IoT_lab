# Subscribe and refresh


## Device JSON
- identifier -> id
- end_points -> ep
  - rest -> r
    - get (read) -> r
    - post (create) -> c
    - put (update) -> u
    - delete -> d
      - value -> v
  - mqtt -> m
    - subscriber -> s
    - publisher -> p
      - value -> v
- info -> in
  - resources -> r
    - name -> n
```JSON
{
    "id": "device_id",
    "ep": {
        "r": {
            "r": [
                {"v": "127.0.0.1:8080/0"},
                {"v": "127.0.0.1:8080/1"}
            ],
            "c": [
                {"v": "127.0.0.1:8080/2"}
            ]
        },
        "m": {
            "s": [
                {"v": "/IoT_lab/group3/device/0"}
            ],
            "p": [
                {"v": "/IoT_lab/group3/device/1"},
                {"v": "/IoT_lab/group3/device/2"}
            ]
        }
    },
    "in": {
        "r": [
            {"n": "temperature"},
            {"n": "humidity"},
            {"n": "motion_sensor"}
        ]
    }
}
```


## User JSON
- identifier -> id
- info -> in
  - name -> n
  - surname -> s
  - emails -> e
    - value -> v
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


## Service JSON
- identifier -> id
- end_points -> ep
  - rest -> r
    - get (read) -> r
    - post (create) -> c
    - put (update) -> u
    - delete -> d
      - value -> v
  - mqtt -> m
    - subscriber -> s
    - publisher -> p
      - value -> v
- info -> in
  - description -> d
```JSON
{
    "id": "service_id",
    "ep": {
        "r": {
            "r": [
                {"v": "127.0.0.1:8080/0"},
                {"v": "127.0.0.1:8080/1"}
            ],
            "c": [
                {"v": "127.0.0.1:8080/2"}
            ]
        },
        "m": {
            "s": [
                {"v": "/IoT_lab/group3/service/0"}
            ],
            "p": [
                {"v": "/IoT_lab/group3/service/1"},
                {"v": "/IoT_lab/group3/service/2"}
            ]
        }
    },
    "in": {
        "d": ""
    }
}
```


# MQTT


## MQTT broker
- hostname -> h
- port -> p
- base_topic -> t
```JSON
{
    "h": "127.0.0.1",
    "p": 8080,
    "t": "..."
}
```



## MQTT response
- error -> e
- message -> m
```JSON
{
    "e": 0/1
    "m": "error_message"
}
```



# REST response
No need of a JSON file
- On failure an HTTP error is raised
- On success the code 200 is returned + a confirmation string