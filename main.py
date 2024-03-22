import time
import pickle

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.support import expected_conditions as EC

import load
import login
import requests


def save_credentials(account, password):
    credentials = {'account': account, 'password': password}
    with open('credentials.pkl', 'wb') as file:
        pickle.dump(credentials, file)
    print("账号信息已保存。")


def load_credentials():
    try:
        with open('credentials.pkl', 'rb') as file:
            credentials = pickle.load(file)
        return credentials['account'], credentials['password']
    except FileNotFoundError:
        return None, None


def get_user_info(cookies):
    user_url = 'https://www.eduplus.net/athena_api/portal/users/name_avatar'
    response = requests.get(user_url, cookies=cookies)
    if response.status_code == 200:
        name_avatar = response.json()
        data = name_avatar['data']
        user = {'name': data['name'], 'username': data['username']}
        return user
    else:
        print("请求失败，状态码：", response.status_code)


def get_joined_courses(cookies):
    course_url = 'https://www.eduplus.net/api/course/courses/web/joined_courses?type=3'
    response = requests.get(course_url, cookies=cookies)
    if 'data' in response.json():
        courses_data = response.json()['data']['fieldList']
        joined_courses = []
        for course in courses_data:
            course_info = {
                'id': course['id'],
                'name': course['name'],
                'creator': course['creator']
            }
            joined_courses.append(course_info)

        return joined_courses
    else:
        print("无法获取课程信息，状态码：", response.status_code)
        return None


def fetch_course_details(cookies, course_id):
    course_info_url = f'https://www.eduplus.net/api/course/chapters/tree_list?courseId={course_id}&details=progress'
    response = requests.get(course_info_url, cookies=cookies)
    if response.status_code == 200:
        course_info = response.json()
        course_data = course_info['data']
        details_list = extract_course_details(course_data)
        return details_list
    else:
        print("请求失败，状态码：", response.status_code)
        return None


def extract_course_details(course_structure):
    details_list = []

    def traverse(details):
        for item in details:
            detail = {
                'name': item['name'],
                'type': item['type'],
                'resourceId': item.get('resourceId'),
                'id': item.get('id'),
                'studyStatusTitle': item.get('studyStatusTitle')
            }
            details_list.append(detail)
            if 'children' in item:
                traverse(item['children'])

    traverse(course_structure)
    return details_list


def remove_ChapterandRoot(details_list):
    filtered_list = []
    for detail in details_list:
        if (detail['type'] != 'Chapter' and detail['type'] != 'Root' and
                detail['studyStatusTitle'] != '已结束' and detail['resourceId'] is not None):
            filtered_list.append(detail)

    return filtered_list


def get_time(resourceId, cookies):
    resource_url = f'https://www.eduplus.net/api/course/user_coursewares/resource/{resourceId}'
    response = requests.get(resource_url, cookies=cookies)
    if response.status_code == 200:
        resource_data = response.json()
        resource_data = resource_data['data']
        totalTime = resource_data['totalTime']
        return totalTime
    else:
        print('获取时间失败')


def register_resource(driver, resourceId, courseId):
    previewWithMenu_url = f'https://www.eduplus.net/course/previewWithMenu/courseWare/{courseId}/{resourceId}?formLibCourse=false'
    print(previewWithMenu_url)
    if load.load(previewWithMenu_url, driver):
        print('注册资源成功')
    else:
        print('注册资源失败')


if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_experimental_option('detach', True)
    driver = webdriver.Chrome(options=options)
    options.add_argument('--ignore-certificate-errors')
    print('项目地址：https://github.com/oyoy2/eduplusauto')
    print('加载浏览器并最小化')
    driver.minimize_window()
    print('正在加载登录')
    save_choice = input('yes：保存账号密码 回车：读取账号密码(yes/回车): ').strip().lower()
    if save_choice == 'yes':
        account = input('请输入账号：')
        password = input('请输入密码：')
        save_credentials(account, password)
        print("账号信息已更新并保存。")
    else:
        account, password = load_credentials()
        if account and password:
            print("已加载账号信息：账号 =", account, "密码 =", password)
        else:
            print("未找到保存的账号信息。请重新输入。")
            account = input('请输入账号：')
            password = input('请输入密码：')
    SESSION = login.login(driver, account, password)
    cookies = {'SESSION': SESSION}
    user = get_user_info(cookies)
    courses = get_joined_courses(cookies)
    course_id = 0
    for course in courses:
        print('序号：' + str(course_id) + ' ' + course['name'] + ' ' + course['creator'])
        course_id += 1
    chose = input('请输入课程序号：')
    if chose.isdigit():
        chose = int(chose)
        if chose <= len(courses):
            course_id = courses[chose]['id']
            print('你选择了：' + courses[chose]['name'] + ' ' + courses[chose]['creator'])
            print('开始获取课程信息')
            course_details = fetch_course_details(cookies, course_id)
            course_details = remove_ChapterandRoot(course_details)
            wait = WebDriverWait(driver, 30)
            for detail in course_details:
                print('正在执行的课程：' + detail['name'])
                register_resource(driver, detail['resourceId'], courses[chose]['id'])
                if detail['type'] == 'Video':
                    print('开始查找视频')
                    video_element = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, '#videoPlayer video'))
                    )
                    print('视频已找到，开始播放')
                    action = ActionChains(driver)
                    action.move_to_element(video_element).click().perform()
                    mute_and_play_script = """
                                    var video = arguments[0];
                                    if (video && typeof video.muted !== 'undefined') {
                                      video.muted = true; // 将视频设置为静音
                                      video.play().catch(function(error) {
                                        console.error('播放视频时出错:', error);
                                      });
                                    }
                                    """
                    driver.execute_script(mute_and_play_script, video_element)
                    total_video_duration = driver.execute_script("return arguments[0].duration;", video_element)
                    last_reported_time = 0
                    current_time = driver.execute_script("return arguments[0].currentTime;", video_element)
                    progress_bar = tqdm(total=int(total_video_duration) - int(current_time), desc='视频播放进度')
                    if total_video_duration > 0:
                        try:

                            while True:
                                current_time = driver.execute_script("return arguments[0].currentTime;", video_element)
                                if current_time >= last_reported_time + 1:
                                    percentage = int((current_time / total_video_duration) * 100)  # 计算百分比
                                    progress_bar.set_postfix(
                                        {'current_time': int(current_time), 'percentage': str(percentage) + '%'},
                                        end='\r')
                                    last_reported_time = current_time
                                    progress_bar.update(1)
                                    time.sleep(1)
                                if current_time >= total_video_duration:
                                    break
                        except KeyboardInterrupt:
                            print('进度条被中断。')
                if detail['type'] == 'Pdf':
                    while True:
                        try:
                            pdf_element = WebDriverWait(driver, 10).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, 'iframe'))
                            )
                            pdf_element = pdf_element.find_element_by_tag_name('iframe')
                            pdf_element.click()
                            break
                        except:
                            print('PDF加载失败')
                            time.sleep(1)
        else:
            print('输入错误')
    else:
        print('输入错误')
