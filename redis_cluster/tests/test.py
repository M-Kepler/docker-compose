# -*-coding:utf-8-*-

"""
Author       : M_Kepler
EMail        : m_kepler@foxmail.com
Last modified: 2022-06-27 22:44:26
Filename     : test.py
Description  : 用 redis-py 读写 redis 集群

官网: https://redis-py.readthedocs.io/en/stable/commands.html#redis-cluster-commands

# 三主三从的模式
[172.118.0.2]     master1
[172.118.0.3]     master2
[172.118.0.4]     master3
[172.118.0.5]     slave of master3
[172.118.0.6]     slave of master1
[172.118.0.7]     slave of master2
"""

from email.contentmanager import ContentManager
import random
from contextlib import contextmanager
from redis.cluster import RedisCluster
from redis.cluster import ClusterNode


class Config:

    CLUSTER_PWD = ''

    CLUSTER_NODES = [
        ClusterNode("172.118.0.2", 6379),
        ClusterNode("172.118.0.3", 6379),
        ClusterNode("172.118.0.4", 6379),
        ClusterNode("172.118.0.5", 6379),
        ClusterNode("172.118.0.6", 6379),
        ClusterNode("172.118.0.7", 6379)
    ]


@contextmanager
def redis_cluster_scope():
    rc = RedisCluster(
        startup_nodes=Config.CLUSTER_NODES,
        password=Config.CLUSTER_PWD,
        decode_responses=True)
    yield rc
    rc.close()


