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

注意，如果设置了 Redis 客户端访问密码 requirepass， 那么也要设置相同的副本集同步密码 masterauth。

另外我们后面使用哨兵模式能够完成故障转移，现有的 Master 可能会变成 Slave，故在当前 Master 容器中也要携带 masterauth 参数。

```sh
redis-server \
  # 指定主节点
  --slaveof master-node 6379 \
  # redis 客户端访问密码
  --requirepass redis_pwd \
  # redis 主从同步密码
  --masterauth redis_pwd
```

因为 redis 集群和 sentinel 集群共用一个网络，这个网络定义在 redis 集群中，所以先拉起 redis 集群，当然也可以先手动创建网络，然后把两个集群加进去

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

**各节点 IP 地如下：**

```
master-node: 172.26.0.2

slave-node1: 172.26.0.4
slave-node2: 172.26.0.3

sentinel-1: 172.26.0.5
sentinel-2: 172.26.0.7
sentinel-3: 172.26.0.6
```

# 测试一下

**进入 master 容器，确认两个 slave 已经连接**

```sh
$docker-compose -f ./redis/docker-compose.yml exec master-node redis-cli -a redis_pwd info replication

# 主库信息
role:master
connected_slaves:2

# 从库信息
slave0:ip=172.26.0.3,port=6379,state=online,offset=305252,lag=1
slave1:ip=172.26.0.4,port=6379,state=online,offset=305252,lag=1

master_failover_state:no-failover

# 主从同步所用的 id 和 offset
master_replid:a80df57875df80925511853cdf056c14a85862e3
master_replid2:43812844acbaad94a9c1042cc5cbae43af67b86b
master_repl_offset:305252
second_repl_offset:278295

repl_backlog_active:1
repl_backlog_size:1048576
repl_backlog_first_byte_offset:278295
repl_backlog_histlen:26958

```

**进入 sentinel 容器，检查集群状态**

