import time
import json

from kafka import KafkaConsumer


def consume_messages(
        kafka_config,
        topic,
        group_id=None,
        from_beginning=False,
        max_messages=None,
        message_callback=None
):
    """
    Consume messages from a Kafka topic

    Args:
        kafka_config (dict): Kafka configuration dictionary
        topic (str): Topic to consume from
        group_id (str, optional): Consumer group ID
        from_beginning (bool): Whether to read from beginning of topic
        max_messages (int, optional): Maximum number of messages to consume
        message_callback (callable, optional): Function to call for each message

    Returns:
        int: Number of messages consumed
    """
    # Override group_id if provided
    if group_id:
        kafka_config = kafka_config.copy()  # Don't modify original
        kafka_config['group_id'] = group_id

    # Set auto_offset_reset
    if from_beginning:
        kafka_config['auto_offset_reset'] = 'earliest'
    elif 'auto_offset_reset' not in kafka_config:
        kafka_config['auto_offset_reset'] = 'latest'

    # Create consumer
    consumer = KafkaConsumer(
        topic,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        **kafka_config
    )

    message_count = 0
    start_time = time.time()

    try:
        for message in consumer:
            message_count += 1

            # Call callback if provided, otherwise use default print behavior
            if message_callback:
                message_callback(message, message_count)
            else:
                _default_message_handler(message, message_count)

            # Check if we've reached the maximum number of messages
            if max_messages and message_count >= max_messages:
                break

    except KeyboardInterrupt:
        print(f"\nShutting down... Consumed {message_count} messages")
        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            print(f"Average rate: {message_count / elapsed_time:.2f} messages/second")
    finally:
        consumer.close()

    return message_count


def _default_message_handler(message, message_count):
    """Default message handler that prints message details"""
    print(f"Message {message_count}:")
    print(f"  Topic: {message.topic}")
    print(f"  Partition: {message.partition}")
    print(f"  Offset: {message.offset}")
    print(f"  Timestamp: {message.timestamp}")
    print(f"  Key: {message.key}")
    print(f"  Value: {message.value}")
    print("-" * 40)
