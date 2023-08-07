from multiprocessing import Queue
from multiprocessing.managers import DictProxy
from models import AdvertModel, LastTimeAdvert
import logging
from models import AdvertModel, AvitoTimeoutException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from base_parser import BaseManager
from typing import List
from threading import Event

class AvitoUrlParser(BaseManager):
    def __init__(self, kill:Event, queue_get: Queue, queue_sender: Queue, queue_checker:Queue, file_log: str, name_log:str, wait_check_queue: int) -> None:
        super().__init__(kill, queue_get, queue_sender, file_log, name_log, wait_check_queue)
        self.logger = logging.getLogger(f"UP_{name_log}")
        self.wait_find = 3
        self.queue_checker = queue_checker
    
    def action(self):
        url = self.current_model[0]
        url_id_dict = self.current_model[1]
        # self.logger.info(str(manager))
        self.getUrl_or_raiseAvitoEx(url)
        wait_max = 30
        while True:
            if self.wait_find > wait_max:
                raise AvitoTimeoutException(f"WAIT > {wait_max} ERROR")
            try:
                list_model = self.get_list_advert_model(url_id_dict, url)
                self.wait_find = 3
                break
            except TimeoutException:
                self.logger.warning(f'Get Advert TIMEOUT exception, wait {self.wait_find}')
                self.wait_find += 3
        
        for model in list_model:
            self.queue_sender.put(model)
    
    def get_list_advert_model(self, url_id_dict: DictProxy, url:str) -> List[AdvertModel]:
        last_id_list = url_id_dict[url]
        adverts = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_all_elements_located, xpath= '//div[@data-marker="items/list"]/div/div[@itemtype="http://schema.org/Product"]') # лист обьявлений
        # adverts = driver.find_elements(By.XPATH, '//*[@itemtype="http://schema.org/Product"]')#for debug
        advert_model_list = [] ## список моделей обьявления для post
        all_parse_id_model_list = []
        flag_existing_advert = False
        for ad in adverts:
            id_atribute = ad.get_attribute('data-marker')
            id_xpath = '//*[@data-marker="{}"]'.format(id_atribute)
            id = id_atribute.replace('item-wrapper(', '').replace(')', '') # образец item-wrapper(2165335464)
            all_parse_id_model_list.append(id)
            if id in last_id_list:
                flag_existing_advert = True
            flag_new_page_proof = False
            try:
                date = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+'//*[@data-marker="item/datetime"]') #время выставления обьявления
            except TimeoutException:
                flag_new_page_proof = True
                date = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+'//*[@data-marker="dateLabelList"]')
            date = LastTimeAdvert.s_str_time_to_datetime(date.text)

            if not flag_existing_advert: #новое обьявление
                self.logger.info(f'new ad, id {id}')
                advert_name_xp = '//*[@data-marker="item/title"]'
                link_xp = '//a[@data-marker="item/link"]'
                address_xp = '//*[@data-marker="item/address"]'
                location_xp = '//*[@data-marker="item/georeferences"]'
                post_time_xp = '//*[@data-marker="item/datetime"]'
                if flag_new_page_proof:
                    advert_name_xp = '//*[@data-marker="titleLabelList"]'
                    link_xp = '//a[@data-marker="item/link"]'
                    address_xp = '//*[@data-marker="addressLabelList"]'
                    location_xp = '//*[@data-marker="georeferencesLabelList"]'
                    post_time_xp = '//*[@data-marker="dateLabelList"]'
                advert_name = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+advert_name_xp).text
                link = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.presence_of_element_located, xpath=id_xpath+link_xp).get_attribute('href')
                try:
                    address = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+address_xp).text
                except:
                    address = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+location_xp).text
                    self.logger.warning(f"No address {id}")
                post_time = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+post_time_xp).text
                post_time = LastTimeAdvert.s_str_time_to_datetime(post_time)
                advert_model_list.append(AdvertModel(advert_name=advert_name,link=link,id=id,post_time=post_time,address=address))

        url_id_dict[url] = all_parse_id_model_list
        return advert_model_list


    # def get_list_advert_model(self) -> List[AdvertModel]:
    #     adverts = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_all_elements_located, xpath= '//*[@itemtype="http://schema.org/Product"]') # лист обьявлений
    #     # adverts = driver.find_elements(By.XPATH, '//*[@itemtype="http://schema.org/Product"]')#for debug
    #     advert_model_list = [] ## список моделей обьявления для post
    #     first_datetime = None
    #     last_time = LastTimeAdvert()
    #     for ad in adverts:
    #         id_atribute = ad.get_attribute('data-marker')
    #         id_xpath = '//*[@data-marker="{}"]'.format(id_atribute)
    #         flag_new_page_proof = True
    #         try:
    #             date = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+'//*[@data-marker="item/datetime"]') #время выставления обьявления
    #         except TimeoutException:
    #             flag_new_page_proof = False
    #             date = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+'//*[@data-marker="dateLabelList"]')
    #         date = date.text
    #         date = LastTimeAdvert.s_str_time_to_datetime(date)
    #         if date <= last_time.get_time_epoch():
    #             break
    #         else: #новое обьявление
    #             logging.info('new ad')
    #             if first_datetime is None:
    #                 first_datetime = LastTimeAdvert.s_str_time_to_datetime(self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath='//*[@data-marker="item/datetime"]').text)
                
    #             if flag_new_page_proof:
    #                 advert_name = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+'//*[@data-marker="item/title"]').text
    #                 link = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.presence_of_element_located, xpath=id_xpath+'//a[@data-marker="item/link"]').get_attribute('href')
    #                 id = id_atribute[-11:-1] # образец item-wrapper(2165335464)
    #                 try:
    #                     address = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+'//*[@data-marker="item/address"]').text
    #                 except:
    #                     address = None
    #                     logging.exception("No address")
    #                 post_time = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+'//*[@data-marker="item/datetime"]').text
    #                 post_time = LastTimeAdvert.s_str_time_to_datetime(post_time)
    #                 advert_model_list.append(AdvertModel(advert_name=advert_name,link=link,id=id,post_time=post_time,address=address))
    #             else:
    #                 advert_name = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+'//*[@data-marker="titleLabelList"]').text
    #                 link = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.presence_of_element_located, xpath=id_xpath+'//a[@data-marker="item/link"]').get_attribute('href')
    #                 id = id_atribute[-11:-1] # образец item-wrapper(2165335464)
    #                 try:
    #                     address = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+'//*[@data-marker="addressLabelList"]').text
    #                 except:
    #                     address = None
    #                     logging.exception("No address")
    #                 post_time = self.parser.find_by_xpath_waiting(wait=self.wait_find, EC_config=EC.visibility_of_element_located, xpath=id_xpath+'//*[@data-marker="dateLabelList"]').text
    #                 post_time = LastTimeAdvert.s_str_time_to_datetime(post_time)
    #                 advert_model_list.append(AdvertModel(advert_name=advert_name,link=link,id=id,post_time=post_time,address=address))

    #     if first_datetime is not None:
    #         last_time.set_datetime(first_datetime)
    #         logging.info('new last time = {}'.format(last_time.get_str_time()))
    #     return advert_model_list