```sh
# 随便进入一个 sentinel 查看状态，端口是 sentinel-1.conf 配置中的端口
$docker-compose -f ./sentinel/docker-compose.yml exec sentinel-1 redis-cli -p 26379 info sentinel
# Sentinel
sentinel_masters:1
sentinel_tilt:0
sentinel_tilt_since_seconds:-1
sentinel_running_scripts:0
sentinel_scripts_queue_length:0
sentinel_simulate_failure_flags:0

# 可以看到主库状态
master0:name=mymaster,status=ok,address=172.26.0.2:6379,slaves=2,sentinels=3
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
  sentinel-3_1  | 1:X 22 Jun 2022 17:48:37.396 # -tilt #tilt mode exited
  ##############
  sentinel-3 发现节点下线
  ##############
  sentinel-3_1  | 1:X 22 Jun 2022 17:48:37.474 # +odown master mymaster 172.28.0.2 6379 #quorum 2/2
  sentinel-3_1  | 1:X 22 Jun 2022 17:48:37.474 # +new-epoch 1

  ##############
  进行 failover 故障转移
  ##############
  sentinel-3_1  | 1:X 22 Jun 2022 17:48:37.474 # +try-failover master mymaster 172.28.0.2 6379
  sentinel-3_1  | 1:X 22 Jun 2022 17:48:37.500 # +vote-for-leader 56cdcb561350a60f3a2bc00d1dd0cdef75bdcb13 1
  sentinel-2_1  | 1:X 22 Jun 2022 17:48:37.509 # +new-epoch 1

  ##############
  投了一票
  ##############
  sentinel-2_1  | 1:X 22 Jun 2022 17:48:37.520 # +vote-for-leader 56cdcb561350a60f3a2bc00d1dd0cdef75bdcb13 1
  sentinel-3_1  | 1:X 22 Jun 2022 17:48:37.521 # 5caaf2e095f6b45378d17ca264833aafef37e842 voted for 56cdcb561350a60f3a2bc00d1dd0cdef75bdcb13 1
  sentinel-3_1  | 1:X 22 Jun 2022 17:48:37.553 # +elected-leader master mymaster 172.28.0.2 6379
  sentinel-3_1  | 1:X 22 Jun 2022 17:48:37.553 # +failover-state-select-slave master mymaster 172.28.0.2 6379

  ##############
  最终选出新的主节点
  ##############
  sentinel-3_1  | 1:X 22 Jun 2022 17:48:37.637 # +selected-slave slave 172.28.0.4:6379 172.28.0.4 6379 @ mymaster 172.28.0.2 6379
  sentinel-3_1  | 1:X 22 Jun 2022 17:48:37.637 * +failover-state-send-slaveof-noone slave 172.28.0.4:6379 172.28.0.4 6379 @ mymaster 172.28.0.2 6379
  sentinel-3_1  | 1:X 22 Jun 2022 17:48:37.738 * +failover-state-wait-promotion slave 172.28.0.4:6379 172.28.0.4 6379 @ mymaster 172.28.0.2 6379

  ##############
  sentinel-2 发现节点下线
  ##############
  sentinel-2_1  | 1:X 22 Jun 2022 17:48:38.218 # +odown master mymaster 172.28.0.2 6379 #quorum 2/2
  sentinel-2_1  | 1:X 22 Jun 2022 17:48:38.218 # Next failover delay: I will not start a failover before Wed Jun 22 17:54:37 2022
  sentinel-3_1  | 1:X 22 Jun 2022 17:48:44.079 # +tilt #tilt mode entered
  sentinel-2_1  | 1:X 22 Jun 2022 17:48:56.301 # +tilt #tilt mode entered
  sentinel-3_1  | 1:X 22 Jun 2022 17:49:14.110 # -tilt #tilt mode exited
  sentinel-3_1  | 1:X 22 Jun 2022 17:49:14.188 # -odown master mymaster 172.28.0.2 6379
  sentinel-3_1  | 1:X 22 Jun 2022 17:49:14.222 # +promoted-slave slave 172.28.0.4:6379 172.28.0.4 6379 @ mymaster 172.28.0.2 6379
  sentinel-3_1  | 1:X 22 Jun 2022 17:49:14.222 # +failover-state-reconf-slaves master mymaster 172.28.0.2 6379
  sentinel-3_1  | 1:X 22 Jun 2022 17:49:14.252 * +slave-reconf-sent slave 172.28.0.3:6379 172.28.0.3 6379 @ mymaster 172.28.0.2 6379
  sentinel-2_1  | 1:X 22 Jun 2022 17:49:14.253 # +config-update-from sentinel 56cdcb561350a60f3a2bc00d1dd0cdef75bdcb13 172.28.0.5 26379 @ mymaster 172.28.0.  2 6379
  sentinel-2_1  | 1:X 22 Jun 2022 17:49:14.253 # +switch-master mymaster 172.28.0.2 6379 172.28.0.4 6379
  sentinel-2_1  | 1:X 22 Jun 2022 17:49:14.253 * +slave slave 172.28.0.3:6379 172.28.0.3 6379 @ mymaster 172.28.0.4 6379
  sentinel-2_1  | 1:X 22 Jun 2022 17:49:19.298 # +tilt #tilt mode entered









  sentinel-3_1  | 1:X 22 Jun 2022 17:49:27.369 # +tilt #tilt mode entered
  sentinel-2_1  | 1:X 22 Jun 2022 17:49:49.360 # -tilt #tilt mode exited
  sentinel-3_1  | 1:X 22 Jun 2022 17:49:57.411 # -tilt #tilt mode exited
  sentinel-3_1  | 1:X 22 Jun 2022 17:49:57.699 * +slave-reconf-inprog slave 172.28.0.3:6379 172.28.0.3 6379 @ mymaster 172.28.0.2 6379
  sentinel-3_1  | 1:X 22 Jun 2022 17:49:57.699 * +slave-reconf-done slave 172.28.0.3:6379 172.28.0.3 6379 @ mymaster 172.28.0.2 6379
  sentinel-3_1  | 1:X 22 Jun 2022 17:49:57.761 # +failover-end master mymaster 172.28.0.2 6379
  sentinel-3_1  | 1:X 22 Jun 2022 17:49:57.761 # +switch-master mymaster 172.28.0.2 6379 172.28.0.4 6379
  sentinel-3_1  | 1:X 22 Jun 2022 17:49:57.762 * +slave slave 172.28.0.3:6379 172.28.0.3 6379 @ mymaster 172.28.0.4 6379
  sentinel-3_1  | 1:X 22 Jun 2022 17:50:02.836 # +tilt #tilt mode entered
  sentinel-3_1  | 1:X 22 Jun 2022 17:50:32.841 # -tilt #tilt mode exited
  ```

# 坑

- 启动 sentinel 集群式，日志输出警告：**WARNING: Sentinel was not able to save the new configuration on disk!!!: Invalid argument**

  可以不管这个错误

- 当哨兵的配置 `sentinel monitor mymaster master-node 6379 2` 用到了主机名 `master-node` 时，无法进行故障转移，如果换成实际的 IP，这可以正常进行故障转移

  [官方文档所 6.2+ 是支持的](https://redis.io/docs/manual/sentinel/#ip-addresses-and-dns-names)，[但是在 github 上看到有个 close 的 issue](https://github.com/redis/redis/issues/8507)

  最终由 `redis:alpine` 换成正式版的镜像 `redis:latest` 就没问题了。。。

- TODO sentinel 可不可以公用一份配置
