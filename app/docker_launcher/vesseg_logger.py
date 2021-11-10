#!/usr/bin/env python3

import json
import datetime
from typing import Union
from pathlib import Path

# write to dir / db
# print beautifully ? 

class VessegLogger:

    LOG = {
        'timestamp': None, 
        'log_type': None, 
        'message': None
    }
    LOG_TYPES = ['info', 'status', 'error']

    def __init__(self, flush=True, save_logs=False):
        self.flush = flush
        self.save_logs = save_logs
        self.log = VessegLogger.LOG

    def update_log(self, new_log: dict) -> None:
        for k, v in new_log.items():
            self.log[k]=v

    def p(self, **kwargs) -> None:
        log = self.log.copy()
        log['timestamp'] = str(datetime.datetime.now())
        for k,v in kwargs.items():
            if k in log:
                log[k] = v
            else:
                raise TypeError(f'p() got an unexpected keyword argument {k}')
        
        print(json.dumps(log), flush=self.flush)
    
        if self.save_logs:
            pass
        
        return log

    
    def d2p(self, log_string: Union[str, bytes], **kwargs) -> None: 
        if isinstance(log_string, bytes):
            log_string = log_string.decode('utf-8')
        for s in log_string.split('\n'):
            if s!='':
                s = s.strip().replace('\'','"')
                try:
                    return self.p(**json.loads(s))            
                except Exception as e:
                    return self.p(log_type='pure', message=s)
    


