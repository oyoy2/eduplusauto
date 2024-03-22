from urllib.parse import urlparse

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def load(url, driver):
    driver.get(url)
    time.sleep(10)
    try:
        videos = driver.find_elements(By.TAG_NAME, 'video')
        if len(videos) > 0:
            print("加载视频成功")
            return True
        else:
            print("没有找到视频元素")
            return False
    except TimeoutException:
        print("加载视频超时")
        return False
