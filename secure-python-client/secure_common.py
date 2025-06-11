import configparser
import os
import warnings

KAFKA_CONFIG_SECTION_NAME = 'kafka'
APPLICATION_CONFIG_SECTION_NAME = 'application'
KAFKA_TOPIC_CONFIG_KEY = 'topic'
KAFKA_SASL_PWD_ENV_VAR = 'SASL_PASSWORD'


def _process_config_value(key, value):
    """Process a configuration value and handle any special cases or type conversion"""

    # Skip sasl_plain_password from config file - it will be set from password parameter
    if key == 'sasl_plain_password':
        warnings.warn(
            "sasl_plain_password is set in config file but will be overridden by " +
            f"--sasl_password argument or {KAFKA_SASL_PWD_ENV_VAR} environment variable"
        )
        return None

    if key == 'bootstrap_servers':
        return value.split(',')

    if key in ['ssl_check_hostname', 'enable_auto_commit']:
        return value.lower() == 'true'

    return value


def load_kafka_config(properties_file, client_type=None, sasl_password=None):
    """Load Kafka configuration from properties file

    Args:
        properties_file (str): Path to the properties file
        client_type (str, optional): 'producer' or 'consumer' to include specific settings
        sasl_password (str, optional): SASL password for the Kafka user this client will use

    Returns:
        dict: Kafka configuration dictionary
    """
    config = configparser.ConfigParser()
    config.read(properties_file)

    kafka_config = {}

    # Always include the kafka section (or DEFAULT if no kafka section)
    section_name = (
        KAFKA_CONFIG_SECTION_NAME
        if config.has_section(KAFKA_CONFIG_SECTION_NAME)
        else 'DEFAULT'
    )
    section = config[section_name]

    for key, value in section.items():
        # Handle special cases that need type conversion
        if (value := _process_config_value(key, value)) is not None:
            kafka_config[key] = value

    # Include client-specific settings if requested
    if client_type and config.has_section(client_type):
        client_section = config[client_type]
        for key, value in client_section.items():
            # Handle special cases that need type conversion
            if (value := _process_config_value(key, value)) is not None:
                kafka_config[key] = value

    # Set password from parameter if provided
    if sasl_password:
        kafka_config['sasl_plain_password'] = sasl_password
    elif kafka_config.get('sasl_mechanism'):
        # If SASL is configured but no password provided, raise error
        raise ValueError(
            "SASL password must be provided via --password argument "
            f"or {KAFKA_SASL_PWD_ENV_VAR} environment variable"
        )

    return kafka_config


def get_password_from_args_or_env(password_arg):
    """Get password from command line argument or environment variable

    Args:
        password_arg (str, optional): Password from command line

    Returns:
        str: Password or None if not found

    Raises:
        ValueError: If password is required but not found
    """
    if password_arg:
        return password_arg.strip()

    env_password = os.getenv(KAFKA_SASL_PWD_ENV_VAR)
    if env_password:
        return env_password.strip()

    return None


def get_topic_from_config(properties_file, command_line_topic=None):
    """Get topic from config or command line, with command line taking precedence"""
    if command_line_topic:
        return command_line_topic

    config = configparser.ConfigParser()
    config.read(properties_file)

    if not config.has_section(APPLICATION_CONFIG_SECTION_NAME):
        raise ValueError(
            f"Configuration file {properties_file} does not " +
            f"contain section '{APPLICATION_CONFIG_SECTION_NAME}'"
        )

    topic = config.get(APPLICATION_CONFIG_SECTION_NAME, KAFKA_TOPIC_CONFIG_KEY, fallback=None)
    if not topic:
        raise ValueError("Topic must be specified either in config file or via --topic argument")

    return topic


def get_producer_settings_from_config(properties_file, args):
    """Get producer settings from config file, with command line arguments taking precedence

    Args:
        properties_file (str): Path to the properties file
        args: Command line arguments

    Returns:
        dict: Producer settings with resolved values
    """
    config = configparser.ConfigParser()
    config.read(properties_file)

    # Default values
    settings = {
        'rate': 1.0,
        'message_size': 20,
        'max_messages': -1,
    }

    # Load from application section if it exists
    if config.has_section(APPLICATION_CONFIG_SECTION_NAME):
        app_section = config[APPLICATION_CONFIG_SECTION_NAME]

        if 'rate' in app_section:
            settings['rate'] = float(app_section['rate'])
        if 'message_size' in app_section:
            settings['message_size'] = int(app_section['message_size'])
        if 'max_messages' in app_section:
            settings['max_messages'] = int(app_section['max_messages'])

    # Override with command line arguments if provided
    if hasattr(args, 'rate') and args.rate is not None:
        settings['rate'] = args.rate
    if hasattr(args, 'message_size') and args.message_size is not None:
        settings['message_size'] = args.message_size
    if hasattr(args, 'max_messages') and args.max_messages is not None:
        settings['max_messages'] = args.max_messages

    return settings


def get_consumer_settings_from_config(properties_file, args):
    """Get consumer settings from config file, with command line arguments taking precedence

    Args:
        properties_file (str): Path to the properties file
        args: Command line arguments

    Returns:
        dict: Consumer settings with resolved values
    """
    config = configparser.ConfigParser()
    config.read(properties_file)

    # Default values
    settings = {
        'max_messages': -1,
    }

    # Load from application section if it exists
    if config.has_section(APPLICATION_CONFIG_SECTION_NAME):
        app_section = config[APPLICATION_CONFIG_SECTION_NAME]

        if 'max_messages' in app_section:
            settings['max_messages'] = int(app_section['max_messages'])

    # Override with command line arguments if provided
    if hasattr(args, 'max_messages') and args.max_messages is not None:
        settings['max_messages'] = args.max_messages

    return settings
