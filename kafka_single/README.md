- [参考资料](#参考资料)
- [测试一下](#测试一下)
  - [kafka](#kafka)
  - [zookeeper](#zookeeper)

## 参考资料

[Set up a Kafka With Docker](https://developer.confluent.io/quickstart/kafka-docker/)

## 测试一下

### kafka

```sh
# 进入到容器
docker-compose -p kafka_single exec broker bash

# 查看主题
[appuser@119ede18cbb2 ~]$ kafka-topics --list --bootstrap-server localhost:9092

# 创建主题
[appuser@119ede18cbb2 ~]$ kafka-topics --create --bootstrap-server localhost:9092 --topic test
Created topic test.

# 查看主题详情
[appuser@119ede18cbb2 ~]$ kafka-topics --describe --bootstrap-server localhost:9092 --topic test
Topic: test     TopicId: ikAub9q6QcW9qUakngNwfQ PartitionCount: 1       ReplicationFactor: 1    Configs:
        Topic: test     Partition: 0    Leader: 1       Replicas: 1     Isr: 1

```

### zookeeper

```sh
# 进入 zookeeper 客户端
[appuser@119ede18cbb2 ~]$ zookeeper-shell zookeeper:2181
Connecting to zookeeper:2181
Welcome to ZooKeeper!
JLine support is disabled

WATCHER::

WatchedEvent state:SyncConnected type:None path:null

# 查看根目录
ls /
[admin, brokers, cluster, config, consumers, controller, controller_epoch, feature, isr_change_notification, latest_producer_id_block, log_dir_event_notification, zookeeper]

# 查看主题
get /brokers/topics/test
{"partitions":{"0":[1]},"topic_id":"ikAub9q6QcW9qUakngNwfQ","adding_replicas":{},"removing_replicas":{},"version":3}

```
