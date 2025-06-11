# Deploying Strimzi Kafka Cluster with SCRAM-SHA-512 Authentication

## Setup

Assuming you have a Kubernetes cluster set up and the Strimzi operator installed as per the instructions in the root README, you can deploy a Kafka cluster with SCRAM-SHA-512 authentication by applying the install files:

```shell
kubectl -n kafka apply -f install-files
```

This will create a Kafka cluster with:
- An internal listener on port 9093 with TLS encryption and SCRAM-SHA-512 authentication.
- An external NodePort listener on port 9094 with TLS encryption and SCRAM-SHA-512 authentication.
- A Kafka topic named `test-topic-1`.
- A Kafka topic named `test-topic-2`.
- A user (`admin`) with Super User permissions.
- A user (`client-1`) with permissions to produce and consume messages only from the `test-topic-1` topic.

## Verifying the Setup

Once the installation is complete we should now have a secure Kafka cluster running.
We can verify the setup by running some admin commands using the Kafka CLI tools. 

### Accessing the NodePort Listener

First, we need to expose the bootstrap service to access the Kafka cluster from outside the Kubernetes cluster. 

With minikube we can do this by running the following command:

```shell
minikube service -n kafka secure-kafka-secureext-bootstrap --url
```
This will setup a tunnel to the bootstrap service and return a URL that we can use to connect to the Kafka cluster. 
The URL will contain `http://` but this can be ignored. 
The `bootstrap-server` value for the secure listener will be the URL without the `http://` prefix.

### Obtaining the certificates and access credentials

