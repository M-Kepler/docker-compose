- [参考资料](#参考资料)
- [测试一下](#测试一下)

## 参考资料

[Redis 安装部署](https://baiyp.ren/Redis%E5%AE%89%E8%A3%85%E9%83%A8%E7%BD%B2.html)

[Redis 集群环境搭建实践](https://www.cnblogs.com/hueyxu/p/13884800.html)

- `redis.conf.default` 是官方的默认配置文件，基于此进行修改，放置在 `./etc/redis/rdis.conf`，所有节点都共用一份配置；上面的修改点都标记了 `===== modify by hjj =====`

- 依赖的镜像也修改了，用 `redis:alpine` 也行

    ```yaml
    # 由
            image: redis
    # 修改为
            image: redis:alpine
    ```

- 其中的挂载关系修改了

    ```yml
    # 由：
        volumes:
            - "/tmp/etc/redis/redis.conf:/etc/redis/redis.conf"
            - "/tmp/data/redis/node1:/data"
    # 修改为：
        volumes:
            - "./etc/redis/:/etc/redis/"
            - "./data/redis/node5:/data"
    ```

- 如果出现 `ERROR: Pool overlaps with other one on this address space` 说明有网络已经占用了 `172.118.0.0/16` 网段，要么修改 `docker-compose.yml` 中的 `networks` 网络配置，要么删掉已有的网络

    ```sh
    # 列出现有网络
    docker network ls

    # 看下是那个网络占用
    docker inspect network [network_id/network_name]

    # 删掉这个网络
    docker network rm [network_id/network_name]
    ```

## 测试一下

```sh
# 进入其中一个容器
docker exec -it redis01 sh

# 创建集群
redis-cli --cluster create redis01:6379 redis02:6379 redis03:6379 redis04:6379 redis05:6379 redis06:6379 --cluster-replicas 1

# 输出一堆提示信息，说明节点的角色，以各个主节点的哈希槽范围

# 三主三从的模式
[172.118.0.2]     master1
[172.118.0.3]     master2
[172.118.0.4]     master3
[172.118.0.5]     slave of master3
[172.118.0.6]     slave of master1
[172.118.0.7]     slave of master2
```

**检查状态**

```sh
172.118.0.2:6379> cluster info
cluster_state:ok            ##### 上线状态i
cluster_slots_assigned:16384
cluster_slots_ok:16384
cluster_slots_pfail:0
cluster_slots_fail:0
cluster_known_nodes:6
cluster_size:3
cluster_current_epoch:6
cluster_my_epoch:1
cluster_stats_messages_ping_sent:877
cluster_stats_messages_pong_sent:854
cluster_stats_messages_sent:1731
cluster_stats_messages_ping_received:849
cluster_stats_messages_pong_received:877
cluster_stats_messages_meet_received:5
cluster_stats_messages_received:1731
total_cluster_links_buffer_limit_exceeded:0

#### 可以看到这几个主节点的哈希槽范围以及节点间关系
172.118.0.2:6379> cluster nodes
f0e291165832a29dd6ff113a25df004bc15f45c7 172.118.0.4:6379@16379 master - 0 1655831937596 3 connected 10923-16383
1be50b3a5c8b2b0ff5c4e3fb85d84221805d5cba 172.118.0.3:6379@16379 master - 0 1655831938098 2 connected 5461-10922
0fafb97647be4cdc0849762d36b262638b7e5880 172.118.0.2:6379@16379 myself,master - 0 1655831936000 1 connected 0-5460

bad2eb7254afe485348d64b666e1c3beea72c6d6 172.118.0.6:6379@16379 slave 0fafb97647be4cdc0849762d36b262638b7e5880 0 1655831936000 1 connected
2b3a74e38b81be3c3cbc252c2946d0d75b2cede4 172.118.0.7:6379@16379 slave 1be50b3a5c8b2b0ff5c4e3fb85d84221805d5cba 0 1655831937093 2 connected
fe974e7d882cc83e919a2cab273bbd08158751cb 172.118.0.5:6379@16379 slave f0e291165832a29dd6ff113a25df004bc15f45c7 0 1655831937000 3 connected

```

Redis 集群通过分片 (sharding) 的方式保存数据库的键值对，整个数据库被分为 16384 个槽(slot)，数据库每个键都属于这 16384 个槽的一个，集群中的每个节点都可以处理 0 个或者最多 16384 个 slot。

槽是数据管理和迁移的基本单位。当数据库中的 16384 个槽都分配了节点时，集群处于上线状态（ok）；如果有任意一个槽没有分配节点，则集群处于下线状态（fail）。

接收命令的节点会计算出命令要处理的键属于哪个槽，并检查这个槽是否指派给自己。

如果键所在的 slot 刚好指派给了当前节点，会直接执行这个命令。否则，节点向客户端返回 MOVED 错误，指引客户端转向 redirect 至正确的节点，并再次发送此前的命令。

```sh
# 从上面可以看到 5798 是在主节点 172.118.0.3 上
172.118.0.2:6379> set name huangjinjie
MOVED 5798 172.118.0.3:6379
OK
```

当我们将命令通过客户端发送给一个从节点时，命令会被重定向至对应的主节点。

```
172.118.0.7:6379> get name
MOVED 5798 172.118.0.3:6379
huangjinjie
172.118.0.7:6379>
```
