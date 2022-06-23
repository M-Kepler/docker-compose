- [参考资料](#参考资料)
- [部署](#部署)
- [主从同步过程](#主从同步过程)
- [测试一下](#测试一下)
- [手动切换](#手动切换)

# 参考资料

[【Redis】docker compose 部署主从复制](https://juejin.cn/post/6997804248457019399)

不知道，好多带 slave 的命令都换了名称。。。比如：`replicaof` 是新版本的命令，旧版本是 `slaveof` 命令

# 部署

`etc/redis.conf` 中修改的地方都用 `XXX modify by hjj` 标记出来了

# 主从同步过程

```log
redis-slave-2  | 1:S 23 Jun 2022 03:53:16.918 * Connecting to MASTER master:6379
redis-slave-2  | 1:S 23 Jun 2022 03:53:16.919 * MASTER <-> REPLICA sync started
redis-slave-2  | 1:S 23 Jun 2022 03:53:16.919 * Non blocking connect for SYNC fired the event.
redis-slave-2  | 1:S 23 Jun 2022 03:53:16.920 * Master replied to PING, replication can continue...
############### 尝试增量同步 ############### 
redis-slave-2  | 1:S 23 Jun 2022 03:53:16.920 * Trying a partial resynchronization (request f0ec31572aba5136a6248f7a5a56f79fd08307a6:17084).
redis-master   | 1:M 23 Jun 2022 03:53:16.921 * Replica 172.125.0.3:6379 asks for synchronization

############### id 不一样，拒绝增量同步，需要全量同步 ###############
redis-master   | 1:M 23 Jun 2022 03:53:16.921 * Partial resynchronization not accepted: Replication ID mismatch (Replica asked for 'f0ec31572aba5136a6248f7a5a56f79fd08307a6', my replication IDs are '12b99900a4b4394725f11a9fdf7ef1dc7d0c1528' and '08242fdd3ce179fa6048ff8c2e32696f08cb25ad')

############### bgsave 生成 rdb 文件 ###############
redis-master   | 1:M 23 Jun 2022 03:53:16.921 * Starting BGSAVE for SYNC with target: disk
redis-master   | 1:M 23 Jun 2022 03:53:16.921 * Background saving started by pid 21

############### 全量同步 ############### 
redis-slave-2  | 1:S 23 Jun 2022 03:53:16.922 * Full resync from master: 12b99900a4b4394725f11a9fdf7ef1dc7d0c1528:16607
redis-master   | 21:C 23 Jun 2022 03:53:16.963 * DB saved on disk
redis-master   | 21:C 23 Jun 2022 03:53:16.964 * Fork CoW for RDB: current 0 MB, peak 0 MB, average 0 MB

redis-slave-2  | 1:S 23 Jun 2022 03:53:17.028 * MASTER <-> REPLICA sync: receiving 215 bytes from master to disk
redis-master   | 1:M 23 Jun 2022 03:53:17.028 * Background saving terminated with success

############### 丢弃原有数据，用全量同步过来的数据 ###############
redis-slave-2  | 1:S 23 Jun 2022 03:53:17.029 * Discarding previously cached master state.
redis-slave-2  | 1:S 23 Jun 2022 03:53:17.029 * MASTER <-> REPLICA sync: Flushing old data
redis-slave-2  | 1:S 23 Jun 2022 03:53:17.029 * MASTER <-> REPLICA sync: Loading DB in memory
redis-master   | 1:M 23 Jun 2022 03:53:17.029 * Synchronization with replica 172.125.0.3:6379 succeeded
redis-slave-2  | 1:S 23 Jun 2022 03:53:17.054 * Loading RDB produced by version 7.0.2
redis-slave-2  | 1:S 23 Jun 2022 03:53:17.054 * RDB age 1 seconds
redis-slave-2  | 1:S 23 Jun 2022 03:53:17.054 * RDB memory usage when created 0.95 Mb
redis-slave-2  | 1:S 23 Jun 2022 03:53:17.054 * Done loading RDB, keys loaded: 2, keys expired: 0.
redis-slave-2  | 1:S 23 Jun 2022 03:53:17.054 * MASTER <-> REPLICA sync: Finished with success
```

# 测试一下

- 启动服务

  ```sh
  docker-compose up -d
  ```

- 看一下集群状态

  ```sh
  docker-compose exec master redis-cli info replication

  # 节点从属关系
  role:master
  connected_slaves:2
  slave0:ip=172.125.0.3,port=6379,state=online,offset=16271,lag=0
  slave1:ip=172.125.0.2,port=6379,state=online,offset=16271,lag=0

  master_failover_state:no-failover
  master_replid:c558d981438683769621ca10f9db53efb558b91e
  master_replid2:d37eeb8c4082c95d7e91d5aafbc6343a47180333
  master_repl_offset:16271
  second_repl_offset:15936
  repl_backlog_active:1
  repl_backlog_size:1048576
  repl_backlog_first_byte_offset:15936
  repl_backlog_histlen:336
  ```

- 连接 master 节点，写入数据

  ```sh
  docker-compose exec master sh

  redis-cli set name huangjinjie
  ```

- 连接 slave 节点，读取数据，验证是否主从同步了

  ```sh
  docker-compose exec slave1 redis-cli get name

  # 主库读写，从库只读
  127.0.0.1:6379> set name2 ddddd
  (error) READONLY You can't write against a read only replica.
  ```

- 单纯的主从是不具备故障切换能力的，把主节点下线后，整个集群就无法继续提供写服务了

  ```sh
  # 主节点下线
  docker-compose stop master

  # 查看从节点日志
  docker-compose logs slave1
  1:S 22 Jun 2022 08:08:33.603 # Unable to connect to MASTER: Invalid argument
  1:S 22 Jun 2022 08:08:34.612 * Connecting to MASTER master:6379
  ```

# 手动切换

修改 slave1 作为主节点，注意从节点的 redis.conf 配置需要注释掉 `bind 127.0.0.1`，允许外部连接

```sh
docker-compose exec slave1 redis-cli slaveof no one
```

修改 slave2 作为 slave1 的从节点

```sh
docker-compose exec slave2 redis-cli slaveof slave1 6379
```

查看一下集群状态

```sh
docker-compose exec slave2 redis-cli info replication

# Replication
role:slave
master_host:slave1  # 已经连接到新的主节点 slave1
master_port:6379
master_link_status:up
master_last_io_seconds_ago:1
master_sync_in_progress:0

slave_read_repl_offset:16621
slave_repl_offset:16621
slave_priority:100
slave_read_only:1

replica_announced:1
connected_slaves:0
master_failover_state:no-failover
master_replid:f0ec31572aba5136a6248f7a5a56f79fd08307a6
master_replid2:08242fdd3ce179fa6048ff8c2e32696f08cb25ad
master_repl_offset:16621
second_repl_offset:16608
repl_backlog_active:1
repl_backlog_size:1048576
repl_backlog_first_byte_offset:16594
repl_backlog_histlen:28

```
