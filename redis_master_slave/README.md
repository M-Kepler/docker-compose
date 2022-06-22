- [参考资料](#参考资料)
- [部署](#部署)
- [Redis 主从模式](#redis-主从模式)
- [测试一下](#测试一下)

# 参考资料

[【Redis】docker compose 部署主从复制](https://juejin.cn/post/6997804248457019399)

不知道，是不是为了政治正确，好多带 slave 的命令都换了名称。。。比如：`replicaof` 是新版本的命令，旧版本是 `slaveof` 命令

# 部署

`etc/redis.conf` 中修改的地方都用 `XXX modify by hjj` 标记出来了

# Redis 主从模式

# 测试一下

- 启动服务

  ```sh
  docker-compose up -d
  ```

- 连接 master 节点，写入数据

  ```sh
  docker-compose exec master sh

  redis-cli set name huangjinjie
  ```

- 连接 slave 节点，读取数据，验证是否主从同步了

  ```sh
  docker-compose exec slave1 sh

  redis-cli get name
  ```
