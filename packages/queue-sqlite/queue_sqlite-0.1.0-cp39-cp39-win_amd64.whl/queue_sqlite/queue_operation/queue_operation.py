import os
import json
import hashlib
from typing import Tuple, Union, List
import threading
import random
from ..core import core
from ..constant import MessageStatus


class QueueOperation:
    def __init__(self, shard_num: int = 4, queue_name: str = "default"):
        self.shard_num = shard_num
        self.db_dir = os.path.join("cache", queue_name)
        self.shard_connections = threading.local()
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        self.init_shards()

    def _get_shard_index(self, message_id: str) -> int:
        """计算消息的分片索引"""
        hash_obj = hashlib.sha256(message_id.encode())
        return int(hash_obj.hexdigest(), 16) % self.shard_num

    def _get_shard_path(self, shard_index: int) -> str:
        """获取分片数据库路径"""
        return os.path.join(self.db_dir, f"queue_shard_{shard_index}.db")

    def _get_shard_conn(self, shard_index: int) -> core.QueueOperation:
        """获取分片数据库连接（线程安全）"""
        if not hasattr(self.shard_connections, "shards"):
            self.shard_connections.shards = {}

        if shard_index not in self.shard_connections.shards:
            db_path = self._get_shard_path(shard_index)
            conn = core.QueueOperation(db_path)
            self.shard_connections.shards[shard_index] = conn

        return self.shard_connections.shards[shard_index]

    def init_shards(self):
        """初始化分片数据库"""
        for i in range(self.shard_num):
            conn = self._get_shard_conn(i)
            conn.init_db()

    # 入队
    def enqueue(self, message: dict) -> str:
        shard_index = self._get_shard_index(message["id"])
        conn = self._get_shard_conn(shard_index)
        conn.enqueue(message)
        return message["id"]

    def dequeue(self, size: int = 1) -> List[dict]:
        messages = []
        collected = 0

        # 随机轮询分片顺序
        shard_order = list(range(self.shard_num))
        random.shuffle(shard_order)

        for shard_index in shard_order:
            if collected >= size:
                break

            conn = self._get_shard_conn(shard_index)
            shard_messages = conn.dequeue(size - collected)
            messages.extend(shard_messages)
            collected += len(shard_messages)

        return messages

    # 获取队列长度
    def get_queue_length(self) -> int:
        """获取队列中待处理消息的数量

        Returns:
            int: 待处理消息数量
        """
        total = 0
        for i in range(self.shard_num):
            conn = self._get_shard_conn(i)
            total += conn.get_queue_length()
        return total

    # 获取完成/失败的消息
    def get_completed_messages(self) -> List[dict]:
        messages = []
        for i in range(self.shard_num):
            conn = self._get_shard_conn(i)
            messages.extend(conn.get_completed_messages())

        return messages

    # 获取消息结果
    def get_result(self, message_id: str) -> Tuple[bool, Union[str, dict]]:
        conn = self._get_shard_conn(self._get_shard_index(message_id))
        return conn.get_result(message_id)

    # 更新消息状态
    def update_status(self, message_id: str, status: MessageStatus):
        conn = self._get_shard_conn(self._get_shard_index(message_id))
        conn.update_status(message_id, status)

    # 更新消息结果
    def update_result(self, message_id: str, result: str):
        conn = self._get_shard_conn(self._get_shard_index(message_id))
        conn.update_result(message_id, result)

    # 删除消息
    def delete_message(self, message_id: str):
        conn = self._get_shard_conn(self._get_shard_index(message_id))
        conn.delete_message(message_id)

    # 清理7天前的已完成/失败消息
    def clean_old_messages(self, shard_index: int, days: int = 7):
        conn = self._get_shard_conn(shard_index)
        conn.clean_old_messages(days)

    # 清理过期但未处理的消息
    def clean_expired_messages(self, shard_index: int):
        conn = self._get_shard_conn(shard_index)
        conn.clean_expired_messages()
