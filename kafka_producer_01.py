import argparse
from uuid import uuid4
from six.moves import input
from confluent_kafka import Producer
# serilization part our object to binary form
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
import pandas as pd
from typing import List
import mysql.connector

# Configuration parameters for MySQL
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'H0134440h.'
MYSQL_DATABASE = 'kafka_sql'
MYSQL_TABLE = 'input_data_02'

# API key:
# KZPMMTWTSCYGC6HV

# API secret:
# 8uLuouD3fDrDS4nRslhBC5XZKgzc8DdHXynIh8C5j/yt1DCz1DE9VPTy+zl93sN4

# Bootstrap server:
# pkc-lzvrd.us-west4.gcp.confluent.cloud:9092



# Configuration parameters for Kafka
API_KEY = 'KZPMMTWTSCYGC6HV'
ENDPOINT_SCHEMA_URL  = 'https://psrc-k0w8v.us-central1.gcp.confluent.cloud'
API_SECRET_KEY = '8uLuouD3fDrDS4nRslhBC5XZKgzc8DdHXynIh8C5j/yt1DCz1DE9VPTy+zl93sN4'
BOOTSTRAP_SERVER = 'pkc-lzvrd.us-west4.gcp.confluent.cloud:9092'
SECURITY_PROTOCOL = 'SASL_SSL'
SSL_MACHENISM = 'PLAIN'
# put schema registry Api key from downloaded file:
SCHEMA_REGISTRY_API_KEY = 'TLDZUVLB5HCF6Q2G'
SCHEMA_REGISTRY_API_SECRET = 'WrAKSO1kvOar4lOHc6I+S+wZ4bgynEIxeW8MoYDsRBYJ6Pwakv7OpldFgBx4O1DS'


def sasl_conf():

    sasl_conf = {'sasl.mechanism': SSL_MACHENISM,
                 # Set to SASL_SSL to enable TLS support.
                #  'security.protocol': 'SASL_PLAINTEXT'}
                'bootstrap.servers':BOOTSTRAP_SERVER,
                'security.protocol': SECURITY_PROTOCOL,
                'sasl.username': API_KEY,
                'sasl.password': API_SECRET_KEY
                }
    return sasl_conf


def schema_config():
    return {'url': ENDPOINT_SCHEMA_URL,
            'basic.auth.user.info': f"{SCHEMA_REGISTRY_API_KEY}:{SCHEMA_REGISTRY_API_SECRET}"}


class Car:
    def __init__(self, record: dict):
        for k, v in record.items():
            setattr(self, k, v)

        self.record = record

    @staticmethod
    def dict_to_car(data: dict, ctx):
        return Car(record=data)

    def __str__(self):
        return f"{self.record}"


def get_car_instance():
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cursor = connection.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {MYSQL_TABLE}")
    while True:
        record = cursor.fetchone()
        if record is None:
            break
        car = Car(record)
        yield car


def car_to_dict(car: Car, ctx):
    """
    Returns a dict representation of a User instance for serialization.
    Args:
        user (User): User instance.
        ctx (SerializationContext): Metadata pertaining to the serialization
            operation.
    Returns:
        dict: Dict populated with user attributes to
"""
    return car.record


def delivery_report(err, msg):
    """
    Reports the success or failure of a message delivery.
    Args:
        err (KafkaError): The error that occurred on None on success.
        msg (Message): The message that was produced or failed.
    """

    if err is not None:
        print("Delivery failed for User record {}: {}".format(msg.key(), err))
        return
    print('User record {} successfully produced to {} [{}] at offset {}'.format(
        msg.key(), msg.topic(), msg.partition(), msg.offset()))


def main(topic):
    schema_registry_conf = schema_config()
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    # subjects = schema_registry_client.get_subjects()
    # print(subjects)
    subject = topic+'-value'

    schema = schema_registry_client.get_latest_version(subject)
    schema_str=schema.schema.schema_str

    string_serializer = StringSerializer('utf_8')
    json_serializer = JSONSerializer(schema_str, schema_registry_client, car_to_dict)

    producer = Producer(sasl_conf())

    print("Producing user records to topic {}. ^C to exit.".format(topic))
    #while True:
        # Serve on_delivery callbacks from previous calls to produce()
    producer.poll(0.0)
    i=0
    try:
        for car in get_car_instance():
          if i<100:
            print(car)
            producer.produce(topic=topic,
                            key=string_serializer(str(uuid4())), # uuid for create random string
                            value=json_serializer(car, SerializationContext(topic, MessageField.VALUE)),
                            on_delivery=delivery_report)
            i+=1
          else:
            break
    except KeyboardInterrupt:
        pass
    except ValueError:
        print("Invalid input, disdemo_infoding record...")
        pass

    print("\nFlushing records...")
    producer.flush()

main("topic_02")