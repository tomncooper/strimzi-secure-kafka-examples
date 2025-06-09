#!/usr/bin/env python3
import argparse
import sys

from pprint import pprint

from secure_common import load_kafka_config
from secure_producer import produce_messages, _default_message_generator
from secure_consumer import consume_messages


def create_producer_parser(subparsers):
    """Create producer subcommand parser"""
    producer_parser = subparsers.add_parser('producer', help='Run Kafka producer')
    producer_parser.add_argument('--config', required=True, help='Path to Kafka properties file')
    producer_parser.add_argument('--topic', required=True, help='Kafka topic to produce to')
    producer_parser.add_argument(
        '--rate', type=float, default=1.0, help='Messages per second (default: 1.0)')
    producer_parser.add_argument(
        '--message-size', type=int, default=20, help='Size of random message (default: 20)')
    producer_parser.add_argument(
        '--max-messages', type=int, help='Maximum number of messages to produce')
    return producer_parser


def create_consumer_parser(subparsers):
    """Create consumer subcommand parser"""
    consumer_parser = subparsers.add_parser('consumer', help='Run Kafka consumer')
    consumer_parser.add_argument('--config', required=True, help='Path to Kafka properties file')
    consumer_parser.add_argument('--topic', required=True, help='Kafka topic to consume from')
    consumer_parser.add_argument(
        '--group-id',
        help='Consumer group ID'
    )
    consumer_parser.add_argument(
        '--from-beginning',
        action='store_true',
        help='Read from beginning of topic'
    )
    consumer_parser.add_argument(
        '--max-messages', type=int, help='Maximum number of messages to consume')
    return consumer_parser


def run_producer(args):
    """Run the producer with given arguments"""
    try:
        # Load Kafka configuration
        kafka_config = load_kafka_config(args.config)

        print(f"Starting producer for topic '{args.topic}' at {args.rate} messages/second")
        print(f"Message size: {args.message_size} characters")
        if args.max_messages:
            print(f"Max messages: {args.max_messages}")
        print("Using configuration:\n")
        pprint(kafka_config)
        print("\n")
        print("Press Ctrl+C to stop...")

        # Create message generator with custom size
        def message_generator(count):
            return _default_message_generator(count, args.message_size)

        # Produce messages
        message_count = produce_messages(
            kafka_config=kafka_config,
            topic=args.topic,
            rate=args.rate,
            max_messages=args.max_messages,
            message_generator=message_generator
        )

        print(f"Produced {message_count} messages to topic '{args.topic}'")

    except Exception as e:
        print(f"Producer error: {e}")
        sys.exit(1)


def run_consumer(args):
    """Run the consumer with given arguments"""
    try:
        # Load Kafka configuration
        kafka_config = load_kafka_config(args.config)

        print(f"Starting consumer for topic '{args.topic}'")
        if args.group_id:
            print(f"Using group ID '{args.group_id}'")
        print(
            "Auto offset reset: " +
            f"{'earliest' if args.from_beginning else kafka_config.get('auto_offset_reset', 'latest')}"
        )
        if args.max_messages:
            print(f"Max messages: {args.max_messages}")
        print("Using configuration:\n")
        pprint(kafka_config)
        print("\n")
        print("Press Ctrl+C to stop...")
        print("-" * 80)

        # Consume messages
        message_count = consume_messages(
            kafka_config=kafka_config,
            topic=args.topic,
            group_id=args.group_id,
            from_beginning=args.from_beginning,
            max_messages=args.max_messages
        )

        print(f"\nTotal messages consumed: {message_count}")

    except Exception as e:
        print(f"Consumer error: {e}")
        sys.exit(1)


def main():
    """Main entry point with subcommand parsing"""
    parser = argparse.ArgumentParser(
        description='Secure Kafka Client - Producer and Consumer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s producer --config kafka.properties --topic my-topic --rate 2.0
  %(prog)s consumer --config kafka.properties --topic my-topic --from-beginning
  %(prog)s consumer --config kafka.properties --topic my-topic --group-id my-group --max-messages 10
        """
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
