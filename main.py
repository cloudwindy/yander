#!/bin/env python3
# -*- coding: utf-8 -*-
"""
Yande.re Crawler - A crawler to get pictures automatically
from Yande.re.
"""
import ssl
from ssl                   import _create_unverified_context
from sys                   import maxsize
from os                    import chdir, makedirs
from os.path               import exists
from time                  import time
from json                  import loads
from logging               import getLogger
from hashlib               import md5
from argparse              import ArgumentParser
from http.client           import IncompleteRead
from urllib.error          import URLError, HTTPError
from urllib.request        import urlopen
from multiprocessing.dummy import Pool
from logging               import basicConfig, DEBUG, INFO, WARNING, ERROR, CRITICAL

__author__ = 'cloudwindy'
__version__ = '1.9'

# 如果遇到SSL相关问题 取消这行注释
#ssl._create_default_https_context = _create_unverified_context

def main():
    parser = ArgumentParser(description = 'A crawler for yande.re')
    parser.add_argument('-v', '--version', action = 'version', version = 'Yande.re Crawler v%s by %s' % (__version__, __author__))
    parser.add_argument('-p', '--prefix', default = '.', help = 'specify prefix directory')
    parser.add_argument('-c', '--conf', default = 'config.json', help = 'specify config file path')
    parser.add_argument('-s', '--no-verify-ssl', default = False, help = "don't ")
    args = parser.parse_args()
    try:
        chdir(args.prefix)
    except:
    file = open(args.conf, 'r')
    conf = loads(file.read())
    file.close()
    basicConfig(level=DEBUG, format='[%(asctime)s %(name)s %(levelname)s] %(message)s', filename=conf['log_file'], filemode='w')
    run_main(conf['tags'], conf['thread_num'], conf['save_dir'])

def run_main(tags, thread_num, save_dir):
    tags = tags
    thread_num = thread_num
    save_dir = save_dir
    log = getLogger('控制')
    log.info('Yande.re 下载工具 %s' % __version__)
    if thread_num > 5:
        log.warning('线程数量大于 5 可能导致下载失败')
        log.warning('原因是 Yande.re 网站最大连接数为 5')
    if tags == '':
        log.info('未指定标签 默认下载所有图片')
    try:
        pool = Pool(thread_num)
        if not exists(save_dir):
            log.info('保存路径不存在')
            log.info('已创建文件夹' + save_dir)
            makedirs(save_dir)
        for page in range(1, maxsize):
            log.info('页面 %d: 正在获取元数据' % page)
            url = 'http://yande.re/post.json?limit=100&page=%d&tags=%s' % (page, tags)
            pic_list = loads(urlopen(url).read().decode())
            # 检测 图片数量
            if len(pic_list) <= 0:
                log.info('页面 %d: 已到达最后一页 准备退出' % page)
                break
            # 排序 从大到小排列
            pic_list.sort(key = lambda pic_list: pic_list['file_size'], reverse = True)
            # 给定 保存路径
            i = 0
            while i < len(pic_list):
                v = pic_list[i]
                pic_list[i]['save_path'] = '%s%d.%s' % (save_dir, v['id'], v['file_ext'])
                i += 1
            # 移除 重复图片
            for pic in pic_list:
                if exists(pic['save_path']):
                    log.debug('页面 %d: ')
                    pic_list.remove(pic)
            # 给定 图片ID
            i = 0
            while i < len(pic_list):
                pic_list[i]['_id'] = i
                i += 1
            if len(pic_list) > 0:
                log.info('页面 %d: 已获取元数据. 共 %d 张图片' % (page, len(pic_list)))
                log.info('页面 %d: 开始下载' % page)
                pool.map(get_pic, pic_list)
                log.info('页面 %d: 下载完毕' % page)
    except KeyboardInterrupt:
        log.info('用户已关闭程序 准备退出')
    except HTTPError as e:
        o = e.reason
        log.exception('服务器错误 原因：%d %s' % (o.errno, o.strerror))
    except URLError as e:
        o = e.reason
        log.exception('链接错误 原因：%d %s' % (o.errno, o.strerror))
    except Exception:
        log.exception('发生了未知错误 原因如下')
    pool.close()
    log.info('正在等待任务结束')
    try:
        pool.join()
    except:
        log.warning('正在强制停止全部任务')
        log.warning('当前正在下载的数据将被丢弃')
    log.info('下载工具已退出')

def get_pic(pic):
    log = getLogger('任务' + str(pic['_id']).rjust(3))
    try:
        (file, speed) = _fetch_file(pic['file_url'])
        if len(file) == pic['file_size'] and _check(file, pic['md5']):
            _save(file, pic['save_path'])
            log.info('任务结束 下载速度：%s/s' % _convert(speed))
        else:
            log.warning('数据完整性检查失败 正在重新下载')
            get_pic(pic)
    except IncompleteRead as e:
        log.warning('数据大小检查失败 正在重新下载')
        get_pic(pic)
    except HTTPError as e:
        o = e.reason
        log.exception('服务器错误 %d %s' % (o.errno, o.strerror))
    except URLError as e:
        o = e.reason
        log.exception('链接错误 %d %s' % (o.errno, o.strerror))
        get_pic(pic)
    except Exception:
        log.exception('发生了未知错误 原因如下：')

# 私有方法

def _fetch_file(url):
    start_time = time()
    file = urlopen(url).read()
    end_time = time()
    exec_time = end_time - start_time
    return (file, (len(file) / exec_time)) # bytes / sec

def _check(file, file_md5):
    checker = md5()
    checker.update(file)
    result_md5 = checker.hexdigest()
    return result_md5 == file_md5

def _save(file, save_path):
    f = open(save_path, 'wb')
    f.write(file)
    f.close()

def _convert(size):
    # Reference：https://blog.csdn.net/mp624183768/article/details/84892999
    kb = 1024
    mb = 1024 * 1024
    gb = 1024 * 1024 * 1024
    tb = 1024 * 1024 * 1024 * 1024
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

if __name__ == '__main__':
    main()
