# Crowsnest processor opendlv GNSS

A processing microservice within the crowsnest ecosystem which listens on `GeodeticWgs84Reading, GeodeticHeadingReading & GroundSpeedReading`s from an OpenDLV session and converts and outputs to "brefv ish" format.

Output to MQTT broker JSON example:  

```json
{ 
    "sent_at": "2023-05-02T08:16:17.680988+00:00", 
    "message": {
      "latitude": 58.13716049333334, 
      "longitude": 12.118547173333331, 
      "heading": 214.43000506775013, 
      "sog": 7.2754386692047115
    }
}

```

## Docker compose example

```yml

version: '3'
services:

# From MO RISE image register
  crowsnest-processor-gnss-opendlv:
    image: ghcr.io/mo-rise/crowsnest-processor-opendlv-gnss:0.0.1
    container_name: cw-gnss-opendlv-0
    restart: unless-stopped
    network_mode: "host"
    environment:
      - CLUON_CID=65
      - CLUON_ENVELOPE_ID=1201
      - MQTT_BROKER_HOST=localhost
      - MQTT_BROKER_PORT=1883
      - MQTT_BASE_TOPIC=CROWSNEST/SEAHORSE/GNSS/0/JSON

# Build from project 
  crowsnest-processor-gnss-opendlv:
    build: .
    image: cw-gnss-opendlv
    container_name: cw-gnss-opendlv-0
    restart: unless-stopped
    network_mode: "host"
    environment:
      - CLUON_CID=65
      - CLUON_ENVELOPE_ID=1201
      - MQTT_BROKER_HOST=localhost
      - MQTT_BROKER_PORT=1883
      - MQTT_BASE_TOPIC=CROWSNEST/SEAHORSE/GNSS/0/JSON

```

## Development setup

To setup the development environment:

```bach
  python3 -m venv venv
  source ven/bin/activate
```

Install everything thats needed for development:

```bach
  pip install -r requirements_dev.txt
```

In addition, code for `brefv` must be generated using the following commands:

```bach
    mkdir brefv
    datamodel-codegen --input brefv-spec/envelope.json --input-file-type jsonschema --output brefv/envelope.py
    datamodel-codegen --input brefv-spec/messages --input-file-type jsonschema  --reuse-model --output brefv/messages
```

To run the linters:

```bach
    black main.py tests
    pylint main.py
```

To run the tests:

```bach
    python -m pytest --verbose tests
```

## License

Apache 2.0, see [LICENSE](./LICENSE)