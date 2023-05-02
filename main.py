"""Main entrypoint for this application"""
from datetime import datetime, timezone
from functools import lru_cache
from typing import Tuple
import logging
import warnings
import math

import numpy as np
from environs import Env
from streamz import Stream
from paho.mqtt.client import Client as MQTT

from pycluon import OD4Session, Envelope as cEnvelope
from pycluon.importer import import_odvd
from brefv.envelope import Envelope

# Reading config from environment variables
env = Env()

MQTT_BROKER_HOST = env("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = env.int("MQTT_BROKER_PORT", 1883)
MQTT_CLIENT_ID = env("MQTT_CLIENT_ID", None)
MQTT_TRANSPORT = env("MQTT_TRANSPORT", "tcp")
MQTT_TLS = env.bool("MQTT_TLS", False)
MQTT_USER = env("MQTT_USER", None)
MQTT_PASSWORD = env("MQTT_PASSWORD", None)
MQTT_BASE_TOPIC = env("MQTT_BASE_TOPIC", "CROWSNEST/SEAHORSE/GNSS/0/JSON")

CLUON_CID = env.int("CLUON_CID", 65)

LOG_LEVEL = env.log_level("LOG_LEVEL", logging.INFO)

## Import and generate code for message specifications
cluon_message_spec = import_odvd("gnss.odvd")

# Setup logger
logging.basicConfig(level=LOG_LEVEL)
logging.captureWarnings(True)
warnings.filterwarnings("once")
LOGGER = logging.getLogger("cw-processor-opendlv-gnss")

# Create mqtt client and confiure it according to configuration
mq = MQTT(client_id=MQTT_CLIENT_ID, transport=MQTT_TRANSPORT)
mq.username_pw_set(MQTT_USER, MQTT_PASSWORD)
if MQTT_TLS:
    mq.tls_set()



### Processing functions

def unpack_position(envelope: cEnvelope):
    """Extract a gnss message from the cluon envelope"""
    try:
        dlv_message = cluon_message_spec.opendlv_proxy_GeodeticWgs84Reading()
        dlv_message.ParseFromString(envelope.serialized_data)

        lat = dlv_message.latitude
        lon = dlv_message.longitude

        # LOGGER.debug("MSG ID: %s", data_IN)
        LOGGER.debug("Position IN: %s  %s", lat, lon)

        return {"latitude": lat, "longitude": lon}

    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Exception when unpacking a position message")


def unpack_heading(envelope: cEnvelope):
    """Extract a heading message from the cluon envelope"""
    try:
        dlv_message = cluon_message_spec.opendlv_proxy_GeodeticHeadingReading()
        dlv_message.ParseFromString(envelope.serialized_data)
        heading = math.degrees(dlv_message.northHeading)
        LOGGER.debug("Heading IN: %s", heading)

        return {"heading": heading}

    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Exception when unpacking a heading message")


def unpack_sog(envelope: cEnvelope):
    """Extract a heading message from the cluon envelope"""
    LOGGER.debug("Got envelope from pycluon")

    try:
        dlv_message = cluon_message_spec.opendlv_proxy_GroundSpeedReading()
        dlv_message.ParseFromString(envelope.serialized_data)
        sog = dlv_message.groundSpeed * 1.944
        LOGGER.debug("SOG IN: %s", sog)

        return {"sog": sog}

    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Exception when unpacking a SOG message")


def to_brefv(messages) -> Envelope:
    """To brefv envelope"""

    LOGGER.debug("Assembling new brefv envelope")

    LOGGER.debug("messages: %s ", messages)

    pos, sog, heading = messages

    envelope = Envelope(
        sent_at=datetime.now(timezone.utc).isoformat(),
        message={
            "latitude": pos["latitude"],
            "longitude": pos["longitude"],
            "heading": heading["heading"],
            "sog": sog["sog"],
        },
    )

    LOGGER.debug("envelope: %s ", envelope)

    return envelope


# EXAMPLE CROWSNEST Position message
# {
#     "sent_at": "2023-04-18T11:23:43.965988+00:00",
#     "message": {
#         "timestamp": "2023-04-18T11:24:01.810000+00:00",
#         "sog": 1.47,
#         "cog": 213.92,
#         "rot": 0.0,
#         "altitude": 6.01,
#         "gps_quality": 5,
#         "num_satellites": 28,
#         "longitude": 12.125421043333333,
#         "latitude": 58.141195201666676,
#         "heading": 199.09,
#         "roll": -12.33,
#         "pitch": "",
#         "roll_accuracy": 0.75,
#         "heading_accuracy": 0.579,
#         "std_dev_altitude": 0.032,
#         "std_dev_longitude": 0.031,
#         "std_dev_latitude": 0.024,
#     },
# }


def to_mqtt(envelope: Envelope):
    """Publish an envelope to a mqtt topic"""

    topic = f"{MQTT_BASE_TOPIC}"

    payload = envelope.json()

    LOGGER.debug("Publishing on %s with payload size: %s", topic, len(payload.encode()))
    try:
        mq.publish(
            topic,
            payload,
        )
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Failed publishing to broker!")


if __name__ == "__main__":

    # Setup pipeline
    source_pos = Stream()
    source_heading = Stream()
    source_speed = Stream()

    pipe_one = source_pos.map(unpack_position)
    pipe_two = source_heading.map(unpack_heading)
    pipe_three = source_heading.map(unpack_sog)

    # pipe_combined = pipe_one.zip_latest(pipe_two)
    pipe_combined = pipe_one.zip_latest(pipe_three, pipe_two)

    pipe_combined.map(to_brefv).sink(to_mqtt)

    # Connect to broker
    LOGGER.info("Connecting to MQTT broker %s %d", MQTT_BROKER_HOST, MQTT_BROKER_PORT)
    mq.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)

    LOGGER.info("All setup done, lets start processing messages!")

    # Register triggers
    session = OD4Session(CLUON_CID)
    session.add_data_trigger(19, source_pos.emit)
    session.add_data_trigger(1051, source_heading.emit)
    session.add_data_trigger(1046, source_speed.emit)

    mq.loop_forever()
