- [参考资料](#参考资料)
- [docker-compose.yml 中的环境变量](#docker-composeyml-中的环境变量)
- [测试一下](#测试一下)

## 参考资料

[使用 docker 或者 docker-compose 部署 Zookeeper 集群](https://www.cnblogs.com/shanfeng1000/p/14488665.html)

## docker-compose.yml 中的环境变量

| 变量          | 描述                                         |
| :------------ | :------------------------------------------- |
| `ZOO_MY_ID`   | Zookeeper 节点的 ID                          |
| `ZOO_SERVERS` | Zookeeper 节点列表，多个节点之间使用空格隔开 |

## 测试一下

```sh
# 进入其中一个容器
docker-compose exec [container_name] bash

# 进入 zookeeper 客户端
/apache-zookeeper-3.8.0-bin/bin/zkCli.sh

# 执行命令查看节点，可以看到三个节点
[zk: localhost:2181(CONNECTED) 0] get /zookeeper/config
server.1=zoo1:2888:3888:participant;0.0.0.0:2181
server.2=zoo2:2888:3888:participant;0.0.0.0:2181
server.3=zoo3:2888:3888:participant;0.0.0.0:2181
version=0

```
