from threading import Lock
from datetime import datetime, timedelta
import json
from multiprocessing import Queue
from queue import Empty
from enum import Enum
from typing import List
from multiprocessing import Manager as ManagerMult

class AdvertModel(object):
    def __init__(self,
                 user_name:str = 'User',
                 advert_name:str = '',
                 link:str = '',
                 id:str = '',
                 post_time:datetime = datetime.today(),
                 address:str = '',
                 detailing:str = '',
                 tel:str = '',
                 source = 'BotLeedGen',) -> None:
        
        self.user_name = user_name # auto
        self.advert_name = advert_name # load actions_driver
        self.link = link # load actions_driver
        self.id = id # load actions_driver
        self.post_time = post_time # load actions_driver
        self.address = address # load actions_driver
        self.detailing = detailing #auto null
        self.tel = tel # load put_phone_advertmodel
        self.source = source # auto

    def to_json(self) -> str:
        diction = {
            'user_name' : self.user_name,
            'advert_name': self.advert_name,
            'link': self.link,
            'id_avito':self.id,
            'post_time':self.post_time.strftime("%Y-%m-%d-%H-%M-%S"),
            'address': self.address,
            'detailing': self.detailing,
            'tel': self.tel,
            'source': self.source,
        }
        if not diction['detailing']: diction['detailing'] = 'Empty Detailing'
        return diction


    def set_tel(self, tel:str) -> None:
        self.tel = tel

    def set_detailing(self, datailing:str) -> None:
        self.datailing = datailing

class __Singleton(type):
    _instances = {}
    _lock: Lock = Lock()
    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                  instance = super().__call__(*args, **kwargs)
                  cls._instances[cls] = instance
        return cls._instances[cls]

class LastTimeAdvert(metaclass=__Singleton):
    @staticmethod
    def _get_mounth_list() -> list:
        return ['января',
                'февраля',
                'марта',
                'апреля',
                'мая',
                'июня',
                'июля',
                'августа',
                'сентября',
                'октября',
                'ноября',
                'декабря',]

    def __init__(self,
                 str_avito_time = '',
                 time_epoch = None) -> None:
        self.str_time = str_avito_time
        self.time_epoch = time_epoch
        self.activity = False

    def is_active(self) -> bool: return self.activity
    def get_str_time(self) -> str: return self.str_time
    def get_time_epoch(self) -> datetime: return self.time_epoch
    def set_str_time(self, time:str) -> None:
        self.activity = True
        self.str_time = time
        self.time_epoch = self.s_str_time_to_datetime(time)
    def set_datetime(self, dt:datetime) -> None:
        self.activity = True
        self.time_epoch = dt
        self.str_time = self.s_datetime_to_str_time(dt)

    @staticmethod
    def s_str_time_to_datetime(time_s:str) -> datetime: #str format ('12 апреля, 17:54') ('Сегодня, 17:54') ('Вчера, 17:54')
        mounth_list = LastTimeAdvert._get_mounth_list()
        today = datetime.today().date()
        year = today.year
        month = 0
        day = 0
        hour = 0
        minute = 0
        second = 0
        microsecond = 0
        if 'Сегодня' in time_s:
            month = today.month
            day = today.day
        elif 'Вчера' in time_s:
            month = (today - timedelta(days=1)).month
            day = (today - timedelta(days=1)).day
        else:
            day = int(time_s[0:3])
            for mounth_one in range(len(mounth_list)):
                if mounth_list[mounth_one] in time_s:
                    month = mounth_one+1
                    break
        minute = int(time_s[-2:])
        hour = int(time_s[-5:-3])
        res_datetime = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second, microsecond=microsecond)
        return res_datetime

    @staticmethod
    def s_datetime_to_str_time(time_d:datetime) -> str:
        mounth_list = LastTimeAdvert._get_mounth_list()
        str_time = ''
        if time_d.day == datetime.today().day:
            str_time = 'Сегодня'
        elif time_d.day == (datetime.today() - timedelta(days=1)).day:
            str_time = 'Вчера'
        else:
            str_time += str(time_d.day) + ' ' + mounth_list[time_d.month]
        str_time += ', ' + str(time_d.hour) + ':' 
        if time_d.minute < 10: str_time += '0'
        str_time += str(time_d.minute)
        return str_time

# class LastIdModel():
#     def __init__(self, url: str, id_list: List[str] = []) -> None:
#         self.url = url
#         self.id_list = id_list
    
#     def put_id_list(self, id_list: List[str]) -> None:
#         self.id_list = id_list

#     def append_list(self, id_list: List[str]) -> None:
#         for id in id_list:
#             self.id_list.append(id)

#     def append(self, id_one: str) -> None:
#         self.id_list.append(id_one)
    
#     def __str__(self) -> str:
#         return f'{self.url}, {self.id_list}'

# class LastIdManager():
#     def __init__(self, url_list: List[str]) -> None:
#         self.manager = ManagerMult()
#         self.url_id_dict = self.manager.dict({url: self.manager.list([]) for url in url_list})

# class LastIdManager():
#     def __init__(self, queue:Queue, url_list: List[str]) -> None:
#         self.queue = queue
#         self.url_id_dict = {url: LastIdModel(url) for url in url_list}
    
#     def add(self, list_id_model: LastIdModel) -> None:
#         self.queue.put(list_id_model)
    
#     def _update(self):
#         while not self.queue.empty():
#             try:
#                 model = self.queue.get_nowait()
#                 self.url_id_dict[model.url] = model
#             except Empty:
#                 pass

#     def get(self, url:str) -> LastIdModel:
#         self._update() 
#         return self.url_id_dict[url]

class ParamParse(Enum):
    url = 1
    phone = 2

class ListProcess(Enum):
    killer = 1
    process = 2

class ParamSend(Enum):
    telegram = 1
    request = 2

class BaseAvitoException(Exception):
    pass

class AvitoExceptionIP(BaseAvitoException):
    pass

class AvitoExceptionLink(BaseAvitoException):
    pass

class AvitoExceptionOther(BaseAvitoException):
    pass

class AvitoTimeoutException(BaseAvitoException):
    pass

class AvitoInterruptLimit(BaseAvitoException):
    pass