`docker-compose` 可以很方便地创建一些测试环境，比如 Redis 集群、Zookeeper 集群、Kafka 集群、MySQL 主从等等，方便学习。

**安装 docker-compose**

```sh
# 获取脚本
$ curl -L https://github.com/docker/compose/releases/download/1.25.0-rc2/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
# 赋予执行权限
$chmod +x /usr/local/bin/docker-compose 
```
