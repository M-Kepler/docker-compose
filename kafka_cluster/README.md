- [参考资料](#参考资料)
- [测试一下](#测试一下)
  - [按集群拆分 yml，接入已有 zookeeper 集群](#按集群拆分-yml接入已有-zookeeper-集群)
    - [zookeeper](#zookeeper)
    - [kafka](#kafka)
    - [kafka-manager](#kafka-manager)
  - [全写到一个文件中](#全写到一个文件中)

## 参考资料

| 变量                         | 描述                                                 |
| :--------------------------- | :--------------------------------------------------- |
| `KAFKA_BROKER_ID`            | kafka 集群中每个 kafka 都有一个 BROKER_ID 来区分自己 |
| `KAFKA_ADVERTISED_LISTENERS` | kafka 的地址和端口，用于向 zookeeper 注册            |
| `KAFKA_ADVERTISED_PORT`      | kafka 端口|
| `KAFKA_ADVERTISED_HOST_NAME` | 广播主机名称，一般用IP指定
| `KAFKA_ZOOKEEPER_CONNECT`    | zookeeper 地址                                       |
| `KAFKA_LISTENERS`            | kafka 监听端口                                       |
| `TZ`                         | 容器时区改为上海                                     |

## 测试一下

### 按集群拆分 yml，接入已有 zookeeper 集群

**因为和 zookeeper 集群分开配置，所以先进入 `zookeeper_cluster` 目录下启动 zookeeper 集群**

```sh
cd ../zookeeper_cluster
docker-compose up -d
```

#### zookeeper

[kafka 开启 jmx_port 后，报端口被占用](https://blog.csdn.net/weixin_37642251/article/details/90405635)

```sh
# 进入其中一个 kafka 容器，用里面的 zookeeper 客户端，连接 zookeeper 集群
docker exec -it broker1 bash

# 或者宿主机本身有 zookeeper 客户端也可以根据 IP 连接 zookeeper 集群
/opt/kafka_2.13-3.2.0/bin/zookeeper-shell.sh 172.25.0.2:2181

# 连接 zookeeper 集群
zookeeper-shell.sh zoo1:2181,zoo2:2181,zoo3:2181

# 查看 kafka1 节点信息
get /brokers/ids/1
{"features":{},"listener_security_protocol_map":{"PLAINTEXT":"PLAINTEXT"},"endpoints":["PLAINTEXT://broker1:9091"],"jmx_port":-1,"port":9091,"host":"broker1","version":5,"timestamp":"1655811906342"}

# 查看 kafka2 节点信息
get /brokers/ids/2
{"features":{},"listener_security_protocol_map":{"PLAINTEXT":"PLAINTEXT"},"endpoints":["PLAINTEXT://broker2:9092"],"jmx_port":-1,"port":9092,"host":"broker2","version":5,"timestamp":"1655811906128"}

# 查看 kafka3 节点信息
get /brokers/ids/3
{"features":{},"listener_security_protocol_map":{"PLAINTEXT":"PLAINTEXT"},"endpoints":["PLAINTEXT://broker3:9093"],"jmx_port":-1,"port":9093,"host":"broker3","version":5,"timestamp":"1655811906292"}

quit

```

#### kafka

```sh
# 进入节点 1 的容器
docker-compose -p kafka_cluster exec kafka1 bash

# 查看主题
kafka-topics.sh --list --bootstrap-server broker1:9091 broker2:9092 broker3:9093

# 创建主题
kafka-topics.sh --create --bootstrap-server broker1:9091 broker2:9092 broker3:9093 --replication-factor 3 --partitions 3 --topic test

# 查看主题详情
kafka-topics.sh --describe --bootstrap-server broker1:9091 broker2:9092 broker3:9093 --topic test
```

#### kafka-manager

```sh
# 拉起管理服务
docker-compose -f kafka-manager.yml up
```

浏览器访问 http://localhost:9002/ ，通过 `docker inspect [zookeeper_node_container_id]` 拿到 zookeeper 节点地址，填入 zookeeper 集群地址

### 全写到一个文件中

所有配置写到一个里面了，直接启动即可；配置和原有的差不多，只不过注释掉了网络部分。

```sh
cd kafka_cluster_all_in_one
docker-compose up
```
