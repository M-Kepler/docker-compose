- [参考资料](#参考资料)
- [搭建部署：三主三从](#搭建部署三主三从)
- [测试一下](#测试一下)
  - [创建集群](#创建集群)
  - [操作集群](#操作集群)
  - [集群容错](#集群容错)
    - [新增一个节点](#新增一个节点)
    - [删除一个节点](#删除一个节点)

## 参考资料

[Redis 安装部署](https://baiyp.ren/Redis%E5%AE%89%E8%A3%85%E9%83%A8%E7%BD%B2.html)

[Redis 集群环境搭建实践](https://www.cnblogs.com/hueyxu/p/13884800.html)

- 基于 [官方最新配置文件](http://download.redis.io/redis-stable/redis.conf) 进行修改，放置在 `./etc/redis/rdis.conf`，所有节点都共用一份配置；上面的修改点都标记了 `XXX modify by hjj`

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

## 搭建部署：三主三从

`backup_run_with_config_file` 目录下是指定配置文件来启动；

`./docker-compose.yml` 是通过 redis 命令行启动参数来启动，两者都可以，用命令行启动方式可以更清晰看到修改了哪些配置

```
docker-compose up -d

```

## 测试一下

### 创建集群

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
$docker exec -it redis01 redis-cli cluster info

cluster_state:ok                # 上线状态
cluster_slots_assigned:16384    # 哈希槽数量（16384 是个特别的固定值）
cluster_slots_ok:16384
cluster_slots_pfail:0
cluster_slots_fail:0
cluster_known_nodes:6           # 集群中的节点数量
cluster_size:3
cluster_current_epoch:6
cluster_my_epoch:1
                                # cluster_stats_messages_xxx 握手消息zhuagntai
cluster_stats_messages_ping_sent:877
cluster_stats_messages_pong_sent:854
cluster_stats_messages_sent:1731
cluster_stats_messages_ping_received:849
cluster_stats_messages_pong_received:877
cluster_stats_messages_meet_received:5
cluster_stats_messages_received:1731
total_cluster_links_buffer_limit_exceeded:0

#### 可以看到这几个主节点的哈希槽范围以及节点间关系

$docker exec -it redis01 redis-cli cluster nodes

# <id>                节点ID
# <ip:port>           IP:端口
# <flags>
# <master>            角色
# <ping-sent>         发送的握手包
# <pong-recv>         接收的握手包
# <config-epoch>
# <link-state>        连接状态
# <slot>              哈希槽范围
ff640781bdf061bf6a42aca1f8bedb4c6af75d8a 172.118.0.5:6379@16379 slave 396574aa1ca26e7f28af20fcf82db9397b58e46e 0 1656322032000 3 connected

396574aa1ca26e7f28af20fcf82db9397b58e46e 172.118.0.4:6379@16379 master - 0 1656322032744 3 connected 10923-16383
894347def67fa881b9d6c6c411728508999b9ae7 172.118.0.6:6379@16379 slave 63c8c3aac9fdb1541266f886923645e7e2a0f32b 0 1656322033752 1 connected
c002b738c8d67574f79b978a6a45b010257d1d31 172.118.0.3:6379@16379 master - 0 1656322033550 2 connected 5461-10922
dfe9bb6db8f7a8ba98ce933026230771b6426b0c 172.118.0.7:6379@16379 slave c002b738c8d67574f79b978a6a45b010257d1d31 0 1656322033550 2 connected
63c8c3aac9fdb1541266f886923645e7e2a0f32b 172.118.0.2:6379@16379 myself,master - 0 1656322033000 1 connected 0-5460

```

查看哈希槽详细信息

```sh
# 随便进入一个节点
$docker exec -it redis01 redis-cli cluster slots

1) 1) (integer) 0          # 哈希槽范围的开始
   2) (integer) 5460       # 哈希槽范围的结束
   3) 1) "172.118.0.2"     # [主] 节点所在 IP
      2) (integer) 6379    # [主] 节点所监听端口
      3) "d8e95992c73c3d2757ec4098b645aef1771e1196"  # [主] 节点的 ID
      4) (empty array)
   4) 1) "172.118.0.6"     # [从] 节点所在 IP
      2) (integer) 6379    # [从] 节点所监听端口
      3) "06a3c4e71a80f43dd098a0a7f5cc193f31bc236a"  # [从] 节点 ID
      4) (empty array)
2) 1) (integer) 5461
   2) (integer) 10922
   3) 1) "172.118.0.3"
      2) (integer) 6379
      3) "af79929fcca37a43963bc2ef5c9ba234cdee0c24"
      4) (empty array)
   4) 1) "172.118.0.7"
      2) (integer) 6379
      3) "49c25bb6a62392fc171ea38fceeafd2043d26502"
      4) (empty array)
3) 1) (integer) 10923
   2) (integer) 16383
   3) 1) "172.118.0.4"
      2) (integer) 6379
      3) "2093a9e633172d3b478e61c17499c462f2a4e496"
      4) (empty array)
   4) 1) "172.118.0.5"
      2) (integer) 6379
      3) "bbac26e78d63dee030eb3992e06dfbda47456dcb"
      4) (empty array)
```

### 操作集群

Redis 集群通过分片 (sharding) 的方式保存数据库的键值对，整个数据库被分为 16384 个槽(slot)，数据库每个键都属于这 16384 个槽的一个，集群中的每个节点都可以处理 0 个或者最多 16384 个 slot。

槽是数据管理和迁移的基本单位。当数据库中的 16384 个槽都分配了节点时，集群处于上线状态（ok）；如果有任意一个槽没有分配节点，则集群处于下线状态（fail）。

接收命令的节点会计算出命令要处理的键属于哪个槽，并检查这个槽是否指派给自己。

如果键所在的 slot 刚好指派给了当前节点，会直接执行这个命令。否则，节点向客户端返回 MOVED 错误，指引客户端转向 redirect 至正确的节点，并再次发送此前的命令。

```sh
#### 本地 redis-cli 命令要加 -c 参数才是集群模式，否则会收到 (error) MOVED 错误，不会帮你重定向到对应的节点
$redis-cli -c

# 查看 key 落在哪个哈希槽
172.118.0.2:6379> CLUSTER KEYSLOT name
(integer) 5798

# 从上面可以看到 5798 是在主节点 172.118.0.3 上
# 即当前键命令所请求的键不在当前请求的节点中，则当前节点会向客户端发送一个Moved 重定向，客户端根据Moved 重定向所包含的内容找到目标节点，再一次发送命令。
# redis-cli 会帮你重定向到其所在节点上
172.118.0.2:6379> set name huangjinjie
-> Redirected to slot [5798] located at 172.118.0.3:6379
OK
```

当我们将命令通过客户端发送给一个从节点时，命令会被重定向至对应的主节点。

```sh
172.118.0.7:6379> get name
MOVED 5798 172.118.0.3:6379
huangjinjie
172.118.0.7:6379>
```

### 集群容错

#### 新增一个节点

#### 删除一个节点
