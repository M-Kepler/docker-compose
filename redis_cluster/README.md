[Redis 安装部署](https://baiyp.ren/Redis%E5%AE%89%E8%A3%85%E9%83%A8%E7%BD%B2.html)

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

- 如果出现 `ERROR: Pool overlaps with other one on this address space` 说明有网络已经占用了 `172.18.0.0/16` 网段，要么修改 `docker-compose.yml` 中的 `networks` 网络配置，要么删掉已有的网络

    ```sh
    # 列出现有网络
    docker network ls

    # 看下是那个网络占用
    docker inspect network [network_id/network_name]

    # 删掉这个网络
    docker network rm [network_id/network_name]
    ```
