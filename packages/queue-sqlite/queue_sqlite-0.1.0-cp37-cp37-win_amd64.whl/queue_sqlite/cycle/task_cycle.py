from ..model import MessageItem
from typing import Callable, Optional
from ..constant import MessageStatus
import json

class TaskCycle:
    def __init__(self, message_item: MessageItem, callback: Optional[Callable]):
        self.message_item = message_item
        self.callback = callback
        self.task_result = None
        self.task_status = None
        self.task_error = None

    def run(self):
        try:
            task_result = self.callback(self.message_item) # type: ignore
        except Exception as e:
            self.task_result = None
            self.task_status = MessageStatus.FAILED
            self.task_error = str(e)
        else:
            self.task_result = task_result # type: ignore
            self.task_status = MessageStatus.COMPLETED
            self.task_error = None

    def get_task_result(self):
        if isinstance(self.task_result, (dict, list)):
            try:
                return json.dumps(self.task_result)
            except:
                return json.dumps({'result': str(self.task_result)})     

        elif isinstance(self.task_result, str):
            try:
                json.loads(self.task_result)
                return self.task_result
            except:
                return json.dumps({'result': self.task_result})
        elif isinstance(self.task_result, (int, float, bool)):
            return json.dumps({'result': self.task_result})
        elif self.task_result is None:
            return 'null'
        else:
            return json.dumps({'result': str(self.task_result)})

    def get_task_status(self):
        return self.task_status

    def get_task_error(self):
        return self.task_error
    
    def get_task_message_item(self):
        return self.message_item
    
    def get_task_callback(self):
        return self.callback
    
    