class RedisClusterContext(object):

    def __init__(self) -> None:
        pass

    def __enter__(self):
        self.rc = RedisCluster(
            startup_nodes=Config.CLUSTER_NODES,
            password=Config.CLUSTER_PWD,
            decode_responses=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rc.close()


class Test():

    def __init__(self, redis_cluster) -> None:
        self.rc = redis_cluster

    def get_cluster_info(self):
        """
        获取集群信息
        """
        print(self.rc.cluster_info())
        print(self.rc.cluster_slots())
        print(self.rc.cluster_nodes())

        exist_key = "exist_key"
        exist_key_slot = self.rc.cluster_keyslot(exist_key)
        print(exist_key_slot)
        print("返回指定键 [%s] 的哈希槽 [%s]，发送到集群中的随机节点" % (exist_key, exist_key_slot))

        print("返回指定哈希槽中的本地键个数 根据指定的 slot_id 发送到节点")
        print(self.rc.cluster_countkeysinslot(exist_key_slot))

        print("返回指定集群槽中的键数")
        print(self.rc.cluster_get_keys_in_slot(exist_key_slot, 5))

    def test_string(self):
        """
        测试设置字符串
        """
        cluster_test_str = "test_str"
        print(self.rc.set(name=cluster_test_str,
                          value='zyooooxie',
                          ex=random.randint(600, 1000)))
        print(self.rc.cluster_keyslot(cluster_test_str))

        print("返回键 %s 的数量" % cluster_test_str)
        print(self.rc.exists(cluster_test_str))

        print("返回键 %s 的类型" % cluster_test_str)
        print(self.rc.type(cluster_test_str))

        print("返回键 %s 的ttl" % cluster_test_str)
        print(self.rc.ttl(cluster_test_str))

        print("设置键 %s 的过期时间" % cluster_test_str)
        print(self.rc.expire(cluster_test_str, 2 * 60 * 60))
        print("返回键 %s 的ttl" % cluster_test_str)
        print(self.rc.ttl(cluster_test_str))

        print("获取键 %s 的值" % cluster_test_str)
        print(self.rc.get(cluster_test_str))

        print("将键名处的值设置为值，并以原子方式返回键名处的旧值。\
            根据 Redis 6.2 GETSET 被视为已弃用。请在新代码中使用 SET 和 GET 参数")
        print(self.rc.getset(cluster_test_str, '新值str'))
        print(self.rc.get(cluster_test_str))

        print("类似 mset,  mget这样的多个key的原生批量操作命令, \
               redis 集群只支持所有 key 落在同一 slot 的情况")
        key1 = 'test1'
        key2 = 'test2'
        print(self.rc.cluster_keyslot(key1))
        print(self.rc.cluster_keyslot(key2))

        # print(self.rc.mset({key1: 'Redis Cluster-{}'.format(key1),
        #   key2: 'Redis Cluster-{}'.format(key2)}))

        # 留意：redis.exceptions.RedisClusterException:
        # MSET - all keys must map to the same key slot

        # print(self.rc.mget(key1, key2))
        # redis.exceptions.RedisClusterException:
        # MGET- all keys must map to the same key slot

        print(self.rc.delete(cluster_test_str, key1, key2))

    def test_hash(self):
        """
        测试哈希值
        """
        cluster_test_hash = 'test_hash'

        print(self.rc.hset(cluster_test_hash, mapping={
              'hash_key': 'hash_value',
              'hash_key1': 'hash_value1',
              'hash_key2': 'hash_value2',
              'hash_key3': 'hash_value3'}))
        print(self.rc.cluster_keyslot(cluster_test_hash))

        print(self.rc.exists(cluster_test_hash))
        print(self.rc.type(cluster_test_hash))

        print(self.rc.ttl(cluster_test_hash))
        print(self.rc.expire(cluster_test_hash, 60 * 60))
        print(self.rc.ttl(cluster_test_hash))

        print(self.rc.hget(cluster_test_hash, 'hash_key'))
        print(self.rc.hget(cluster_test_hash, 'hash_key2222'))

        print(self.rc.hgetall(cluster_test_hash))

        print(self.rc.hexists(cluster_test_hash, 'hash_key'))
        print(self.rc.hexists(cluster_test_hash, 'hash_key2222'))

        print(self.rc.hkeys(cluster_test_hash))
        print(self.rc.hvals(cluster_test_hash))

        print(self.rc.hlen(cluster_test_hash))
        print(self.rc.hdel(cluster_test_hash, 'hash_key2222', 'hash_key'))
        print(self.rc.hlen(cluster_test_hash))

        print(self.rc.hmget(cluster_test_hash, 'hash_key', 'hash_key2'))

        print(self.rc.hmset(cluster_test_hash, {
            'test': 'test1', 'test2': 'test3'}))
        print(self.rc.hgetall(cluster_test_hash))

        print(self.rc.delete(cluster_test_hash))

    def tes_list(self):
        """
        测试列表
        """
        cluster_test_list = 'test_list'
        print(self.rc.rpush(cluster_test_list, 'list1', 'list2', 'list3'))
        print(self.rc.cluster_keyslot(cluster_test_list))

        print(self.rc.type(cluster_test_list))
        print(self.rc.exists(cluster_test_list))

        print(self.rc.ttl(cluster_test_list))
        print(self.rc.expire(cluster_test_list, 5 * 60 * 60))
        print(self.rc.ttl(cluster_test_list))

        print(self.rc.lindex(cluster_test_list, 1))
        print(self.rc.llen(cluster_test_list))

        print(self.rc.lrange(cluster_test_list, 0, -1))
        print(self.rc.lpush(cluster_test_list, 'list0'))
        print(self.rc.lrange(cluster_test_list, 0, -1))

        print(self.rc.linsert(
            cluster_test_list, 'BEFORE', 'list0', 'list0000'))
        print(self.rc.lrange(cluster_test_list, 0, -1))

        print(self.rc.linsert(cluster_test_list, 'AFTER', 'list3', 'list4'))
        print(self.rc.lrange(cluster_test_list, 0, -1))

        print(self.rc.lpop(cluster_test_list))
        print(self.rc.lrange(cluster_test_list, 0, -1))

        print(self.rc.rpop(cluster_test_list))
        print(self.rc.lrange(cluster_test_list, 0, -1))

        print(self.rc.lrem(cluster_test_list, 1, 'list0'))
        print(self.rc.lrange(cluster_test_list, 0, -1))

        print(self.rc.lset(cluster_test_list, 0, 't_list'))
        print(self.rc.lrange(cluster_test_list, 0, -1))

        print(self.rc.delete(cluster_test_list))

    def test_set(self):
        """
        测试集合
        """
        cluster_test_set = 'test_set'
        print(self.rc.sadd(
            cluster_test_set, 'set1', 'set2', 'set3', 'set3', 'set3'))

        print(self.rc.cluster_keyslot(cluster_test_set))

        print(self.rc.type(cluster_test_set))
        print(self.rc.exists(cluster_test_set))

        print(self.rc.ttl(cluster_test_set))
        print(self.rc.expire(cluster_test_set, 4 * 60 * 60))
        print(self.rc.ttl(cluster_test_set))

        print(self.rc.scard(cluster_test_set))
        print(self.rc.smembers(cluster_test_set))

        print(self.rc.sismember(cluster_test_set, 'set0'))
        print(self.rc.sismember(cluster_test_set, 'set2'))

        print(self.rc.srem(cluster_test_set, 'set1'))
        print(self.rc.smembers(cluster_test_set))

        print(self.rc.delete(cluster_test_set))


if __name__ == "__main__":
    with RedisClusterContext() as rc:
        api = Test(rc)
        api.get_cluster_info()
        api.test_string()
        api.test_hash()
        api.test_set()
