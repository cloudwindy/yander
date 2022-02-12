# yande-downloader (yander)
本项目是图片爬虫项目，可以从如 https://yande.re 之类的以 danbooru 为基础的网站上爬取图片（可以爬R18）。为了得到最佳的速率，建议使用离目标网站同一国家甚至同一机房的服务器。（要爬yandere的话建议使用日本主机）
## For English users
This is a crawler project for downloading images from https://yande.re or similar websites. To get the best speed, it's recommended to use a server as close as possible to the target website. By the way I'm too lazy to translate this page to English but feel free to create new issues.

# Yander 爬虫工具
## Windows 安装指南
0. 如果你已经安装 Python 3，跳转到第 4 步。
1. 前往最新的 Python 3 版本发布页面（一键传送👉https://www.python.org/downloads/）
2. 选择适合你 Windows 版本的 Python（你也可以直接点黄色的 Download Python 按钮）
3. 下载 Python 安装包
4. Git 克隆本项目（点绿色的写着 Code 的按钮然后点 Download ZIP 然后解压）
5. 按需求配置 config.json
6. 双击 main.py 运行 或者在控制台窗口输入 python3 main.py 然后回车

## Linux 安装指南
### Ubuntu / Debian-based 操作系统
```
sudo apt-get update
sudo apt-get install -y python3 git
git clone https://github.com/cloudwindy/yander
cd yander
```

### CentOS / RedHat-based 操作系统
```
sudo yum install -y python3 git
git clone https://github.com/cloudwindy/yander
cd yander
```

## 配置文件详解（当前版本）
|         参数         | 类型 |     解释      |     默认     |
| -------------------- | ---- | ------------- | ------------ |
| start                | 必选 | 起始页码      |              |
| end                  | 必选 | 结束页码      |              |
| save_dir             | 必选 | 保存路径      |              |
| thread_num           | 可选 | 线程数        | 单线程       |
| log                  | 可选 | 日志位置      | 不记录日志   |
| log_autopurge        | 可选 | 自动清空日志  | 不清空日志   |
| tags                 | 可选 | 标签          | 处理全部图片 |
| except_tags          | 可选 | 排除标签      | 不排除图片   |
| no_check_certificate | 可选 | 不检查SSL证书 | 检查SSL证书  |
| proxy                | 可选 | 使用代理      | 不使用代理   |
| proxy_addr           | 可选 | 代理地址      | 不使用代理   |

**有计划在未来实现yaml配置文件，请拭目以待！**

# 配置文件详解（未来，现在还不能用）

## 术语解释

程序：指的是本项目的主程序 main.py。

模块：配置文件中的对象，比如说```"log":{"enabled": true}```，那么log就是一个模块，enabled决定这个模块是启用还是禁用的状态。（enabled是所有可禁用模块必须的参数）对于不可禁用的模块例如```"pages":{"mode":"infinite"}```，mode决定这个模块的运行状态（mode是所有不可禁用模块必须的参数）。

参数：配置文件中对象下的属性，比如说```"log":{"path":"./save"}```，那么path就是一个参数，这个参数决定了log模块是如何工作的。

标志：main.py 中的一些不属于配置文件的一部分配置，用于调试。这些标志中有的将来可能会移动到配置文件中，有的会被写死（hardcode）。标志可以在 main.py 源代码中找到，通常自带注释。

页面：由于 yande.re API 限制，一个页面是100张图片。

目标页面：要处理的页面，因为本程序除了下载以外还可以更改、校验、共享（正在开发）已下载的图集，因此不能称为“要下载的页面”。如果你只用这个程序来下载，那么当然可以理解为“要下载的页面”。

处理：下载、更改、校验、共享（正在开发）。主要是下载。

## **模块：run 参数**
参数模块用于存储程序运行的基础参数。不可能禁用。

### 参数：mode 运行模式
程序运行的模式。有以下三个选项：
* ```"download"``` 下载模式（默认）
* ```"verify"``` 校验模式
* ```"web"``` 后端模式（开发中）

### 参数：path 保存路径
文件保存到的路径。

* 同时接受 Windows 风格路径（“\\\\”）和 Linux 风格路径（“/”）。
* 末尾斜杠可有可无。
* 如果路径不存在，那么程序会尝试自动创建它。
* 请确保目标路径的权限设定允许当前用户访问。
* 不要在 Windows 上使用 ```con```、```nul``` 等设备名。

示例：./save 保存到当前文件夹下的 save 子文件夹。

默认：./save

### 参数：delete 授权删除
授权程序删除本地文件。有以下两个选项：
* ```true``` 授权
* ```false``` 不授权

**警告：此选项将允许程序删除保存路径中已存储的文件。请仅在需要时启用，并在使用完成后立刻关闭！**

## **模块：pages 页面**
页面模块用于存储目标页面的信息。不可能禁用。

### 参数：mode 页面模式
指定目标页面的模式。有以下四个模式：
* ```"infinite"``` 一直运行到最后一页为止。**不推荐：程序出现问题时将会卡死。**
* ```"single"``` 只处理一个页面。
* ```"list"``` 只处理列表中的页面。
* ```"range"``` 只处理区间内的页面。

### 参数：single 单个页面
只有页面模式为"single"时有效。只处理参数值指定的页面

示例：2 只下载第二页

### 参数：list 列表
只有页面模式为"list"时有效。参数值指定所有要处理的页面。

示例：[1, 4, 5] 只下载第一页、第四页和第五页。

### 参数：range 区间
只有页面模式为"list"时有效。

示例：[1, 4] 下载一到四页（那么也就是第一页，第二页，第三页，**第四页**）

## **模块：parallel 并行下载**
并行下载模块用于多线程加速下载。禁用后只用一个线程。

### 参数：jobs 线程数
指定下载的线程数。**注意：过高的并发量可能引起HTTP429报错。**
示例：5 使用五线程下载（推荐）

## **模块：tags 标签**
标签模块用于根据标签过滤图片。禁用后不对目标图片做任何限制，也就是处理一切图片。除了以下两个参数所规定不下载的图片之外的所有图片都会被下载。仅当运行模式为下载模式和校验模式时有效。

### 参数：required 必要标签
必须包含的标签。下载模式时，不包含此标签的图片将不会被下载。校验模式时，**如果已授权删除，那么不包含此标签的图片将被主动删除。**

示例：["yuri", "loli"] 只下载含有“yuri”（百合）及“loli”（萝莉）标签的图片。格式与列表相同。

### 参数：rejected 排除标签
不能包含的标签。下载模式时，包含此标签的图片将不会被下载。校验模式时，**如果已授权删除，那么包含此标签的图片将被主动删除。**

示例：["extreme_content", "rating:e"]，不下载含有“extreme_content”（猎奇）及“rating:e”（R18）标签的图片。

## **模块：log 日志**
日志模块用于记录运行过程中的事件。禁用后不保存日志。

### 参数：path 日志路径
日志文件存储的路径。格式与保存路径相同。

示例：./yander.log 日志将被保存到 yander.log 文件

## **模块：proxy 代理**
代理模块用于将流量重定向到HTTP代理。禁用后不使用代理。

### 参数：addr 代理地址
代理服务器的IP地址。

### 参数：port 代理端口
代理服务器的端口。

## **模块：db 数据库**
数据库模块用于提供程序与数据库的接口。禁用后不使用数据库。只有运行模式为后端时有效。
