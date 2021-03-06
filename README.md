`docker-compose` 可以很方便地创建一些测试环境，比如 Zookeeper 集群、Kafka 集群、MySQL 主从、Redis 主从、Redis 哨兵、Redis cluster 等等，方便学习。

**安装 docker-compose**

为了避免版本导致的不必要的麻烦，不建议用 `apt` 安装，统一用以下方式安装新版

```sh
# 获取脚本
$ curl -L https://github.com/docker/compose/releases/download/1.25.0-rc2/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose

# 赋予执行权限
$chmod +x /usr/local/bin/docker-compose

# 查看版本
docker-compose -version
# apt 安装的是 1.25 的版本
docker-compose version 1.27.2, build 18f557f9
```

**portainer轻量级 docker 管理界面工具**

如果是通过 TCP 连接服务器上的 docker 服务，需要修改容器服务启动方式，启用 TCP 连接

```sh
# 添加 -H tcp://0.0.0.0
ExecStart=/usr/bin/dockerd -H fd:// -H tcp://0.0.0.0 --containerd=/run/containerd/containerd.sock
```

浏览器访问 http://localhost:9000