In order to connect to the Kafka cluster using TLS, we need to obtain the root CA certificate used by the Kafka cluster.
This is created for you automatically by Strimzi and stored in a Kubernetes secret named `<kafka-cluster-name>-ca-cert`.
You can, alternatively, tell Strimzi to [use a custom CA certificate](https://strimzi.io/docs/operators/latest/deploying#installing-your-own-ca-certificates-str) from your own infrastructure.

```shell
kubectl -n kafka get secret secure-cluster-ca-cert -o jsonpath='{.data.ca\.crt}' | base64 -d > ca.crt
```

This will create a file named `ca.crt` in the current directory containing the CA certificate.
We then need to add this certificate to our trust store. 
For this example, we will create a new PKCS12 trust store named `client-truststore.p12` (with the password `changeit`) and import the CA certificate into it:

```shell
keytool -importcert -file ca.crt -alias secure-cluster-ca -keystore client-truststore.p12 -storetype PKCS12 -storepass changeit -noprompt
```

We then need to create a `admin.properties` file which will tell the Kafka CLI tools how to connect to the Kafka cluster securely.

```properties
ssl.truststore.location=client-truststore.p12
ssl.truststore.type=PKCS12
ssl.truststore.password=changeit
security.protocol=SASL_SSL
sasl.mechanism=SCRAM-SHA-512
```
To this we need to add the sasl.jaas.config for the user we want to authenticate as.
In this case we will use the `admin` user which has Super User permissions.
The jaas config can be obtained from the `admin` secret created by Strimzi when the user was created.

```shell
kubectl -n kafka get secret admin -o jsonpath='{.data.sasl\.jaas\.config}' | base64 -d > admin-jaas.conf
```

Copy the contents of `admin-jaas.conf` into the `admin.properties` file:

```properties
sasl.jaas.config=<contents of admin-jaas.conf>
```

The final required property is to set the `ssl.endpoint.identification.algorithm` to an empty string. 
This will disable hostname verification, which is convenient for local testing. 

```properties
ssl.endpoint.identification.algorithm=
```

This **should not be done in production environments**. 
In production you should enable hostname verification and ensure that the hostname in the broker's SSL certificate matches the hostname the client is trying to connect to.
Strimzi allows you to set the hostname in the broker's SSL certificate by [configuring the listener](https://strimzi.io/docs/operators/latest/configuring#type-GenericKafkaListenerConfigurationBroker-reference).

### Testing the Connection

Now that we have a configured `admin.properties` file, we can test the connection to the Kafka cluster using the Kafka CLI tools (these are in the `bin` directory of your Kafka installation).

```shell
kafka-topics.sh --bootstrap-server <bootstrap-server> --list --command-config admin.properties
```

Replace `<bootstrap-server>` with the value obtained from the `minikube service` command. If the connection is successful, you should see a list of two Kafka topics. `test-topic-1` and `test-topic-2`.

You can also produce and consume messages using the following commands:

```shell
kafka-console-producer.sh --bootstrap-server <bootstrap-server> --topic test-topic-2 --producer.config admin.properties
```
Type some messages into the console and press Enter after each to send them.
Press Ctrl+C to exit the producer.

```shell
kafka-console-consumer.sh --bootstrap-server <bootstrap-server> --topic test-topic-2 --from-beginning --consumer.config admin.properties
```
You should see the messages you sent in the producer console.

### Switching to the `client1` user

Now we have verified the secure connection is up and running, we can switch to the `client1` user which has limited permissions and will be used for our client applications.

```shell
kubectl -n kafka get secret client1 -o jsonpath='{.data.sasl\.jaas\.config}' | base64 -d > client1-jaas.conf
```

Copy the contents of the `admin.properties` file into a new file called `client.properties`. 
Replace the admin users `sasl.jaas.config` line with the contents of `client1-jaas.conf`:

```properties
sasl.jaas.config=<contents of client1-jaas.conf>
```

Now we can test the connection using the `client-1` user:

```shell
kafka-topics.sh --bootstrap-server <bootstrap-server> --list --command-config client.properties
```

If the connection is successful, you should see only the `test-topic-1` topic listed, as `client1` does not have permissions to access `test-topic-2`.

You can also produce and consume messages using the following commands:

```shell
kafka-console-producer.sh --bootstrap-server <bootstrap-server> --topic test-topic-1 --producer.config client.properties
```
Type some messages into the console and press Enter after each to send them.
Press Ctrl+C to exit the producer.  

You can then consume those messages using the following command. 
Note that we have to supply the consumer group ID here because, as we defined in the ACLs of the corresponding `KafkaUser` CR in the `install-files` directory, `client1` is only allowed to be part of that of consumer group `test-group-1` (the `admin` user is a super user and can be part of any group):

```shell
kafka-console-consumer.sh --bootstrap-server <bootstrap-server> --group test-group-1 --topic test-topic-1 --from-beginning --consumer.config client.properties
```

## Connecting Clients

### Java Clients

Coming soon...

### Python Clients

For this example we will use the [kafka-python](https://kafka-python.readthedocs.io/en/master/) client library.
All the code for the python client example is in the `secure-python-client` directory in repository root.

Assuming you have built the container image as described in the `secure-python-client/README.md`, you can run the producer and consumer applications in a containerized environment using Podman or Docker.

First create a configuration file named `config.ini` with the following content:

```ini
[kafka]
bootstrap_servers=<bootstrap-server>
ssl_cafile=ca.crt
ssl_check_hostname=false
security_protocol=SASL_SSL
sasl_mechanism=SCRAM-SHA-512
sasl_plain_username=client1

[producer]
acks=all
client_id=test-client-producer-1

[consumer]
group_id=test-group-1
client_id=test-client-consumer-1

[application]
topic=test-topic-1
```


You can then run the producer application using the following command.
Here we are mounting the `config.ini` file you created above and the CA certificate into the container so that the application can access them. 
This command assumes that both files are in the current directory:

```bash
podman run --rm -v $(pwd)/config.ini:/opt/app/config.ini:z -v $(pwd)/ca.crt:/opt/app/ca.crt:z secure-python-kafka-client:latest producer --config config.ini --sasl_password=<sasl-password>
```

You can find the sasl password from the jaas config you created earlier for the `client1` user or by running the following command:

```shell
kubectl -n kafka get secret client1 -o jsonpath='{.data.password}' | base64 -d
```
Make sure you exclude the `%` character at the end of the password when you pass it to the command above.

In another terminal, you can run the consumer application using the following command:

```bash
podman run --rm -v $(pwd)/config.ini:/opt/app/config.ini:z -v $(pwd)/ca.crt:/opt/app/ca.crt:z secure-python-kafka-client:latest consumer --config config.ini --sasl_password=<sasl-password>
```

You should see the producer sending messages to the `test-topic-1` topic and the consumer receiving them and printing them to the console.
Note that there may be a slight delay before output appears in the consumer console (depending on your docker/podman setup).