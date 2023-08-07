from typing import List
from multiprocessing import Queue, Process
import time
from sender import Sender
from phone_parser import AvitoPhoneParser
from url_parser import AvitoUrlParser
from models import ParamParse, ParamSend, ListProcess
from threading import Thread
from multiprocessing import Manager as ManagerMult
from datetime import datetime, timedelta

class Manager():

    def __init__(self, url_list:List[str] = []) -> None:
        self.url_list = url_list
        self.timesleep_check_count_queues = 60
        self.timesleep_add_urllist_queue = self.timesleep_check_count_queues
        self.counter_processes = 0
        self.default_wait_check_queue = 10
        self.queue_checker_id = Queue()
        self.manager = ManagerMult()

        self.phone_parser_list = []
        self.phone_parser_queue = Queue()
        self.phone_file_log = 'PHONE'
        self.maxsize_queue_phone = 50
        self.max_process_phone = 2

        self.url_parser_list = []
        self.url_parser_queue = Queue()
        self.url_file_log = 'URL'
        self.maxsize_queue_url = 10
        self.max_process_url = 2

        self.swich_day_time_event = self.manager.Event()
        if self.pause_work() == 0: self.swich_day_time_event.set()
        else: self.swich_day_time_event.clear()
        self.send_queue = Queue()
        self.sender = Process(target = self._start_process, args=(Sender,
                                                                  self.send_queue,
                                                                  self.phone_parser_queue,
                                                                  self.url_list,
                                                                  self.swich_day_time_event,
                                                                  self.default_wait_check_queue,
                                                                  'SENDER',
                                                                  ParamSend.telegram))
    
    def manage(self):
        def add_url_list(queue_post:Queue, queue_get:Queue, url_list: List[str]):
            url_id_dict = self.manager.dict({url:[] for url in url_list})
            while True:
                for url in url_list:
                    queue_post.put([url, url_id_dict])
                time.sleep(self.timesleep_add_urllist_queue)

        self.sender.start()
        self.counter_processes += 1

        url_adder = Thread(target=add_url_list, args=(self.url_parser_queue, self.queue_checker_id , self.url_list))
        url_adder.start()

        while True:
            self._save_object_in_list(ParamParse.url)
            self._save_object_in_list(ParamParse.phone)
            time.sleep(self.timesleep_check_count_queues)
    
    def _start_process(self, target_class, *args):
        target_class(*args).start()

    def _save_object_in_list(self, param:str):

        if param == ParamParse.url:
            process_count = self.url_parser_queue.qsize() // self.maxsize_queue_url + 1
            if process_count > self.max_process_url:
                process_count = self.max_process_url
            if process_count == len(self.url_parser_list):
                return
            if process_count > len(self.url_parser_list):
                for _ in range(process_count - len(self.url_parser_list)):
                    kill_event = self.manager.Event()
                    process = Process(target = self._start_process,
                                      name=f'PROCESS - {self.counter_processes}',
                                      args = (AvitoUrlParser,
                                              kill_event,
                                              self.url_parser_queue,
                                              self.phone_parser_queue,
                                              self.queue_checker_id,
                                              self.url_file_log,
                                              f'PROCESS - {self.counter_processes}',
                                              self.default_wait_check_queue))
                    self.url_parser_list.append({ListProcess.killer: kill_event, ListProcess.process: process})
                    self.url_parser_list[-1][ListProcess.process].start()
                    self.counter_processes += 1
            else:
                for _ in range(len(self.url_parser_list) - process_count):
                    print(f"Kill process {self.url_parser_list[0][ListProcess.process].name}")
                    self.url_parser_list.pop(0)[ListProcess.killer].set()
                    
        
        if param == ParamParse.phone:
            process_count = 0
            if self.pause_work() == 0:
                process_count = self.phone_parser_queue.qsize() // self.maxsize_queue_phone + 1
                self.swich_day_time_event.set()
            else:
                self.swich_day_time_event.clear()
            if process_count > self.max_process_phone:
                process_count = self.max_process_phone
            if process_count == len(self.phone_parser_list):
                return
            if process_count > len(self.phone_parser_list):
                for _ in range(process_count - len(self.phone_parser_list)):
                    kill_event = self.manager.Event()
                    process = Process(target = self._start_process,
                                      name=f'PROCESS - {self.counter_processes}',
                                      args = (AvitoPhoneParser,
                                              kill_event,
                                              self.phone_parser_queue,
                                              self.send_queue,
                                              self.phone_file_log,
                                              f'PROCESS - {self.counter_processes}',
                                              self.default_wait_check_queue))
                    self.phone_parser_list.append({ListProcess.killer: kill_event, ListProcess.process: process})
                    self.phone_parser_list[-1][ListProcess.process].start()
                    self.counter_processes += 1
            else:
                for _ in range(len(self.phone_parser_list) - process_count):
                    print(f"Kill process {self.url_parser_list[0][ListProcess.process].name}")
                    self.phone_parser_list.pop(0)[ListProcess.killer].set()

    def pause_work(self) -> int:

        def is_weekend(day:datetime = datetime.now()) -> bool:
            if day.month == 1:
                january_weekends = [1, 2, 3, 4, 5, 6, 7, 8]
                if day.day in january_weekends:
                    return True
            if day.month == 12:
                if day.day == 31:
                    return True
            if day.month == 5:
                if day.day == 9:
                    return True
            return datetime.weekday(day) == 6
        
        now = datetime.now()
        sleep = 0
        if is_weekend(now):
            start_hour = 11
            start_minute = 0
            end = 19
        else:
            start_hour = 10
            start_minute = 30
            end = 21
        if now.hour >= end:
            tomorrow = now + timedelta(days=1)
            tomorrow_specific = datetime(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day, hour=start_hour, minute=start_minute, second=0, microsecond=0)
            sleep = tomorrow_specific - now
        elif (now.hour < start_hour) or (now.hour == start_hour and now.minute < start_minute):
            now_specific = datetime(year=now.year, month=now.month, day=now.day, hour=start_hour, minute=start_minute, second=0, microsecond=0)
            sleep = now_specific - now
        # self.logger.info(f'pause {sleep}')
        if sleep == 0:
            return sleep
        return sleep.total_seconds()   