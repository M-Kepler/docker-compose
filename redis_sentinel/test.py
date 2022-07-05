# -*-coding:utf-8-*-

"""
Author       : M_Kepler
EMail        : m_kepler@foxmail.com
Last modified: 2022-06-24 23:55:01
Filename     : read.py
Description  : 测试一下 Redis 哨兵集群模式下的读写操作

官网: https://redis-py.readthedocs.io/en/stable/commands.html#sentinel-commands
"""

from redis.sentinel import Sentinel


class Config:
    MASTER_NAME = "mymaster"
    # REDIS 节点
    REDIS_NODES = [
        ("172.126.0.1", 6379),
        ("172.126.0.2", 6379),
        ("172.126.0.3", 6379)]

    # 哨兵节点
    SENTINEL_NODES = [
        ("172.126.0.4", 26379),
        ("172.126.0.5", 26379),
        ("172.126.0.6", 26379)]

    # 客户端访问密码
    REQUIREPASS = "redis_pwd"

    # 主从同步密码
    MASTERAUTH = "redis_pwd"


sentinel = Sentinel(Config.SENTINEL_NODES, socket_timeout=0.5)

# 得到redis master节点的信息
master = sentinel.discover_master(Config.MASTER_NAME)

print("master node is: ", master)

# 得到redis 所有从节点的信息
slave = sentinel.discover_slaves(Config.MASTER_NAME)
print("slave node is: ", slave)

# 得到主节点连接
master = sentinel.master_for(
    Config.MASTER_NAME,
    socket_timeout=0.5,
    password=Config.REQUIREPASS)

# 主节点写
master.set("name", "huangjinjie")

# 得到从节点连接
slave = sentinel.slave_for(
    Config.MASTER_NAME,
    socket_timeout=0.5,
    password=Config.REQUIREPASS)

# 从节点读
print(slave.get("name"))


# ======================================
# 集群初始状态
# ======================================
# master node is:  ('172.126.0.1', 6379)
# slave node is:  [('172.126.0.3', 6379), ('172.126.0.2', 6379)]
# b'huangjinjie'

# ======================================
# 关闭 master-node 主节点后，主节点变了
# ======================================
# master node is:  ('172.126.0.3', 6379)
# slave node is:  [('172.126.0.2', 6379)]
# b'huangjinjie'

# ======================================
# master-node 主节点重新上线后，原来的主节点变成从节点了
# ======================================
# master node is:  ('172.126.0.3', 6379)
# slave node is:  [('172.126.0.1', 6379), ('172.126.0.2', 6379)]
# b'huangjinjie'
