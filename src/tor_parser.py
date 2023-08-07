from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from tbselenium.tbdriver import TorBrowserDriver
from tbselenium.utils import prepend_to_env_var
from tbselenium import common
from tbselenium.exceptions import *

from stem.control import Controller
from stem.process import launch_tor_with_config
from stem import Signal

import logging
import os
import time
from datetime import datetime
from selenium.webdriver.common.utils import free_port

from tbselenium import tbdriver

import tempfile
import logging
from typing import List
from models import LastTimeAdvert
from threading import Event

DEBUG_MODE = False

class _Settings():
    def __init__(self, use_bridge:bool = True) -> None:
        self.TOR_TIMEOUT_LOAD = 90

        self.TOR_DATA_DIR = tempfile.mkdtemp()
        self.HOME_PATH = os.getcwd()
        self.TOR_LOG = 'notice file ' + self.HOME_PATH + '/logs/tor/notice'
        self.TB_PATH = self.HOME_PATH + '/tor-browser/tor-browser'
        self.DRIVER_PATH = self.HOME_PATH + '/driver/geckodriver'
        self.SOCKS_PORT = free_port()
        self.CONTROL_PORT = free_port()

        self.BRIDGE_SNOWFLAKE = ['snowflake 192.0.2.4:80 8838024498816A039FCBBAB14E6F40A0843051FA fingerprint=8838024498816A039FCBBAB14E6F40A0843051FA url=https://snowflake-broker.torproject.net.global.prod.fastly.net/ front=cdn.sstatic.net ice=stun:stun.l.google.com:19302,stun:stun.antisip.com:3478,stun:stun.bluesip.net:3478,stun:stun.dus.net:3478,stun:stun.epygi.com:3478,stun:stun.sonetel.net:3478,stun:stun.uls.co.za:3478,stun:stun.voipgate.com:3478,stun:stun.voys.nl:3478 utls-imitate=hellorandomizedalpn',
                                 'snowflake 192.0.2.3:80 2B280B23E1107BB62ABFC40DDCC8824814F80A72 fingerprint=2B280B23E1107BB62ABFC40DDCC8824814F80A72 url=https://snowflake-broker.torproject.net.global.prod.fastly.net/ front=cdn.sstatic.net ice=stun:stun.l.google.com:19302,stun:stun.antisip.com:3478,stun:stun.bluesip.net:3478,stun:stun.dus.net:3478,stun:stun.epygi.com:3478,stun:stun.sonetel.com:3478,stun:stun.uls.co.za:3478,stun:stun.voipgate.com:3478,stun:stun.voys.nl:3478 utls-imitate=hellorandomizedalpn',]
        self.TORCC = {'ControlPort': str(self.CONTROL_PORT),
                      'SOCKSPort': str(self.SOCKS_PORT),
                      'DataDirectory': self.TOR_DATA_DIR,}
                    #   'Log': self.TOR_LOG + '_cp' + str(self.control_port) + '_sp' + str(self.socks_port) + '.log',}

        if use_bridge:
            self.TORCC['UseBridges'] = '1'
            self.TORCC['ClientTransportPlugin'] = 'snowflake exec ' + self.TB_PATH + '/Browser/TorBrowser/Tor/PluggableTransports/snowflake-client'
            self.TORCC['Bridge'] = self.BRIDGE_SNOWFLAKE[0]
        
        
        self.OPTIONS = tbdriver.Options()
        self.OPTIONS.page_load_strategy = 'eager' # Доступ к DOM готов, но другие ресурсы, такие как изображения, все еще могут загружаться
        self.OPTIONS.headless = not DEBUG_MODE

        USER_AGENT = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16'
        self.PROFILE = {"privacy.resistFingerprinting": False, "general.useragent.override": USER_AGENT}



