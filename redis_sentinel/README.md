- [参考资料](#参考资料)
- [搭建部署：一主二从三哨兵](#搭建部署一主二从三哨兵)
- [测试一下](#测试一下)
- [故障转移 failover](#故障转移-failover)
  - [模拟 redis 集群主节点掉线](#模拟-redis-集群主节点掉线)
  - [redis 集群原主节点重新上线](#redis-集群原主节点重新上线)
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
redis-server /path/to/sentinel.conf --sentinel

# 方法二
redis-sentinel /path/to/sentinel.conf
```

**拉起 redis 集群**

```sh
docker-compose -f ./redis/docker-compose.yml up
```

**拉起 sentinel 集群**

```sh
docker-compose -f ./sentinel/docker-compose.yml up
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

# 主库信息
role:master
connected_slaves:2

# 从库信息
slave0:ip=172.126.0.3,port=6379,state=online,offset=2942,lag=1
slave1:ip=172.126.0.2,port=6379,state=online,offset=2942,lag=1

# 故障迁移信息
master_failover_state:no-failover

# 主从复制的 id 和 offset
master_replid:727dd4ada94d08666bba57c15e1a2e28e221fc2c
master_replid2:0000000000000000000000000000000000000000
master_repl_offset:3230
second_repl_offset:-1

# 主从复制时保存的缓存命令
repl_backlog_active:1
repl_backlog_size:1048576
repl_backlog_first_byte_offset:1
repl_backlog_histlen:3230

```

**进入 sentinel 容器，检查集群状态**

```sh
# 随便进入一个 sentinel 查看状态，端口是 sentinel-1.conf 配置中的端口
$docker-compose -f ./sentinel/docker-compose.yml exec sentinel-1 redis-cli -p 26379 info sentinel

sentinel_masters:1
sentinel_tilt:0
sentinel_tilt_since_seconds:-1
sentinel_running_scripts:0
sentinel_scripts_queue_length:0
sentinel_simulate_failure_flags:0

# sentinel 信息，可以看到 主库是 172.126.0.1，两个从节点，三个哨兵
master0:name=mymaster,status=ok,address=172.126.0.1:6379,slaves=2,sentinels=3
```

# 故障转移 failover

## 模拟 redis 集群主节点掉线

- **关掉 master-node 主节点**

  ```sh
  docker-compose -f ./redis/docker-compose.yml stop master-node
  ```

- **Redis 集群日志**

  ```log
  ###################
  主节点下线
  ###################
  redis-master-node-1  | 1:signal-handler (1655949381) Received SIGTERM scheduling shutdown...
  redis-master-node-1  | 1:M 23 Jun 2022 01:56:21.379 # User requested shutdown...
  redis-master-node-1  | 1:M 23 Jun 2022 01:56:21.380 * Waiting for replicas before shutting down.
  redis-master-node-1  | 1:M 23 Jun 2022 01:56:21.581 * 2 of 2 replicas are in sync when shutting down.
  redis-master-node-1  | 1:M 23 Jun 2022 01:56:21.581 * Saving the final RDB snapshot before exiting.
  redis-master-node-1  | 1:M 23 Jun 2022 01:56:21.660 * DB saved on disk
  redis-master-node-1  | 1:M 23 Jun 2022 01:56:21.660 # Redis is now ready to exit, bye bye...

  ###################
  从节点与主节点连接丢失
  ###################

  redis-slave-node2-1  | 1:S 23 Jun 2022 01:56:21.685 # Connection with master lost.
  redis-slave-node2-1  | 1:S 23 Jun 2022 01:56:21.686 * Caching the disconnected master state.
  redis-slave-node2-1  | 1:S 23 Jun 2022 01:56:21.686 * Reconnecting to MASTER master-node:6379
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:56:21.685 # Connection with master lost.
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:56:21.685 * Caching the disconnected master state.
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:56:21.685 * Reconnecting to MASTER master-node:6379
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:56:21.691 * MASTER <-> REPLICA sync started
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:56:21.691 # Error condition on socket for SYNC: Connection refused
  redis-slave-node2-1  | 1:S 23 Jun 2022 01:56:21.695 * MASTER <-> REPLICA sync started
  redis-slave-node2-1  | 1:S 23 Jun 2022 01:56:21.695 # Error condition on socket for SYNC: Connection refused
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:56:22.591 * Connecting to MASTER master-node:6379
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:56:22.594 * MASTER <-> REPLICA sync started
  redis-slave-node2-1  | 1:S 23 Jun 2022 01:56:22.613 * Connecting to MASTER master-node:6379
  redis-slave-node2-1  | 1:S 23 Jun 2022 01:56:22.640 * MASTER <-> REPLICA sync started
  redis-master-node-1 exited with code 0
  redis-master-node-1 exited with code 0

  ###################
  故障转移后
  ###################

  redis-slave-node1-1  | 1:S 23 Jun 2022 01:57:40.166 * Connecting to MASTER master-node:6379
  redis-slave-node2-1  | 1:M 23 Jun 2022 01:57:40.621 * Discarding previously cached master state.
  redis-slave-node2-1  | 1:M 23 Jun 2022 01:57:40.621 # Setting secondary replication ID to b4fa318e23e6ac4e613bc6e9de0c169342407438, valid up to offset: 4496. New replication ID is cc4224af792add3518719d5a6925da04a8379d95

  ###################
  slave-node2 被 sentinel-2 推举为主节点
  ###################

  redis-slave-node2-1  | 1:M 23 Jun 2022 01:57:40.621 * MASTER MODE enabled (user request from 'id=3 addr=172.126.0.6:46398 laddr=172.126.0.3:6379 fd=9 name=sentinel-2cd20474-cmd age=102 idle=0 flags=x db=0 sub=0 psub=0 multi=4 qbuf=188 qbuf-free=20286 argv-mem=4 multi-mem=169 rbs=1024 rbp=45 obl=45 oll=0 omem=0 tot-mem=22469 events=r cmd=exec user=default redir=-1 resp=2')
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:57:48.198 # Unable to connect to MASTER: Invalid argument
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:57:48.199 * Connecting to MASTER 172.126.0.3:6379
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:57:48.199 * MASTER <-> REPLICA sync started

  ###################
  slave-node1 连接新的主节点
  ###################
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:57:48.199 * REPLICAOF 172.126.0.3:6379 enabled (user request from 'id=3 addr=172.126.0.6:33268 laddr=172.126.0.2:6379 fd=9 name=sentinel-2cd20474-cmd age=110 idle=8 flags=x db=0 sub=0 psub=0 multi=4 qbuf=6066 qbuf-free=14408 argv-mem=4 multi-mem=179 rbs=1024 rbp=1024 obl=1024 oll=4 omem=82016 tot-mem=104495 events=r cmd=exec user=default redir=-1 resp=2')

  redis-slave-node1-1  | 1:S 23 Jun 2022 01:57:48.228 * Non blocking connect for SYNC fired the event.
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:57:48.279 * Master replied to PING, replication can continue...
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:57:48.290 * Trying a partial resynchronization (request b4fa318e23e6ac4e613bc6e9de0c169342407438:4496).
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:57:48.295 * Successful partial resynchronization with master.
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:57:48.295 # Master replication ID changed to cc4224af792add3518719d5a6925da04a8379d95
  redis-slave-node1-1  | 1:S 23 Jun 2022 01:57:48.295 * MASTER <-> REPLICA sync: Master accepted a Partial Resynchronization.
  redis-slave-node2-1  | 1:M 23 Jun 2022 01:57:48.292 * Replica 172.126.0.2:6379 asks for synchronization
  redis-slave-node2-1  | 1:M 23 Jun 2022 01:57:48.293 * Partial resynchronization request from 172.126.0.2:6379 accepted. Sending 1667 bytes of backlog starting from offset 4496.

  ```

- **sentinel 集群日志**

  [Redis 哨兵模式下，Master 节点宕机后，进行故障转移的过程日志分析](https://blog.csdn.net/miaomiao19971215/article/details/108567837)

  ```log
  1. +sdown: 哨兵节点主观认为 master 下线
  +sdown master mymaster 172.126.0.1 6379

  2. 当主观认为节点下线的哨兵数量到达 quorum 后，就认为节点已经客观下线了 
  +odown master mymaster 172.126.0.1 6379 #quorum 2/2

  3. 开始对 IP 为 172.126.0.1 端口为 6379，名为 "mymaster" 的 Redis 集群进行故障转移
  try-failover master mymaster 172.126.0.1 6379

  4. 在哨兵集群中投票选举出一个哨兵，作为本次执行故障转移操作的 leader。
  +vote-for-leader 2cd204746a7043140ce30cd21812ab158e601ac4 2


  5.在哨兵集群中再次确认进行即将执行故障转移的 leader 是哪一个哨兵
  +elected-leader master mymaster 172.126.0.1 6379

  6. leader 开始在集群中寻找合适的 slave
  +failover-state-select-slave master mymaster 172.126.0.1 6379

  7. 已经找到了合适的 slave 作为新的 master，它是位于 S2 服务器上的 192.168.50.122 6379 Redis 服务。
  +selected-slave slave 172.126.0.3:6379 172.126.0.3 6379 @ mymaster 172.126.0.1 6379

  8. 新主节点 slave-node3 向目标 slave-node2 发送 "slaveof-noone" 指令，令其不要再做其它任何节点的 slave 了，从现在开始，它就是老大，完成从 slave 到 master 的转换
  +failover-state-send-slaveof-noone slave 172.126.0.3:6379 172.126.0.3 6379 @ mymaster 172.126.0.1 6379

  9. 开始对 sentinel 集群中的所有 slave 做 reconf 操作 (广播新的节点配置，sentinel 节点更新配置信息)
  +failover-state-reconf-slaves master mymaster 172.126.0.1 6379

  10. 修改 redis 集群中节点的从属关系
  +slave-reconf-sent slave 172.126.0.2:6379 172.126.0.2 6379 @ mymaster 172.126.0.1 6379

  11. 目标 slave 配置信息更新完毕，leader 可以对下一个 slave 开始 reconfig 操作了。
  +slave-reconf-done slave 172.126.0.2:6379 172.126.0.2 6379 @ mymaster 172.126.0.1 6379

  12. 故障转移完成
  +failover-end master mymaster 172.126.0.1 6379

  13. 故障转移完毕后，各个 sentinel 开始监控新的 master。
  +switch-master mymaster 172.126.0.1 6379 172.126.0.3 6379
  ```

- **再看一下集群状态**

  ```sh
  # Sentinel
  sentinel_masters:1
  sentinel_tilt:0
  sentinel_tilt_since_seconds:-1
  sentinel_running_scripts:0
  sentinel_scripts_queue_length:0
  sentinel_simulate_failure_flags:0

  # 已经切换到 172.126.0.3 即 slave-node2
  master0:name=mymaster,status=ok,address=172.126.0.3:6379,slaves=2,sentinels=3
  ```

## redis 集群原主节点重新上线

**master-node 节点重新上线**

```sh
$docker-compose -f ./redis/docker-compose.yml start master-node
```

**查看一下 redis 集群状态**

```sh
# 现在角色变为从节点了
$docker-compose -f ./redis/docker-compose.yml exec master-node redis-cli -a redis_pwd info replication
Warning: Using a password with '-a' or '-u' option on the command line interface may not be safe.
# Replication
role:slave
master_host:172.126.0.3
master_port:6379
```

**查看一下 sentinel 集群日志**

```log
sentinel-sentinel-2-1  | 1:X 23 Jun 2022 03:13:41.299 # -sdown slave 172.126.0.1:6379 172.126.0.1 6379 @ mymaster 172.126.0.3 6379
sentinel-sentinel-1-1  | 1:X 23 Jun 2022 03:13:41.680 # -sdown slave 172.126.0.1:6379 172.126.0.1 6379 @ mymaster 172.126.0.3 6379
sentinel-sentinel-3-1  | 1:X 23 Jun 2022 03:13:41.717 # -sdown slave 172.126.0.1:6379 172.126.0.1 6379 @ mymaster 172.126.0.3 6379

##### 原来的主节点被修改为从节点了
sentinel-sentinel-2-1  | 1:X 23 Jun 2022 03:13:51.265 * +convert-to-slave slave 172.126.0.1:6379 172.126.0.1 6379 @ mymaster 172.126.0.3 6379
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
