import json
import time
import random
import string

from kafka import KafkaProducer
from kafka.errors import KafkaError


def generate_random_string(length=20):
    """Generate a random string of specified length"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def produce_messages(kafka_config, topic, rate=1.0, max_messages=-1, message_generator=None):
    """
    Produce messages to a Kafka topic

    Args:
        kafka_config (dict): Kafka configuration dictionary
        topic (str): Topic to produce to
        rate (float): Messages per second (0 for no rate limiting)
        max_messages (int): Maximum number of messages to produce, -1 for unlimited
        message_generator (callable, optional): Function to generate messages (takes message_count as arg)

    Returns:
        int: Number of messages produced
    """

    print("#### DEBUG #####")
    print(kafka_config)

    # Create producer
    producer = KafkaProducer(
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        **kafka_config
    )

    message_count = 0
    start_time = time.time()

    try:
        while True:
            # Generate message using provided generator or default
            if message_generator:
                message = message_generator(message_count)
            else:
                message = _default_message_generator(message_count)

            # Send message
            future = producer.send(topic, value=message)

            # Optional: wait for confirmation
            try:
                record_metadata = future.get(timeout=10)
                print(f"Message {message_count} sent to topic '{record_metadata.topic}' "
                      f"partition {record_metadata.partition} offset {record_metadata.offset}")
            except KafkaError as e:
                print(f"Failed to send message {message_count}: {e}")

            message_count += 1

            # Check if we've reached the maximum number of messages
            if max_messages > 0 and message_count >= max_messages:
                break

            # Control rate
            if rate > 0:
                time.sleep(1.0 / rate)

    except KeyboardInterrupt:
        print(f"\nShutting down... Sent {message_count} messages")
        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            print(f"Average rate: {message_count / elapsed_time:.2f} messages/second")
    finally:
        producer.close()

    return message_count


def _default_message_generator(message_count, message_size=20):
    """Default message generator that creates random messages"""
    return {
        'id': message_count,
        'timestamp': time.time(),
        'data': generate_random_string(message_size)
    }
