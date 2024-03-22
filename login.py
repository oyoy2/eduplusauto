from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def login(driver, account, password):
    driver.get('https://uc.eduplus.net/login')
    print("正在尝试自动登录...")
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        password_login_button_locator = "//div[text()='密码登录']"
        password_login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, password_login_button_locator))
        )
        password_login_button.click()

        account_input_locator = (By.XPATH, "//input[@placeholder='请输入账号/手机号']")
        password_input_locator = (By.XPATH, "//input[@placeholder='请输入密码']")

        account_input = driver.find_element(*account_input_locator)
        password_input = driver.find_element(*password_input_locator)

        account_input.send_keys(account)
        password_input.send_keys(password)

        login_button_locator = (By.CSS_SELECTOR, "button.el-button.el-button--primary.el-button--large")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(login_button_locator)
        )
        login_button.click()

        WebDriverWait(driver, 10).until(
            lambda driver: 'quc_ticket' in driver.current_url
        )
        quc_ticket_value = driver.current_url.split('quc_ticket=')[1].split('&')[0]
        print(f'成功获取到登录cookie: {quc_ticket_value}')
        return quc_ticket_value
    except NoSuchElementException as e:
        print("未找到某个元素，请检查选择器是否正确。")
    except TimeoutException as e:
        print("等待元素超时，请检查页面加载情况。")
    except Exception as e:
        print(f"发生错误: {e}")