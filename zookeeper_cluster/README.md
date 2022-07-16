- [参考资料](#参考资料)
- [docker-compose.yml 中的环境变量](#docker-composeyml-中的环境变量)
- [测试一下](#测试一下)
  - [查看节点](#查看节点)
  - [创建节点](#创建节点)
  - [修改节点](#修改节点)
  - [删除节点](#删除节点)
  - [查看和重新执行历史命令](#查看和重新执行历史命令)
  - [连接到其他服务器](#连接到其他服务器)
  - [节点监听](#节点监听)

## 参考资料

[使用 docker 或者 docker-compose 部署 Zookeeper 集群](https://www.cnblogs.com/shanfeng1000/p/14488665.html)

[ZooKeeper 命令行工具 zkCli.sh](https://www.cnblogs.com/f-ck-need-u/p/9232829.html)

![alt](https://images2017.cnblogs.com/blog/546172/201801/546172-20180111225828738-663859686.png)

## docker-compose.yml 中的环境变量

| 变量          | 描述                                         |
| :------------ | :------------------------------------------- |
| `ZOO_MY_ID`   | Zookeeper 节点的 ID                          |
| `ZOO_SERVERS` | Zookeeper 节点列表，多个节点之间使用空格隔开 |

## 测试一下

- 连接集群

  XXX 连接集群和连接单个节点没啥区别啊感觉？获取的信息都一样

  ```sh
  # 加 -server 参数，指定集群地址
  $docker-compose exec zoo2 zkCli.sh -server zoo1:2181,zoo2:2181,zoo3:2181

  [zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 0] get /zookeeper/config
  server.1=zoo1:2888:3888:participant;0.0.0.0:2181
  server.2=zoo2:2888:3888:participant;0.0.0.0:2181
  server.3=zoo3:2888:3888:participant;0.0.0.0:2181
  version=0
  ```

### 查看节点

- `zkServer.sh status` 看一下节点服务角色

  ```sh
  $docker-compose exec zoo1 zkServer.sh status
  ZooKeeper JMX enabled by default
  Using config: /conf/zoo.cfg
  Client port found: 2181. Client address: localhost. Client SSL: false.
  Mode: follower                  ##### 角色

  $docker-compose exec zoo2 zkServer.sh status
  ZooKeeper JMX enabled by default
  Using config: /conf/zoo.cfg
  Client port found: 2181. Client address: localhost. Client SSL: false.
  Mode: follower

  $docker-compose exec zoo3 zkServer.sh status
  ZooKeeper JMX enabled by default
  Using config: /conf/zoo.cfg
  Client port found: 2181. Client address: localhost. Client SSL: false.
  Mode: leader
  ```

- `ls` 看一下目录结构

  `ls -R` 就想 Linux 中的 tree 命令，查看目录树

  ```sh
  # 进入其中一个容器
  # 默认是连接到 localhost:2181
  $docker-compose exec zoo1 zkCli.sh

  # 执行命令查看节点，可以看到三个节点
  [zk: localhost:2181(CONNECTED) 0] get /zookeeper/config
  server.1=zoo1:2888:3888:participant;0.0.0.0:2181
  server.2=zoo2:2888:3888:participant;0.0.0.0:2181
  server.3=zoo3:2888:3888:participant;0.0.0.0:2181
  version=0

  ```

- `stat` 或 `ls -s` 看一下节点zhuagntai

  ```sh
  [zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 2] stat /zk_test
  cZxid = 0x100000010                   # 创建节点的事务 zxid
      # 每次修改 zookeeper 状态都会收到一个 zxid 形式的时间戳, 也就是 zookeeper 事务 ID。
      # 事务 ID 是 zookeeper 中所有修改总的次序。每个修改都有唯一的 zxid, 如果 zxid1 小于 zxid2, 那么 zxid1 在 zxid2 之前发生
  ctime = Tue Jul 05 07:31:15 UTC 2022  # 创建时间
  mZxid = 0x100000010                   # 最后更新的事务 zxid
  mtime = Tue Jul 05 07:31:15 UTC 2022  # 修改时间
  pZxid = 0x100000016                   # 最后更新的子节点
  cversion = 1                          # znode 子节点变化号，znode 子节点修改次数
  dataVersion = 0                       # znode 数据变化号
  aclVersion = 0                        # 访问控制列表变化号
  ephemeralOwner = 0x0                  # 如果是临时节点，这个是 znode 拥有的 session_id，如果不是临时节点，则为 0
  dataLength = 11                       # znode 的数据长度
  ```

### 创建节点

```sh
# create [-s] [-e] path data acl
```

- `create` 普通节点

  ```sh
  # 创建
  [zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 1] create /zk_test huangjinjie
  [zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 2] create /zk_test/test1 value

  # 查看
  [zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 3] get /zk_test
  [zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 4] get /zk_test/test1

  ```

- `create -s` 带序号节点

  ```sh
  # 创建带序列号的 znode
  [zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 1] create -s /test1 aaaaaaaaa
  Created /zk_test10000000002

  # 创建了带序列号的 znode 后，以后只能使用带序列号的路径 /test10000000002 来引用这个 znode，而不能用/test1来引用。
  [zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 2] get /zk_test10000000002
  ```

- `create -e` 创建一个临时 znode

  临时 znode 在会话退出时会自动删除，所以不能在临时节点上创建子节点。另外，虽然临时节点属于某会话，但所有客户端都可以查看、引用它。

  ```sh
  [zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 1] create -e /test2 333
  Created /test2
  ```

### 修改节点

```sh
[zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 13] set /zk_test huangjinjie2
```

### 删除节点

```sh
# delete 可以删除节点。但是它不能递归删除，如要删除的节点下有子节点，则删除失败
[zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 19] delete /zk_test_zoo2

# deleteall 命令可以递归删除节点，所以也会删除节点中的所有子节点。
[zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 22] deleteall /zk_test

```

### 查看和重新执行历史命令

history 命令可以列出最近操作的 10 条命令历史，并给出每个历史命令的编号。redo命令可以根据历史命令的编号重新调用这些命令。

- 查看历史命令

  ```sh
  [zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 27] history
  17 - ls -R /zk_test
  18 - ls -R /
  19 - delete /zk_test_zoo2
  20 - rmr /zk_test
  21 - ls -R /zk_test
  22 - deleteall /zk_test
  23 - ls -R /zk_test
  24 - ls -R /
  25 - ?
  26 - ls -R /
  27 - history

  ```

- 再次执行历史命令

  ```sh
  [zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 28] redo 24
  /
  /zk_test10000000002
  /zookeeper
  /zookeeper/config
  /zookeeper/quota

  ```

### 连接到其他服务器

```sh
# 启动，默认连接到 localhost:2181
[root@localhost zookeeper]# docker-compose exec zoo2 zkCli.sh

# 通过 connect 连接到其他服务器
[zk: localhost:2181(CONNECTED) 1] connect zoo1:2181,zoo2:2181,zoo3:2181

# 关闭链接
[zk: localhost:2181(CONNECTED) 2] close

# 关闭后，不会切换回之前的连接，需要手动再连接
[zk: zoo1:2181,zoo2:2181,zoo3:2181(CLOSED) 7]
[zk: zoo1:2181,zoo2:2181,zoo3:2181(CLOSED) 7] connect localhost:2181

```

### 节点监听

节点创建、删除、更新 都会触发监听事件

```sh
# 连接集群
$docker-compose exec zoo2 zkCli.sh -server zoo1:2181,zoo2:2181,zoo3:2181

# 旧的命令是 stat [path] watch
[zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 16] stat /abc watch
'stat path [watch]' has been deprecated. Please use 'stat [-w] path' instead.
Node does not exist: /abc

# 监听 /abc 节点
[zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 17] stat -w /abc
Node does not exist: /abc

# 创建节点，触发 NodeCreated 事件
[zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 18] create /abc 111

WATCHER::

WatchedEvent state:SyncConnected type:NodeCreated path:/abc
Created /abc


# 添加监听事件
[zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 21] get -w /abc
111

# 修改节点，触发 NodeDataChanged 事件
[zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 22] set /abc 222

WATCHER::

WatchedEvent state:SyncConnected type:NodeDataChanged path:/abc


[zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 23] create /hello 333
Created /hello
[zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 24] get -w /hello
333

# 删除节点，触发 NodeDeleted 事件
[zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 25] delete /hello

WATCHER::

WatchedEvent state:SyncConnected type:NodeDeleted path:/hello
[zk: zoo1:2181,zoo2:2181,zoo3:2181(CONNECTED) 26]
```
