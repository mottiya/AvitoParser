from multiprocessing import Queue
from models import AdvertModel
import logging
import time
from models import AvitoInterruptLimit, AvitoTimeoutException, AdvertModel
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from base_parser import BaseManager
from threading import Event

class AvitoPhoneParser(BaseManager):

    def __init__(self, kill:Event, queue_get: Queue, queue_sender: Queue, file_log: str, name_log:str, wait_check_queue: int) -> None:
        super().__init__(kill, queue_get, queue_sender, file_log, name_log, wait_check_queue)
        self.logger = logging.getLogger(f"PP_{name_log}")
        self.interrupt_max = 5
        self.wait_find = 3

    def action(self):
        model = self.current_model
        try:
            complete_advert = self.get_complete_model(model)
        finally:
            self.wait_find = 3
        self.queue_sender.put(complete_advert)

    def get_complete_model(self, model:AdvertModel) -> AdvertModel:
        target_url = model.link
        self.getUrl_or_raiseAvitoEx(target_url)

        wait_max = 12
        interrupt = 0
        while True:
            if self.wait_find > wait_max:
                raise AvitoTimeoutException(f"WAIT > {wait_max} ERROR")
            try:
                phone = self.get_telephone(self.wait_find)
                model.set_tel(phone)
                self.logger.info("SEND ADVERT")
                return model
            except AvitoTimeoutException:
                interrupt += 1
            except TimeoutException:
                self.logger.warning(f'Get telephone TIMEOUT exception, {interrupt}/{self.interrupt_max}, wait {self.wait_find}')
                self.wait_find += 3
            except Exception as err:
                self.logger.warning(f'Get telephone SOME exeption')
                raise err
            if interrupt > self.interrupt_max:
                raise AvitoInterruptLimit("Trying to get a phone, limit exceeded")
            self.getUrl_or_raiseAvitoEx(target_url)


    def get_telephone(self, wait:int) -> str: # or raise Exeption
        button = self.parser.find_by_xpath_waiting(wait, EC.element_to_be_clickable, '//*[@data-marker="item-contact-bar/call"]')
        try:
            time.sleep(2)
            button.click()
            time.sleep(2)
        except:
            self.parser.browser.execute_script("javascript:window.scrollBy(250,350)", button)
            time.sleep(2)
            button.click()
            time.sleep(2)
        try:
            tel = self.parser.find_by_xpath_waiting(wait, EC.presence_of_element_located, '//a[@data-marker="anonymous-number-bottom-sheet/call"]').get_attribute('href')
        except TimeoutException:
            raise AvitoTimeoutException("No contact Bar")
        tel = tel.replace('%C2%A0','').replace('-','')[4:]
        return tel                    
