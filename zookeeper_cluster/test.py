# -*-coding:utf-8-*-

"""
Author       : M_Kepler
EMail        : m_kepler@foxmail.com
Last modified: 2022-07-05 22:48:35
Filename     : test.py
Description  : kazoo
"""

from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError
from contextlib import contextmanager


class Config:
    # 网络已经在 docker_compose.yml 中规划好了
    ZK_NODES = [
        "172.100.0.101:2181",
        "172.100.0.102:2181",
        "172.100.0.103:2181"
    ]


@contextmanager
def zk_session_scope():
    zkCli = KazooClient(hosts=Config.ZK_NODES)
    zkCli.start()
    yield zkCli
    zkCli.stop()


class ZKClient(object):
    def __init__(self, zk):
        self._zk = zk

    def create_znode(self, path, value=b'', ephemeral=False,
                     sequence=False, makepath=False):
        """
        创建 znode

        path      节点目录路径
        value     节点的值
        sequence  是否是有序节点
        ephemeral 是否是临时节点
        makepath  递归创建，如果不加上中间那一段，就是建立一个空的节点
        """
        try:
            self._zk.create(path, value, ephemeral, sequence, makepath)
        except NodeExistsError:
            print("path: %s already exists." % path)

    def update_znode(self, path, value):
        """
        更新节点的值

        空节点的值不能用 set 修改，否则执行报错！

        :param path 节点路径
        :param value 节点的值
        """

        self._zk.set(path, value)

    def get_znode(self, path, watcher):
        """
        查询节点

        :param path    节点路径
        :param watcher 监视器（回调）
        """
        node = self._zk.get_children(path, watch=watcher)
        print(node)

    def delete_znode(self, path, recursive=False):
        """
        删除节点

        :param path      节点路径
        :param recursive 是否递归删除所有子节点
        """

        self._zk.delete(path, recursive)

    def clear_all(self):
        nodes = self._zk.get_children("/")
        for node in nodes:
            if node != "zookeeper":
                print(node)
                self._zk.delete("/%s" % node, recursive=True)


if __name__ == "__main__":
    def get_watcher(event):
        """
        zookeeper 所有读操作都有设置 watch 选项

        get_children()
        get()
        exists()
        """
        print("get 事件触发器: %s" % str(event))

    with zk_session_scope() as session:
        api = ZKClient(session)
        node_path = "/huangjinjie"
        node_value = b"111111111111"
        api.create_znode(node_path, node_value)
        # 第一次没有触发
        session.get(node_path, get_watcher)
        api.update_znode(node_path, b"2222222222")
        # 数据有更新后再次获取，才触发
        session.get(node_path, get_watcher)
