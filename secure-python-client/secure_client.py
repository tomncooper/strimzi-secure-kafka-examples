#!/usr/bin/env python3
import argparse
import sys

from pprint import pprint

from kafka.errors import KafkaError

from secure_common import (
    load_kafka_config,
    get_topic_from_config,
    get_producer_settings_from_config,
    get_consumer_settings_from_config,
    get_password_from_args_or_env,
    KAFKA_SASL_PWD_ENV_VAR
)
from secure_producer import produce_messages, _default_message_generator
from secure_consumer import consume_messages


def create_producer_parser(subparsers):
    """Create producer subcommand parser"""
    producer_parser = subparsers.add_parser('producer', help='Run Kafka producer')
    producer_parser.add_argument('--config', required=True, help='Path to Kafka properties file')
    producer_parser.add_argument(
        '--topic',
        help='Kafka topic to produce to (overrides config file)'
    )
    producer_parser.add_argument(
        '--rate', type=float, help='Messages per second (overrides config file)')
    producer_parser.add_argument(
        '--message-size', type=int, help='Size of random message (overrides config file)')
    producer_parser.add_argument(
        '--max-messages',
        type=int,
        help='Maximum number of messages to produce (overrides config file)'
    )
    producer_parser.add_argument(
        '--sasl_password',
        help=f'SASL password (overrides {KAFKA_SASL_PWD_ENV_VAR} environment variable)'
    )
    return producer_parser


def create_consumer_parser(subparsers):
    """Create consumer subcommand parser"""
    consumer_parser = subparsers.add_parser('consumer', help='Run Kafka consumer')
    consumer_parser.add_argument('--config', required=True, help='Path to Kafka properties file')
    consumer_parser.add_argument(
        '--topic',
        help='Kafka topic to consume from (overrides config file)'
    )
    consumer_parser.add_argument(
        '--from-beginning',
        action='store_true',
        help='Read from beginning of topic'
    )
    consumer_parser.add_argument(
        '--max-messages',
        type=int,
        help='Maximum number of messages to consume (overrides config file)'
    )
    consumer_parser.add_argument(
        '--sasl_password',
        help=f'SASL password (overrides {KAFKA_SASL_PWD_ENV_VAR} environment variable)'
    )
    return consumer_parser


def run_producer(args):
    """Run the producer with given arguments"""
    try:
        # Get password from args or environment
        sasl_password = get_password_from_args_or_env(args.sasl_password)

        # Load Kafka configuration with producer-specific settings
        kafka_config = load_kafka_config(
            args.config,
            client_type='producer',
            sasl_password=sasl_password
        )

        # Get topic from config or command line
        topic = get_topic_from_config(args.config, args.topic)

        # Get producer settings from config with command line overrides
        producer_settings = get_producer_settings_from_config(args.config, args)

        print(
            f"Starting producer for topic '{topic}' at " +
            f"{producer_settings['rate']} messages/second"
        )
        print(f"Message size: {producer_settings['message_size']} characters")
        if producer_settings['max_messages']:
            print(f"Max messages: {producer_settings['max_messages']}")
        print("Using configuration:\n")
        # Create a copy of config without password for display
        display_config = kafka_config.copy()
        if 'sasl_plain_password' in display_config:
            display_config['sasl_plain_password'] = '***REDACTED***'
        pprint(display_config)
        print(f"\nProducer settings: {producer_settings}")
        print("\nPress Ctrl+C to stop...")

        # Create message generator with custom size
        def message_generator(count):
            return _default_message_generator(count, producer_settings['message_size'])

        # Produce messages
        message_count = produce_messages(
            kafka_config=kafka_config,
            topic=topic,
            rate=producer_settings['rate'],
            max_messages=producer_settings['max_messages'],
            message_generator=message_generator
        )

        print(f"Produced {message_count} messages to topic '{topic}'")

    except (IOError, ValueError, KeyError, KafkaError) as e:
        print(f"Producer error: {e}")
        sys.exit(1)


def run_consumer(args):
    """Run the consumer with given arguments"""
    try:
        # Get password from args or environment
        password = get_password_from_args_or_env(args.sasl_password)

        # Load Kafka configuration with consumer-specific settings
        kafka_config = load_kafka_config(
            args.config,
            client_type='consumer',
            sasl_password=password
        )

        # Get topic from config or command line
        topic = get_topic_from_config(args.config, args.topic)

        # Get consumer settings from config with command line overrides
        consumer_settings = get_consumer_settings_from_config(args.config, args)

        print(f"Starting consumer for topic '{topic}'")
        print(f"Using group ID '{kafka_config['group_id']}'")
        auto_offset = (
            'earliest'
            if args.from_beginning
            else kafka_config.get('auto_offset_reset', 'latest')
        )
        print("Auto offset reset: " + f"{auto_offset}")
        if consumer_settings['max_messages']:
            print(f"Max messages: {consumer_settings['max_messages']}")
        print("Using configuration:\n")
        # Create a copy of config without password for display
        display_config = kafka_config.copy()
        if 'sasl_plain_password' in display_config:
            display_config['sasl_plain_password'] = '***REDACTED***'
        pprint(display_config)
        print(f"\nConsumer settings: {consumer_settings}")
        print("\nPress Ctrl+C to stop...")
        print("-" * 80)

        # Consume messages
        message_count = consume_messages(
            kafka_config=kafka_config,
            topic=topic,
            group_id=kafka_config['group_id'],
            from_beginning=args.from_beginning,
            max_messages=consumer_settings['max_messages']
        )

        print(f"\nTotal messages consumed: {message_count}")

    except (IOError, ValueError, KeyError, KafkaError) as e:
        print(f"Consumer error: {e}")
        sys.exit(1)


def main():
    """Main entry point with subcommand parsing"""
    parser = argparse.ArgumentParser(
        description='Secure Kafka Client - Producer and Consumer',
    )

    # Create subparsers
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = True

    # Create producer and consumer subcommands
    create_producer_parser(subparsers)
    create_consumer_parser(subparsers)

    # Parse arguments
    args = parser.parse_args()

    # Route to appropriate function
    if args.command == 'producer':
        run_producer(args)
    elif args.command == 'consumer':
        run_consumer(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
