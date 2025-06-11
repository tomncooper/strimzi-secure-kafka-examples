# Secure Python Kafka Client Demo Application

This directory contains a simple Python application that demonstrates how to connect to a secure Kafka cluster using the `kafka-python` library. 

The producer application produced random string messages at a configurable rate to a Kafka topic, while the consumer application consumes messages from that topic and prints them to the console.

## Prerequisites

- Python 3.8 or later
- `kafka-python` library installed. You can install it by running the pip with the `requirements.txt` file:
  ```bash
  pip install -r requirements.txt
  ```

## Container image

The application is can also be packaged as a container image. 

You can build the image using the following command:
```bash
podman build -t secure-python-kafka-client:latest .
```

## Configuration

The application takes configuration parameters from a `.ini` format properties file. 
The keys should match the argument names for the [KafkaProducer](https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html) and [KafkaConsumer](https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html) classes in the `kafka-python` [library](https://kafka-python.readthedocs.io/en/master/index.html).
Common client configuration should be placed under the `[kafka]` section, while producer-specific configuration should be placed under the `[producer]` section and consumer-specific configuration under the `[consumer]` section.
The application also has an `[application]` section for application-specific settings such as the topic to produce/consume messages from, the rate of message production, the size of each message, and the maximum number of messages to process.
These can be set in the configuration file but also can be overridden by command line arguments.
The following is an example of a configuration file:

```ini
[kafka]
bootstrap_servers=<bootstrap-server>
ssl_ca_location=ca.crt
ssl_check_hostname=false
security_protocol=SASL_SSL
sasl_mechanism=SCRAM-SHA-512
sasl_plain_username=client1
sasl_plain_password=<password>
topic=test-topic-1

[application]
topic=test-topic-1
rate=1
message_size=100
max_messages=1000

[producer]
client_id=test-client-producer-1
acks=all

[consumer]
group_id=test-group-1
client_id=test-client-consumer-1
auto_offset_reset=earliest
```

## Running the Application

### Directly

To run the producer application, execute the following command:
```bash
python producer.py --config config.ini
```

To run the consumer application, execute the following command:

```bash
python consumer.py --config config.ini
```

### Containerized

Assuming you have built the container image as described above, you can run the producer and consumer applications in a containerized environment using Podman or Docker.

Make sure you have the `config.ini` file in the current directory, as it will be mounted into the container.

To run the producer application in a container, use the following command:
```bash
podman run --rm -v $(pwd)/config.ini:/opt/app/config.ini secure-python-kafka-client:latest producer --config config.ini
```

To run the consumer application in a container, use the following command:
```bash
podman run --rm -v $(pwd)/config.ini:/opt/app/config.ini secure-python-kafka-client:latest consumer --config config.ini
```