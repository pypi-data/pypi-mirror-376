from ..mounter import TaskMounter
from typing import Callable, List
from ..constant import MessageStatus

class core:
    class QueueOperation:
        def __init__(self, db_path: str):
            ...

        def init_db(self):
            ...

        def enqueue(self, message_dict: dict) -> str:
            ...
        
        def dequeue(self, size: int = 1) -> List[dict]:
            ...

        def get_queue_length(self) -> int:
            ...

        def get_completed_messages(self) -> List[dict]:
            ...

        def get_result(self, message_id: str):
            ...

        def update_status(self, message_id: str, status: MessageStatus):
            ...

        def update_result(self, message_id: str, result: str):
            ...

        def delete_message(self, message_id: str):
            ...

        def clean_old_messages(self, days: int):
            ...

        def clean_expired_messages(self):
            ...
    
    class TaskMounter:
        def __init__(self, task_class: type[TaskMounter]):
            ...
        
        def get_task_list(self) -> List[str]:
            ...

        def get_task_function(self, name: str) -> Callable:
            ...
            