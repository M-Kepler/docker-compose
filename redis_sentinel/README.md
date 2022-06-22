- [参考资料](#参考资料)
- [Redis 一主二从三哨兵](#redis-一主二从三哨兵)
- [测试一下](#测试一下)

# 参考资料

[使用Docker-Compose搭建高可用redis哨兵集群](https://cloud.tencent.com/developer/article/1615281)

# Redis 一主二从三哨兵

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

# 测试一下

- 进入 master 容器，确认两个 slave 已经连接

  ```sh
  $cd ./redis
  $docker-compose exec master-node redis-cli -a redis_pwd info replication

  Warning: Using a password with '-a' or '-u' option on the command line interface may not be safe.

  # Replication

  # 可以看到从库状态
  role:master
  connected_slaves:2
  slave0:ip=172.20.0.4,port=6379,state=online,offset=742,lag=0
  slave1:ip=172.20.0.3,port=6379,state=online,offset=756,lag=0

  master_failover_state:no-failover

  # 主从同步所用的 id 和 offset
  master_replid:f7ae6a5e397be90c9f55130e2bacaf7620c06fd2
  master_replid2:de6d7efc618ee9fbe655515052a3827f4165ea26
  master_repl_offset:756
  second_repl_offset:407

  repl_backlog_active:1
  repl_backlog_size:1048576
  repl_backlog_first_byte_offset:407
  repl_backlog_histlen:350

  ```

- 进入 sentinel 容器，检查集群状态（命令和看 redis 集群一样）

  ```sh
  $cd ./sentinel
  $docker-compose exec master-node redis-cli -a redis_pwd info replication

  # Replication
  role:master
  connected_slaves:2
  slave0:ip=172.22.0.4,port=6379,state=online,offset=826,lag=0
  slave1:ip=172.22.0.2,port=6379,state=online,offset=826,lag=0

  master_failover_state:no-failover

  master_replid:6894325e58c6f9764b74d15414768e9ef06749f4
  master_replid2:321c00de0bdf3873a745bfa201325d8b1b8e7b17
  master_repl_offset:826
  second_repl_offset:99

  repl_backlog_active:1
  repl_backlog_size:1048576
  repl_backlog_first_byte_offset:99
  repl_backlog_histlen:728

  ```
