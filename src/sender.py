from multiprocessing import Queue
import logging
import time
from models import ParamSend
from notifiers import get_notifier
import requests
import os
from threading import Event


class Sender():
    def __init__(self, queue: Queue, queue_check_night:Queue, url_list:list, swich_day_time_event:Event, wait_check_queue: int, file_log: str, param_send:ParamSend) -> None:
        logging.basicConfig(filename=os.getcwd() + f'/logs/processes/log_process_{file_log}.log',
                            level=logging.INFO,
                            format='(%(name)s) %(asctime)s %(levelname)s [%(filename)s, %(funcName)s] - %(message)s')
        self.logger = logging.getLogger(f"{file_log}")
        self.queue_get = queue
        self.queue_check_night = queue_check_night
        self.url_list = url_list
        self.swich_day_time_event = swich_day_time_event
        self.wait_check_queue = wait_check_queue
        self.param_send = param_send
        # if self.param_send == ParamSend.telegram:
        self.tgbot = Tgbot()
        if self.param_send == ParamSend.request:
            self.tgbot.ids.append(self.tgbot.ids_admins)
    
    def start(self):
        cur_day_time = self.swich_day_time_event.is_set() # True - day; False - night.
        self.count_send_advert = {url.split('/')[3]:0 for url in self.url_list}
        while True:
            try:
                if cur_day_time != self.swich_day_time_event.is_set():
                    send_stats = ''
                    if cur_day_time:
                        send_stats += 'Обьявлений собрано за день:'
                        for c in self.count_send_advert:
                            send_stats += f'\n{c} : {self.count_send_advert[c]}'
                    else:
                        send_stats += f'{self.queue_check_night.qsize()} обьявлений собрано за ночь, начинаю сбор номеров телефонов:'
                    cur_day_time = self.swich_day_time_event.is_set()
                    for c in self.count_send_advert:
                        self.count_send_advert[c] = 0
                    self.tgbot.send(send_stats)
                if self.queue_get.empty():
                    self.logger.info(f'queue is empty, sleep {self.wait_check_queue} sec')
                    time.sleep(self.wait_check_queue)
                else:
                    self.logger.info(f'queue is not empty, objects in queue {self.queue_get.qsize()}')
                    current_model = self.queue_get.get()
                    index = current_model.link.split('/')[3]
                    for i in self.count_send_advert:
                        if i in index:
                            self.count_send_advert[i] += 1
                            break
                    time.sleep(1)
                    self._send(current_model)
            except:
                self.logger.error('ERROR', exc_info=True)

    def _send(self, model):
        if self.param_send == ParamSend.telegram:
            self.tgbot.send(model.to_json())
        if self.param_send == ParamSend.request:
            self._send_req(model.to_json())

    def _send_req(self, model):
        def try_request(url, json=None) -> requests.Response:
            self.logger.info(str([url, json]))
            for t in range(7):
                response = requests.post(url=url, json=json)
                if response.status_code == 201:
                    return(response)
                self.logger.info(f"sleep {2**t} seconds, status {response.status_code}")
                time.sleep(2**t)
            raise Exception(f"request failed {response.status_code}")
        
        url = 'http://194.87.94.203/api/v1/newadvert/'
        try:
            try_request(url=url, json=model)
        except:
            self.logger.critical(f"REQUEST EXCEPTION, model = {model}", exc_info=True)

class Tgbot:
    def __init__(self) -> None:
        self.token = ''
        self.ids = [] # мой и заказчика
        self.ids_admins = [] #админы
        self.telegram = get_notifier('telegram')
    
    def send(self, message):
        for id in self.ids:
            self.telegram.notify(token=self.token, chat_id=id, message=str(message))

if __name__ == "__main__":
    from threading import Thread
    from models import AdvertModel
    q = Queue()
    q_ch = Queue()
    for i in range(7):
        q_ch.put(0)
    urls = ['https://m.avito.ru/murino/kvartiry/prodam-ASgBAgICAUSSA8YQ?f=ASgBAQICAUSSA8YQAUCQvg0Ulq41&s=104',
            'https://m.avito.ru/kudrovo/kvartiry/prodam-ASgBAgICAUSSA8YQ?f=ASgBAQICAUSSA8YQAUCQvg0Ulq41&s=104',
            'https://m.avito.ru/sankt-peterburg/kvartiry/prodam-ASgBAgICAUSSA8YQ?f=ASgBAQICAUSSA8YQAUCQvg0Ulq41&s=104']
    swich_day_time_event = Event()
    w = 10
    f = 'test_sender'
    p = ParamSend.telegram
    s = Sender(q, q_ch, urls, swich_day_time_event, w, f, p)
    s.tgbot.ids = [746828525]
    print('Начало цикла')
    t = Thread(target=s.start, args=())
    t.start()
    while True:
        inp = input('Введите что угодно для следующего шага')
        if inp == '1':
            swich_day_time_event.set()
        if inp == '0':
            swich_day_time_event.clear()
        q.put(AdvertModel(user_name='user_name',
                          advert_name='advert_name',
                          link='https://m.avito.ru/sankt-peterburg/kvartiry/prodam-ASgBAgICAUSSA8YQ?f=ASgBAQICAUSSA8YQAUCQvg0Ulq41&s=104',
                          id='id',
                          address='address',
                          tel='phone',))