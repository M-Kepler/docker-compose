- [参考资料](#参考资料)
- [搭建部署：三主三从](#搭建部署三主三从)
- [测试一下](#测试一下)
  - [创建集群](#创建集群)
    - [方式一：手动创建](#方式一手动创建)
      - [启动节点](#启动节点)
      - [查看节点信息](#查看节点信息)
      - [`cluster meet [ip] [port]` 节点握手](#cluster-meet-ip-port-节点握手)
      - [`cluster nodes` 查看集群信息](#cluster-nodes-查看集群信息)
      - [`cluster addslots [slot_begin]..[slot_end]` 指派槽](#cluster-addslots-slot_beginslot_end-指派槽)
      - [`cluster replicate [master_node_id]` 设置节点从属关系](#cluster-replicate-master_node_id-设置节点从属关系)
      - [搭建完成，查看集群状态文件按](#搭建完成查看集群状态文件按)
    - [方式二：自动创建](#方式二自动创建)
      - [启动节点](#启动节点-1)
      - [创建集群](#创建集群-1)
      - [检查状态](#检查状态)
      - [查看集群信息](#查看集群信息)
      - [查看哈希槽详细信息](#查看哈希槽详细信息)
  - [操作集群](#操作集群)
  - [故障转移](#故障转移)
  - [集群伸缩](#集群伸缩)
    - [`--cluster add-node [ip]:[port] [ip]:[port]` 新增一个节点](#--cluster-add-node-ipport-ipport-新增一个节点)
    - [`--cluster reshard` 哈希槽重新分配](#--cluster-reshard-哈希槽重新分配)
    - [`--cluster del-node` 删除一个节点](#--cluster-del-node-删除一个节点)

# 参考资料

[Redis 安装部署](https://baiyp.ren/Redis%E5%AE%89%E8%A3%85%E9%83%A8%E7%BD%B2.html)

[★ Redis 集群环境搭建实践](https://www.cnblogs.com/hueyxu/p/13884800.html)

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

# 搭建部署：三主三从

`backup_run_with_config_file` 目录下是指定配置文件来启动；

`./docker-compose.yml` 是通过 redis 命令行启动参数来启动，两者都可以，用命令行启动方式可以更清晰看到修改了哪些配置

# 测试一下

## 创建集群

**地址规划**

```sh
# 三主三从的模式
redis01    [172.118.0.2]    master1
redis02    [172.118.0.3]    master2
redis03    [172.118.0.4]    master3
redis04    [172.118.0.5]    slave of master3
redis05    [172.118.0.6]    slave of master1
redis06    [172.118.0.7]    slave of master2
```

### 方式一：手动创建

#### 启动节点

```
docker-compose up -d
```

#### 查看节点信息

此时还都是各自为战，每个节点都是主节点

```sh
docker exec -it redis01 redis-cli cluster nodes
c42e8c842fac82493c3ca469f585ca6a484c678c :6379@16379 myself,master - 0 0 0 connected

docker exec -it redis02 redis-cli cluster nodes
ed909c42b9443a3d334aba90a69649a84afdf8ca :6379@16379 myself,master - 0 0 0 connected

docker exec -it redis03 redis-cli cluster nodes
c8d340dabe58411f390c9185368105159652a177 :6379@16379 myself,master - 0 0 0 connected

docker exec -it redis04 redis-cli cluster nodes
6ca15939c24cf69f48d3e58a983d3406d65d5d07 :6379@16379 myself,master - 0 0 0 connected

docker exec -it redis05 redis-cli cluster nodes
4240bb90ea25b8d38f457240820aa52dcca7d01d :6379@16379 myself,master - 0 0 0 connected

docker exec -it redis06 redis-cli cluster nodes
f0ca6a906f739b28a5a92677db38e57a73e63289 :6379@16379 myself,master - 0 0 0 connected
```

#### `cluster meet [ip] [port]` 节点握手

将各个独立的节点连接起来，构成一个包含多个节点的集群，【随便一个节点】使用 `CLUSTER MEET <ip> <port>` 命令与其他节点相连即可；

```sh
# 进入其中一个节点，用 cluster meet 命令与其他节点
docker exec -it redis01 redis-cli cluster meet 172.118.0.3 6379
OK

docker exec -it redis01 redis-cli cluster meet 172.118.0.4 6379
OK

docker exec -it redis01 redis-cli cluster meet 172.118.0.5 6379
OK

docker exec -it redis01 redis-cli cluster meet 172.118.0.6 6379
OK

docker exec -it redis01 redis-cli cluster meet 172.118.0.7 6379
OK
```

#### `cluster nodes` 查看集群信息

虽然发现了其他节点，但还没配置主从关系，还是各自为战

```sh
$docker exec -it redis06 redis-cli cluster nodes

c42e8c842fac82493c3ca469f585ca6a484c678c 172.118.0.2:6379@16379 master - 0 1656429709012 1 connected
f0ca6a906f739b28a5a92677db38e57a73e63289 172.118.0.7:6379@16379 myself,master - 0 1656429707000 0 connected
6ca15939c24cf69f48d3e58a983d3406d65d5d07 172.118.0.5:6379@16379 master - 0 1656429708710 3 connected
4240bb90ea25b8d38f457240820aa52dcca7d01d 172.118.0.6:6379@16379 master - 0 1656429708000 4 connected
c8d340dabe58411f390c9185368105159652a177 172.118.0.4:6379@16379 master - 0 1656429707998 2 connected
ed909c42b9443a3d334aba90a69649a84afdf8ca 172.118.0.3:6379@16379 master - 0 1656429708602 5 connected
```

#### `cluster addslots [slot_begin]..[slot_end]` 指派槽

槽是数据管理和迁移的基本单位。当数据库中的 16384 个槽都分配了节点时，集群处于上线状态（ok）；如果有任意一个槽没有分配节点，则集群处于下线状态（fail）

**注意：** 只有主节点有处理槽的能力，如果将槽指派步骤放在主从复制之后，并且将槽位分配给从节点，那么集群将无法正常工作（处于下线状态）

```sh
$docker exec -it redis01 redis-cli cluster addslots {0..5000}
OK

$docker exec -it redis02 redis-cli cluster addslots {5001..10000}
OK

$docker exec -it redis03 redis-cli cluster addslots {10001..16383}
OK
```

#### `cluster replicate [master_node_id]` 设置节点从属关系

```sh
# redis04    [172.118.0.5]    slave of master3
# redis05    [172.118.0.6]    slave of master1
# redis06    [172.118.0.7]    slave of master2

$docker exec -it redis04 redis-cli cluster replicate c8d340dabe58411f390c9185368105159652a177
OK

$docker exec -it redis05 redis-cli cluster replicate c42e8c842fac82493c3ca469f585ca6a484c678c
OK

$docker exec -it redis06 redis-cli cluster replicate ed909c42b9443a3d334aba90a69649a84afdf8ca
OK
```

再看一下节点关系

```sh
$docker exec -it redis06 redis-cli cluster nodes

c42e8c842fac82493c3ca469f585ca6a484c678c 172.118.0.2:6379@16379 master
ed909c42b9443a3d334aba90a69649a84afdf8ca 172.118.0.3:6379@16379 master
c8d340dabe58411f390c9185368105159652a177 172.118.0.4:6379@16379 master

6ca15939c24cf69f48d3e58a983d3406d65d5d07 172.118.0.5:6379@16379 slave c8d340dabe58411f390c9185368105159652a177
4240bb90ea25b8d38f457240820aa52dcca7d01d 172.118.0.6:6379@16379 slave c42e8c842fac82493c3ca469f585ca6a484c678c
f0ca6a906f739b28a5a92677db38e57a73e63289 172.118.0.7:6379@16379 myself,slave ed909c42b9443a3d334aba90a69649a84afdf8ca
```

#### 搭建完成，查看集群状态文件按

`cluster-config-file` 会记录下集群节点的状态

```sh
$docker exec -it redis06 cat nodes.conf

# 结果和 cluster nodes 一样

c42e8c842fac82493c3ca469f585ca6a484c678c 172.118.0.2:6379@16379 master - 0 1656430546547 1 connected 0-5000
ed909c42b9443a3d334aba90a69649a84afdf8ca 172.118.0.3:6379@16379 master - 0 1656430545033 5 connected 5001-10000
c8d340dabe58411f390c9185368105159652a177 172.118.0.4:6379@16379 master - 0 1656430545000 2 connected 10001-16383
6ca15939c24cf69f48d3e58a983d3406d65d5d07 172.118.0.5:6379@16379 slave c8d340dabe58411f390c9185368105159652a177 0 1656430546547 2 connected
4240bb90ea25b8d38f457240820aa52dcca7d01d 172.118.0.6:6379@16379 slave c42e8c842fac82493c3ca469f585ca6a484c678c 0 1656430546039 1 connected
f0ca6a906f739b28a5a92677db38e57a73e63289 172.118.0.7:6379@16379 myself,slave ed909c42b9443a3d334aba90a69649a84afdf8ca 0 1656430545000 5 connected
vars currentEpoch 5 lastVoteEpoch 0
```

### 方式二：自动创建

在 Redis 5.0 之后直接利用 --cluster create 完成

#### 启动节点

```sh
docker-compose up -d
```

#### 创建集群

```sh
# --cluster-replicas 1 代表 一个 master 后有几个 slave，1 代表为 1 个 slave 节点

# 进入其中一个容器， 创建集群
$docker exec -it redis01 redis-cli --cluster create \
    redis01:6379 redis02:6379 redis03:6379 \   # 这几个是主
    redis04:6379 redis05:6379 redis06:6379 \   # 这几个是从
    --cluster-replicas 1

# 输出一堆提示信息，说明节点的角色，以各个主节点的哈希槽范围
```

#### 检查状态

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
```

#### 查看集群信息

可以看到这几个主节点的哈希槽范围以及节点间关系

```sh
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

#### 查看哈希槽详细信息

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

## 操作集群

- Redis 集群通过分片的方式保存数据库的键值对，整个数据库被分为 16384 个槽，数据库每个键都属于这 16384 个槽的一个，集群中的每个节点都可以处理 0 个或者最多 16384 个 槽；

- 槽是数据管理和迁移的基本单位。当数据库中的 16384 个槽都分配了节点时，集群处于上线状态（ok）；如果有任意一个槽没有分配节点，则集群处于下线状态（fail）。

- 接收命令的节点会计算出命令要处理的键属于哪个槽，并检查这个槽是否指派给自己。

- 如果键所在的 slot 刚好指派给了当前节点，会直接执行这个命令。否则，节点向客户端返回 `MOVED` 错误，指引客户端转向 redirect 至正确的节点，并再次发送此前的命令。

```sh
# -c 连接集群结点时使用，此选项可防止 moved 和 ask 异常。
# 否则会收到 (error) MOVED 错误，【不会帮你重定向到对应的节点】
$redis-cli -h 172.118.0.2 -c

# 查看 key 落在哪个哈希槽
172.118.0.2:6379> CLUSTER KEYSLOT name
(integer) 5798

# 从上面可以看到 5798 是在主节点 172.118.0.3 上
# 即当前键命令所请求的键不在当前请求的节点中，则当前节点会向客户端发送一个 Moved 重定向
# 客户端根据 Moved 重定向所包含的内容找到目标节点，再一次发送命令。
# 加了 -c 参数启动的 redis-cli 会帮你重定向到其所在节点上
172.118.0.2:6379> set name huangjinjie
-> Redirected to slot [5798] located at 172.118.0.3:6379
OK
```

当我们将命令通过客户端发送给一个从节点时，命令会被重定向至对应的主节点。

```sh
$redis-cli -h 172.118.0.2  -c

172.118.0.2:6379> get name
# 重定向了
-> Redirected to slot [5798] located at 172.118.0.3:6379
"huangjinjie"
172.118.0.3:6379>

```

## 故障转移

## 集群伸缩

### `--cluster add-node [ip]:[port] [ip]:[port]` 新增一个节点

### `--cluster reshard` 哈希槽重新分配

### `--cluster del-node` 删除一个节点
