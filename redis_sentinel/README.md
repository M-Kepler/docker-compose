- [参考资料](#参考资料)
- [搭建部署：一主二从三哨兵](#搭建部署一主二从三哨兵)
- [测试一下](#测试一下)
- [故障转移 failover](#故障转移-failover)
- [坑](#坑)

# 参考资料

[使用Docker-Compose搭建高可用redis哨兵集群](https://cloud.tencent.com/developer/article/1615281)

[深入理解Redis高可用方案-Sentinel](https://www.cnblogs.com/ivictor/p/9755065.html)

[Redis Sentinel的故障转移过程](https://blog.csdn.net/jiangxiulilinux/article/details/104993777)

[docker-compose 搭建 redis 哨兵集群](https://www.cnblogs.com/JulianHuang/p/12650721.html)

# 搭建部署：一主二从三哨兵

![image](https://images2017.cnblogs.com/blog/802666/201711/802666-20171102101833623-796701766.jpg)

这里没用 redis.conf 配置文件，通过命令参数指定了

注意，如果设置了 Redis 客户端访问密码 requirepass，另外我们后面使用哨兵模式能够完成故障转移，现有的 Master 可能会变成 Slave，故在当前 Master 容器中也要携带 masterauth 参数。

```sh
redis-server \
  # 指定主节点
  --slaveof master-node 6379 \
  # redis 客户端访问密码
  --requirepass redis_pwd \
  # redis 主从同步密码
  --masterauth redis_pwd
```

因为 redis 集群和 sentinel 集群共用一个 redis 集群中定义的网络，，所以先拉起 redis 集群，当然也可以先手动创建网络，然后把两个集群加进去

**哨兵启动方式**

```sh
# 方法一
redis-server /redis/sentinel.conf --sentinel

# 方法二
```

**拉起 redis 集群**

```sh
cd ./redis
docker-compose up
```

**拉起 sentinel 集群**

```sh
cd ./sentinel
docker-compose up
```

# 测试一下

**各节点 IP 地如下：**

```
master-node: 172.126.0.1

slave-node1: 172.126.0.2
slave-node2: 172.126.0.3

sentinel-1: 172.126.0.5
sentinel-2: 172.126.0.6
sentinel-3: 172.126.0.7
```

**进入 master 容器，确认两个 slave 已经连接**

```sh
$docker-compose -f ./redis/docker-compose.yml exec master-node redis-cli -a redis_pwd info replication

```

**进入 sentinel 容器，检查集群状态**

```sh
# 随便进入一个 sentinel 查看状态，端口是 sentinel-1.conf 配置中的端口
$docker-compose -f ./sentinel/docker-compose.yml exec sentinel-1 redis-cli -p 26379 info sentinel
```

# 故障转移 failover

- **关掉 master-node 主节点**

  ```sh
  cd ./redis
  docker-compose stop master-node
  ```

- **Redis 集群日志**

  ```log
  ```

- **sentinel 集群日志**

  ```log
  ```

# 坑

- **启动 sentinel 集群式，日志输出警告：WARNING: Sentinel was not able to save the new configuration on disk!!!: Invalid argument**

  指定 sentinel.conf 配置文件映射到容器内时直接使用文件映射, 这么做有可能导致哨兵没有写入配置文件的权限

  解决方案:使用文件夹映射，也可以不管这个错误

- **当哨兵的配置 `sentinel monitor mymaster master-node 6379 2` 用到了主机名 `master-node` 时，无法进行故障转移，如果换成实际的 IP，这可以正常进行故障转移**

  [官方文档说 6.2.6 是支持的](https://redis.io/docs/manual/sentinel/#ip-addresses-and-dns-names)，[但是在 github 上看到有个 close 的 issue](https://github.com/redis/redis/issues/8507)

  最终由 `redis:alpine` 换成正式版的镜像 `redis:latest` 就没问题了。。。尴尬的是 `redis:latest` 是 6.2.6 的版本，`redis:alpine` 是 7.0.2 版本，这个版本还更新一点呢

- **WARNING: Sentinel was not able to save the new configuration on disk!!!: Device or resource busy**

  虽然配置一样的，但是因为在故障转移过程中要修改配置，所以 sentinel 不可以公用一份配置
