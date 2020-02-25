#!/bin/env python3
# -*- coding: utf-8 -*-
"""
Yande.re Crawler - A crawler to get pictures automatically
from Yande.re.
"""
import ssl
from ssl                   import _create_unverified_context
from sys                   import maxsize
from os                    import chdir, makedirs, remove
from os.path               import exists, join, getsize
from time                  import time
from json                  import loads
from logging               import getLogger
from hashlib               import md5
from argparse              import ArgumentParser
from http.client           import IncompleteRead
from urllib.error          import URLError, HTTPError
from urllib.request        import urlopen, UnknownHandler, ProxyHandler, build_opener, install_opener
from multiprocessing.dummy import Pool

import logzero
from logzero  import LogFormatter, setup_default_logger, setup_logger
from requests import get

__author__ = 'cloudwindy'
__version__ = '2.1'

# 基本单位
kb = 1024
mb = 1024 * 1024
gb = 1024 * 1024 * 1024
tb = 1024 * 1024 * 1024 * 1024

CHUNK_SIZE = 256 * kb

# 日志格式
log_format = '%(color)s[%(levelname)1.1s %(asctime)s] %(name)s:%(end_color)s %(message)s'
formatter = LogFormatter(fmt=log_format)

def main(tags):
    log = setup_logger('主程序', formatter=formatter)
    log.warning('当前区块大小: %s' % _convert(CHUNK_SIZE))
    if thread_num > 5:
        log.warning('线程数量大于 5 可能导致下载失败')
        log.warning('原因是 Yande.re 网站最大连接数为 5')
    if tags == '':
        log.warning('未指定标签 默认下载所有图片')
    pool = Pool(thread_num)
    if not exists(save_dir):
        log.debug('保存路径不存在: ' + save_dir)
        log.debug('已创建文件夹' + save_dir)
        makedirs(save_dir)
    for page in range(1, maxsize):
        try:
            if get_page(page, pool, tags):
                break
        except KeyboardInterrupt:
            print()
            log.info('用户已关闭程序 准备退出')
            break
        except Exception:
            log.exception('发生了错误:')
    pool.close()
    log.info('正在等待任务结束')
    try:
        pool.join()
    except KeyboardInterrupt:
        print()
        log.warning('正在强制停止全部任务')
        log.warning('当前正在下载的区块将被丢弃')
    log.info('下载工具已退出')

# 获取页面元数据
def get_page(page, pool, tags):
    log = setup_logger('页面 %d' % page, formatter=formatter)
    log.info('正在获取元数据')
    url = 'https://yande.re/post.json?limit=100&page=%d&tags=%s' % (page, tags)
    pic_list = loads(get(_url(url)).text)
    # 检测 图片数量
    if len(pic_list) <= 0:
        log.info('已到达最后一页 准备退出')
        return True
    # 移除 重复图片
    for pic in pic_list[:]:
        # 如果图片已有大小等于元数据 移出下载列表
        if exists(_path(pic)):
            size = _get_size(pic)
            if size > pic['file_size']:
                log.warning('文件大小%d比实际大小%d还大' % (size, pic['file_size']))
                remove(_path(pic))
            if size == pic['file_size']:
                pic_list.remove(pic)
    # 排序 从大到小排列
    pic_list.sort(key = lambda pic_list: pic_list['file_size'], reverse=True)
    # 给定 图片ID
    for i in range(len(pic_list)):
        pic_list[i]['_id'] = i
    if len(pic_list) > 0:
        log.debug('已获取元数据. 共 %d 张图片' % len(pic_list))
        log.info('下载开始')
        pool.map(get_pic, pic_list)
        log.info('下载完毕')
    else:
        log.info('已跳过')

# 下载一张图片
def get_pic(pic):
    log = setup_logger('任务' + str(pic['_id']).rjust(2), formatter=formatter)
    try:
        start = 0
        if exists(_path(pic)):
            start = _get_size(pic)
        _fetch_file(log, _url(pic['file_url']), _path(pic),  start, pic['file_size'])
        return
    except IncompleteRead as e:
        log.warning('数据大小检查失败 正在重新下载')
    except Exception:
        log.exception('下载失败 正在重新下载')
    get_pic(pic)

# 私有方法

# 如果启用了强制HTTP 更换协议
def _url(s):
    if force_http:
        return s.replace('https', 'http', 1)
    else:
        return s

# 获取文件大小 用于断点续传
def _get_size(pic):
    return getsize(_path(pic))

# 根据图片元数据和保存位置生成对应路径
def _path(pic):
    return join(save_dir, '%d.%s' % (pic['id'], pic['file_ext']))

# 获取单个文件 (断点续传)
def _fetch_file(log, url, save_path, start, end):
    log.debug('下载区间 %s - %s' % (_convert(start), _convert(end)))
    headers = {
        'Range': '%s-%s' % (str(start), str(end))
    }
    req = get(url, stream=True, headers=headers)
    size = end - start
    log.info('下载开始 大小: %s' % _convert(size))
    start_time = time()
    with open(save_path, 'ab') as f:
        chunk_start_time = time()
        for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                log.debug('实时速度: %s/s' % _speed(CHUNK_SIZE, chunk_start_time))
                f.write(chunk)
                f.flush()
                chunk_start_time = time()
            else:
                break
    log.info('下载结束 总速度: %s/s' % _speed(size, start_time))

def _speed(size, start_time):
    end_time = time()
    exec_time = end_time - start_time
    speed = size / exec_time
    return _convert(speed)

#def _check(content, file_md5):
#    checker = md5()
#    checker.update(content)
#    result_md5 = checker.hexdigest()
#    return result_md5 == file_md5

def _convert(size):
    # 参考：https://blog.csdn.net/mp624183768/article/details/84892999
    if size >= tb:
        return '%.1f TB' % (size / tb)
    elif size >= gb:
        return '%.1f GB' % (size / gb)
    elif size >= mb:
        return '%.1f MB' % (size / mb)
    elif size >= kb:
        return '%.1f KB' % (size / kb)
    else:
        return '%d B' % size

thread_num = None
save_dir = None
force_http = False
if __name__ == '__main__':
    parser = ArgumentParser(description = 'Yande.re 下载工具')
    parser.add_argument('-v', '--version', action = 'version', version = 'Yande.re 下载工具 v%s by %s' % (__version__, __author__))
    parser.add_argument('-p', '--prefix', default = '.', help = '制定工作路径')
    parser.add_argument('-c', '--conf', default = './config.json', help = '指定配置文件路径')
    args = parser.parse_args()
    log = setup_logger('主程序', formatter=formatter)
    log.info('Yande.re 下载工具')
    try:
        chdir(args.prefix)
    except FileNotFoundError:
        log.error('路径不存在: ' + args.prefix)
        exit()
    file = None
    try:
        file = open(args.conf, 'r')
    except FileNotFoundError:
        log.error('找不到配置文件: ' + args.conf)
        exit()
    conf = loads(file.read())
    file.close()
    thread_num = conf['thread_num']
    save_dir = conf['save_dir']
    if conf['force_http']:
        log.debug('已启用强制 HTTP')
        force_http = True
    elif conf['no_check_certificate']:
        log.debug('已禁用 SSL 证书认证')
        ssl._create_default_https_context = _create_unverified_context
    handler = UnknownHandler()
    if conf['proxy']:
        log.debug('已启用 HTTP 代理: ' + conf['proxy_addr'])
        handler = ProxyHandler({
            'http': 'http://' + conf['proxy_addr'],
            'https': 'https://' + conf['proxy_addr']
        })
    install_opener(build_opener(handler))
    main(conf['tags'])
