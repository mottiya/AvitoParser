from tor_parser import TorParser
from multiprocessing import Queue
from threading import Event
from queue import Empty
import logging
import time
from models import AvitoExceptionLink, AvitoExceptionIP, AvitoExceptionOther, BaseAvitoException, AvitoTimeoutException
from selenium.webdriver.common.by import By
from datetime import datetime

class BaseManager(): # при наследовании добавить поле logger, и переопределить метод actions
    def __init__(self, kill:Event, queue_get: Queue, queue_sender: Queue, file_log: str, name_log:str, wait_check_queue: int) -> None:
        self.kill = kill
        self.queue_get = queue_get
        self.queue_sender = queue_sender
        self.parser = TorParser(kill, name_log)
        self.wait_check_queue = wait_check_queue
        self.current_model = None
        logging.basicConfig(filename=self.parser.settings.HOME_PATH + f'/logs/processes/log_process_{file_log}.log',
                            level=logging.INFO,
                            format='(%(name)s) %(asctime)s %(levelname)s [%(filename)s, %(funcName)s] - %(message)s')

    def start(self):
        self.parser.subscribe_tor(self.subscribe_queue)
    
    def subscribe_queue(self):
        while True:
            if self.kill.is_set():
                self.logger.info(f"DELETE MANAGER")
                return
            if self.queue_get.empty():
                self.logger.info(f'queue is empty, sleep {self.wait_check_queue} sec')
                time.sleep(self.wait_check_queue)
            else:
                self.logger.info(f'queue is not empty, objects in queue {self.queue_get.qsize()}')
                try:
                    self.current_model = self.queue_get.get_nowait()
                except Empty:
                    self.logger.warning(f'FAILED GET, queue is empty')
                    continue
                try:
                    self.action()
                except AvitoExceptionLink:
                    self.logger.info(f'ad removed, id {self.current_model.id}, link {self.current_model.link}')
                except AvitoTimeoutException:
                    self.queue_get.put(self.current_model)
                    self.logger.warning('Timeout in action')
                    self.log_exeptions_pages()
                    raise self.parser.ChangeIPException()
                except AvitoExceptionOther:
                    self.queue_get.put(self.current_model)
                    self.logger.warning('Other exception')
                    self.log_exeptions_pages()
                    raise self.parser.ChangeIPException()
                except BaseAvitoException as err:
                    self.queue_get.put(self.current_model)
                    self.logger.warning('Base exception', exc_info=True)
                    raise self.parser.ChangeIPException()
                except Exception as err:
                    self.queue_get.put(self.current_model)
                    raise err
                finally:
                    self.wait_find = 3
    
    def getUrl_or_raiseAvitoEx(self, url:str) -> None: #raise AvitoException if some problem

        self.parser.get_browser()
        self.logger.info(f'Try Get {url}')
        self.parser.browser.get(url)
        self.logger.info('Get is complete')
        # self.log_exeptions_pages()
        try:
            self.parser.browser.find_element(value='app')
        except:
            self.logger.warning('Access restricted: IP problem')
            raise AvitoExceptionIP('Access restricted: IP problem')
        else:
            try:
                self.parser.browser.find_element(By.XPATH, '//article[@data-marker="not-found"]')
            except:
                try:
                    self.parser.browser.find_element(By.XPATH, '//*[@data-marker="search-container"]')
                except:
                    self.logger.warning('No search container')
                    try:
                        self.parser.browser.find_element(By.XPATH, '//*[@data-marker="item-container"]')
                    except:
                        self.logger.warning('No item container')
                        raise AvitoExceptionOther("Other Avito exception")
            else:
                self.logger.warning('Link not found')
                raise AvitoExceptionLink('Link not valid')

    def log_exeptions_pages(self):
        try:
            with open(f'{self.parser.settings.HOME_PATH}/logs/log_exeptions_pages/page_{datetime.now()}.html','w') as file:
                file.write(self.parser.browser.page_source)
        except:
            self.logger.warning('Except write page in file', exc_info=True)
            # self.logger.info(self.parser.browser.page_source)

    def action(self):
        pass
