# 新建清理调度器
import threading
import time
from ..queue_operation import QueueOperation


class CleanupScheduler:
    def __init__(self, queue_operation: QueueOperation, interval_minutes=60):
        self.queue_operation = queue_operation
        self.interval = interval_minutes * 60  # 转换为秒
        self.is_running = False
        self.cleanup_thread = None

    def cleanup_expired_messages(self):
        """清理过期消息"""
        while self.is_running:
            try:
                # 清理7天前的已完成/失败消息
                for i in range(self.queue_operation.shard_num):
                    self.queue_operation.clean_old_messages(i, 7)
                    
                # 清理过期但未处理的消息
                for i in range(self.queue_operation.shard_num):
                    self.queue_operation.clean_expired_messages(i)
                    
            except Exception as e:
                print(f"清理消息错误: {str(e)}")
            
            # 休眠等待下次清理
            for _ in range(self.interval):
                if not self.is_running:
                    break
                time.sleep(1)

    def start_cleanup(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.cleanup_thread = threading.Thread(target=self.cleanup_expired_messages, daemon=True)
        self.cleanup_thread.start()

    def stop_cleanup(self):
        if not self.is_running:
            return
        
        self.is_running = False
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=2.0)