# Strimzi Secure Kafka Examples

This repository contains example code and walk-throughs covering secure Kafka deployments and client setup using [Strimzi](https://strimzi.io/).

## Setup

The examples in this repository assume you are running [minikube](https://minikube.sigs.k8s.io/docs/), however they should work on any Kubernetes cluster (such as [KIND](https://kind.sigs.k8s.io/) or a remote cluster).

Make sure you start minikube with sufficient resources, for example:
```shell
minikube start --cpus=4 --memory=8g --disk-size=30g
```
To run the examples you will need to have [Strimzi](https://strimzi.io/) installed in your cluster.
First create a namespace to run the Strimzi operator and Kafka cluster in:
```shell
kubectl create namespace kafka
```
Then install the operator (version 0.46.0). First download the operator install files:
```shell
curl -LO https://github.com/strimzi/strimzi-kafka-operator/releases/download/0.46.0/strimzi-cluster-operator-0.46.0.yaml
```
Update the namespace to make the one you created above (on MacOS you may need to use `sed -i ''`):
```shell
sed -i 's/namespace: .*/namespace: kafka/' strimzi-cluster-operator-0.46.0.yaml
```
```shell
kubectl -n kafka apply -f strimzi-cluster-operator-0.46.0.yaml
```