class TorParser():

    class ChangeIPException(Exception):
        pass

    _DEFAULT_TRYS_LOAD = 10

    def __init__(self, kill_event:Event, name_log:str) -> None:
        self.settings = _Settings(not DEBUG_MODE)
        self.logger = logging.getLogger(f'Tor - {name_log}')
        self.single_time = LastTimeAdvert()
        self.single_time.set_datetime(datetime.today()) # - timedelta(days=1))

        self.tor_process = None
        self.controller = None
        self.browser = None
        
        self.kill_event = kill_event
    
    def start_tor(self, timeout: int = 300) -> None:
        self.tor_process = self._wait_launch_tor_process(timeout=timeout)

        try:
            self.controller = Controller.from_port(port=self.settings.CONTROL_PORT)
            self.controller.authenticate()
        except Exception as err:
            self.logger.critical("Controller from port exeption", exc_info=True)
            raise err
        
    def get_browser(self, page_load_timeout: int = 150, trys: int = _DEFAULT_TRYS_LOAD) -> TorBrowserDriver:
        if self.browser:
            return self.browser
        else:
            for i in range(trys):
                try:
                    self.logger.info("TRY Start Browser")
                    self.browser = TorBrowserDriver(tbb_path=self.settings.TB_PATH,
                                                    executable_path=self.settings.DRIVER_PATH,
                                                    pref_dict=self.settings.PROFILE,
                                                    options=self.settings.OPTIONS,
                                                    socks_port=self.settings.SOCKS_PORT,
                                                    control_port=self.settings.CONTROL_PORT,
                                                    tor_cfg=common.USE_STEM,)
                    self.logger.info("SUCCESS START Browser")
                except:
                    self.logger.warning("Start Browser FAILED", exc_info=True)
                    self.quit_browser()
                    continue
                try:
                    self.logger.info("TRY Set page load timeout")
                    self.browser.set_page_load_timeout(page_load_timeout)
                    self.logger.info("SUCCESS SET page load timeout")
                except:
                    self.logger.warning("Set page load timeout FAILED", exc_info=True)
                    self.quit_browser()
                    continue
                return self.browser
            raise Exception(f"START TOR BROWSER FAILED, TRYS {trys}")
        
    def change_ip(self, trys: int = _DEFAULT_TRYS_LOAD) -> None:
        if self.browser:
            self.quit_browser()
        for t in range(trys):
            try:
                self.logger.info("TRY Change IP")
                self.controller.signal(Signal.NEWNYM)
                self.logger.info("SUCCESS CHANGE IP")
                return
            except:
                self.logger.warning("Change IP FAILED", exc_info=True)
                time.sleep(t*2)
                continue
        raise Exception(f"SEND NEWNUM TOR FAILED, TRYS {trys}")

    def find_by_xpath_waiting(self, wait: int, EC_config, xpath: str = '', is_log: bool = False) -> WebElement | List[WebElement]:
        if is_log:
            self.logger.info('find by xpath = {}'.format(xpath))
        return WebDriverWait(self.browser, wait).until(EC_config((By.XPATH, xpath)))

    def _wait_launch_tor_process(self, timeout: int, trys: int = _DEFAULT_TRYS_LOAD):
        tor_binary = os.path.join(self.settings.TB_PATH, common.DEFAULT_TOR_BINARY_PATH)
        prepend_to_env_var("LD_LIBRARY_PATH", os.path.dirname(tor_binary))

        def log_tor(init_line: str):
            self.logger.info(init_line)

        for i in range(trys):
            try:
                tor_process = launch_tor_with_config(config=self.settings.TORCC,
                                                     tor_cmd=tor_binary,
                                                     timeout=timeout,
                                                     init_msg_handler=log_tor)
                return tor_process
            except:
                self.logger.exception('Tor is not loaded')
        raise Exception(f"TOR LAUNCH FAILED, TRYS {trys}")
    
    def quit_browser(self) -> None:
        if self.browser is None:
            self.logger.info("SUCCESS QUIT Browser")
            return
        try:
            self.logger.info("TRY Quit Browser")
            self.browser.quit()
            self.logger.info("SUCCESS QUIT Browser")
        except:
            self.logger.warning("Quit Browser FAILED", exc_info=True)
        
        self.browser = None

    def close(self) -> None:
        self.quit_browser()


        if not self.tor_process is None:
            try:
                self.logger.info("TRY Tor Process Kill")
                self.tor_process.kill()
                self.logger.info("SUCCESS KILL Tor Process")
                self.tor_process = None
            except:
                self.logger.warning("Tor Process Kill FAILED", exc_info=True)

        if not self.controller is None:
            try:
                self.logger.info("TRY Controller close")
                self.controller.close()
                self.logger.info("SUCCESS CLOSE Controller")
                self.controller = None
            except:
                self.logger.warning("Controller close FAILED", exc_info=True)

        self.logger.info("ALL CLOSE")
    
    def subscribe_tor(self, action, *args, **kwargs):
        while True:
            time.sleep(1)
            try:
                self.start_tor()
            except:
                self.logger.critical("CRITICAL START TOR", exc_info=True)
                self.close()
                continue
            while True:
                try:
                    action(*args, **kwargs)
                    self.close()
                    return
                    # return будет срабатывать только если действие закончилось без ошибок 
                    # действие настроенно как бесконечный цикл и закончится без ошибок
                    # только при сигнале от вышестоящего менеджера
                except self.ChangeIPException:
                    try:
                        self.change_ip()
                    except:
                        self.logger.critical("CRITICAL CHANGE IP", exc_info=True)
                        self.close()
                        break
                except:
                    self.logger.critical("CRITICAL ACTION", exc_info=True)
                    self.close()
                    break
                finally:
                    if self.kill_event.is_set():
                        self.logger.info(f"DELETE TOR")
                        self.close()
                        return
