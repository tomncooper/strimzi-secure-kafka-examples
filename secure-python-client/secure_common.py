import configparser


CONFIG_KEY_MAP = {
    'bootstrap.servers': 'bootstrap_servers',
    'security.protocol': 'security_protocol',
    'sasl.mechanism': 'sasl_mechanism',
    'sasl.username': 'sasl_plain_username',
    'sasl.password': 'sasl_plain_password',
    'ssl.ca.location': 'ssl_cafile',
    'ssl.certificate.location': 'ssl_certfile',
    'ssl.key.location': 'ssl_keyfile',
    'ssl.key.password': 'ssl_keyfile_password',
    'ssl.check.hostname': 'ssl_check_hostname',
    'group.id': 'group_id',
    'auto.offset.reset': 'auto_offset_reset',
    'enable.auto.commit': 'enable_auto_commit'
}


def load_kafka_config(properties_file):
    """Load Kafka configuration from properties file"""
    config = configparser.ConfigParser()
    config.read(properties_file)

    kafka_config = {}
    for key, value in config['kafka'].items():
        if key in CONFIG_KEY_MAP:
            mapped_key = CONFIG_KEY_MAP[key]
            if key == 'bootstrap.servers':
                kafka_config[mapped_key] = value.split(',')
            elif key in ['ssl.check.hostname', 'enable.auto.commit']:
                kafka_config[mapped_key] = value.lower() == 'true'
            else:
                kafka_config[mapped_key] = value
        else:
            # Keep unmapped properties as-is
            kafka_config[key] = value

    return kafka_config
