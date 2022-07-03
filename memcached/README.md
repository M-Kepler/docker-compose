- [部署](#部署)
- [测试一下](#测试一下)

## 部署

[超简单的 memcached 集群搭建](https://blog.51cto.com/u_11243465/2104364)

repcached 由日本人开发，可以说是 Memcached 的一个 patch, 为了实现 Memcached 的复制功能，可以支持多个 Memcached 之间相互复制，解决了 Memcached 的容灾问题。

Repcached 是一个单 master 单 slave 的方案，它的 master/slave 都是可读写的，而且可以同步，如果 master 挂掉，slave 侦测到连接断了，就会自动 listen 而成为 master，如果 slave 挂掉，master 也会侦测到连接已经断开，并且重新侦听，等待 slave 加入。

```sh
docker-compose up -d
```

## 测试一下

```sh
# 获取容器 IP
CONTAINER_NAME="memcached"
CONTAINER_IP=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $CONTAINER_NAME)

# 连接
$telnet $CONTAINER_IP 11211
Trying 172.18.0.2...
Connected to 172.18.0.2.
Escape character is '^]'.


# 写入数据
set foo 0 0 3
bar
STORED

# 读取数据
get foo
VALUE foo 0 3
bar
END

# 退出
quit
```
