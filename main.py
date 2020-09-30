#!/bin/env python3
# -*- coding: utf-8 -*-
# 导入内部模块
from os                    import devnull, chdir, makedirs, remove
from os.path               import exists, join, getsize
from sys                   import maxsize
from time                  import time
from json                  import loads
from hashlib               import md5
from argparse              import ArgumentParser
from multiprocessing.dummy import Pool

# 导入外部模块
missing = []
try:
    from tqdm import tqdm
except ImportError:
    missing.append('tqdm')

try:
    from logzero import setup_logger, LogFormatter
except ImportError:
    missing.append('logzero')

try:
    from requests import Session, get
    from requests.adapters import HTTPAdapter
except ImportError:
    missing.append('requests')

if missing:
    print(f'''
 严重错误: Yande.re 下载工具缺少一些必要的依赖

 tqdm     - 用于显示进度 {"(缺失)" if "tqdm" in missing else ""}
 logzero  - 用于记录日志 {"(缺失)" if "logzero" in missing else ""}
 requests - 用于发起请求 {"(缺失)" if "requests" in missing else ""}

 请运行以下的命令以安装这些依赖
 pip3 install tqdm logzero requests
''')
    exit()


class Flags:
    '''
    以下是一些调试以及实验性的参数
    除非是为了测试 否则这些参数不应改变
    '''
    # 区块大小 数值越大占用内存越大
    CHUNK_SIZE = 32 * kb
    # 不检查 HTTPS 证书
    NO_CHECK_CERTIFICATE = False
    # 无限重试
    ENDLESS_RETRY = True
    # 使用旧版 UIPrinter
    UI_PRINTER_VER_1 = False
    # 作者名字 我觉得应该没人要改这个...
    ARTHUR_NAME = 'cloudwindy'


# 导入本地模块
if Flags.UI_PRINTER_VER_1:
    from cli1 import UIPrinter, Fore, Back, Style, init
else:
    from cli2 import UIPrinter, Fore, Back, Style, init


class Application:
    '''主程序'''

    def main(self):
        parser = ArgumentParser(description='Yande.re 爬虫')
        parser.add_argument('-v',
                            '--version',
                            action='version',
                            version='Yande.re 爬虫 by %s' % Flags.ARTHUR_NAME)
        parser.add_argument('-p',
                            '--prefix',
                            type=chdir,
                            default='.',
                            help='指定工作路径')
        parser.add_argument('-c',
                            '--conf',
                            type=open,
                            default='./config.json',
                            help='指定配置文件路径')
        parser.add_argument('-V',
                            '--verify',
                            action='store_true',
                            default=False,
                            help='检查文件完整性')
        args = parser.parse_args()
        ui = UIPrinter('初始化')
        ui.note('Yande.re %s工具' % ('校验' if args.verify else '下载'))
        conf = loads(args.conf.read())
        args.conf.close()
        # - 可选参数 thread_num 线程数量
        # 默认值: 1
        self.thread_num = conf.get('thread_num', 1)
        # - 必选参数 save_dir 保存路径
        self.save_dir = conf['save_dir']
        # - 可选参数 tags 主标签
        # 默认值: 不指定标签
        self.tags = conf.get('tags')
        if not self.tags:
            ui.warn('未指定标签 默认处理所有图片')
        # - 可选参数 except_tags 排除的标签
        # 默认值: 不排除标签
        if except_tags := conf.get('except_tags'):
            self.except_tags = '-' + except_tags.replace('-', '+-')
        else:
            ui.warn('未排除标签 不会自动过滤猎奇等类型图片')
        # - 必选参数 start 起始页码
        if start := conf.get('start'):
            self.start = start
        else:
            ui.fail('未指定起始页码("start")!')
        # - 可选参数 end 结束页码
        # 默认值: 处理直到最后一页
        # 特殊值: 为 -1 时下载到最后一页
        end = conf.get('end')
        if not end or end < 0:
            self.end = maxsize
            ui.warn('程序将处理到最后一页')
        # 特殊值: 等于 start 或为 0 时只下载 start 指定的页面
        elif end in (start, 0):
            self.end = start + 1
            ui.warn('程序将仅处理第 %d 页' % start)
        else:
            self.end = end
        # - 可选参数 proxy_addr 代理地址
        if conf.get('proxy') and (addr := conf.get('proxy_addr')):
            self.proxies = {
                'http': 'http://' + addr,
                'https': 'http://' + addr
            }
            ui.warn('已启用 HTTP(S) 代理: %s' % addr)
        # - 可选参数 log 日志路径
        # 默认值: 不记录日志
        self.logfile = logfile = conf.get('log')
        # - 可选参数 log_autopurge 自动清空日志
        # 默认值: 不清空日志
        if conf.get('log_autopurge') and exists(logfile):
            remove(logfile)
            ui.warn('已删除旧日志: ' + logfile)
        # - 实验参数 Flags.NO_CHECK_CERTIFICATE
        if Flags.NO_CHECK_CERTIFICATE:
            ui.warn('已禁用 SSL 证书认证')
        if args.verify:
            self.verify_mode()
        else:
            self.download_mode()

    def download_mode(self):
        '''下载模式: 自动下载所有图片'''
        ui = UIPrinter('主程序')
        pool = Pool(self.thread_num)
        if not exists(save_dir := self.save_dir):
            ui.warn('保存路径不存在: ' + save_dir)
            ui.succ('已创建文件夹' + save_dir)
            makedirs(save_dir)
        for page in range(self.start, self.end):
            try:
                if self.get_page(page, pool):
                    break
            except KeyboardInterrupt:
                print()
                ui.note('用户已关闭程序 退出')
                break
            except Exception:
                ui.fail('发生了错误:')
        pool.close()
        ui.note('正在等待任务结束')
        try:
            pool.join()
        except KeyboardInterrupt:
            print()
            ui.warn('正在强制停止全部任务')
            ui.warn('当前正在下载的任务将被丢弃')
        ui.note('下载工具已退出')

    def verify_mode(self):
        '''校验模式: 验证图片完整性 不通过则删除'''
        main_ui = UIPrinter('主程序')
        if not exists(self.save_dir):
            main_ui.fail('请先下载再校验')
            return
        for page in range(self.start, self.end):
            page_ui = UIPrinter('页面 %d' % page)
            pic_list = self._get_pic_list(page)
            if len(pic_list) <= 0:
                page_ui.note('已到达最后一页 退出')
                return
            for pic in tqdm(pic_list,
                            desc='页面 %d' % page,
                            dynamic_ncols=True):
                pic_log = self._get_logger('图片 %d' % pic['id'])
                try:
                    realmd5 = None
                    with open(self._path(pic), 'rb') as f:
                        realmd5 = md5(f.read()).hexdigest()
                    if realmd5 != (picmd5 := pic['md5']):
                        path = self._path(pic)
                        remove(path)
                        pic_log.warning('%s != %s', realmd5, picmd5)
                except FileNotFoundError:
                    pass
                except Exception:
                    pic_log.exception('')
        main_ui.note('校验工具已退出')

    def get_page(self, page, pool):
        '''获取页面元数据'''
        ui = UIPrinter(f'页面 {page}')
        ui.wait('正在获取元数据')
        pic_list = self._get_pic_list(page)
        pic_list_len = len(pic_list)
        # 检测 图片数量
        if pic_list_len <= 0:
            ui.note('已到达最后一页 退出')
            return
        ui.succ('已获取元数据')
        ui.wait('正在移除重复图片...')
        for pic in pic_list[:]:
            # 如果图片已有大小等于元数据 移出下载列表
            if exists(self._path(pic)):
                if self._get_size(pic) == pic['file_size']:
                    pic_list.remove(pic)
        # 别移没了
        if pic_list_len <= 0:
            ui.no('已下载完毕 跳过')
            return
        ui.wait('正在进行大小排序...')
        # 排序 从大到小排列
        pic_list.sort(key=lambda pic_list: pic_list['file_size'], reverse=True)
        ui.succ('共 %d 张图片' % len(pic_list))
        ui.note('下载开始')
        pool.map(self.get_pic, pic_list)
        ui.succ('下载完毕')

    def get_pic(self, pic):
        '''
        下载单张图片
        由于 Yande.re 不支持, 断点续传功能已移除
        '''
        log = self._get_logger('图片' + str(pic['id']))
        while True:
            try:
                log.info('下载开始 大小: %s', _convert(pic['file_size']))
                # 禁用自动重试
                req = Session()
                req.mount('http://', HTTPAdapter(max_retries=0))
                req.mount('https://', HTTPAdapter(max_retries=0))
                t1 = time()
                # 向图片地址发起请求
                res = req.get(pic['file_url'],
                              stream=True,
                              timeout=30,
                              verify=not Flags.NO_CHECK_CERTIFICATE,
                              proxies=self.proxies)
                # HTTP 状态码检查
                res.raise_for_status()
                t2 = time()
                log.info('连接完成 用时: %d毫秒', int((t2 - t1) * 100))
                # 打开文件准备写入
                with open(self._path(pic), 'wb') as f:
                    # 配置进度条
                    with tqdm(unit='B',
                              unit_scale=True,
                              desc='图片' + str(pic['id']),
                              total=pic['file_size'],
                              leave=False,
                              dynamic_ncols=True) as pbar:
                        # 按区块读取
                        for chunk in res.iter_content(chunk_size=Flags.CHUNK_SIZE):
                            if chunk:
                                pbar.update(f.write(chunk))
                            else:
                                break
                t3 = time()
                speed = _convert(pic['file_size'] / (t3-t2))
                log.info("下载完成 速度: %s/s", speed)
                break
            except Exception:
                # 错误重试
                log.exception('正在重试...')
                if not Flags.ENDLESS_RETRY:
                    break

    def __init__(self):
        # 预定义所有参数
        self.start = None
        self.end = None
        self.tags = None
        self.except_tags = None
        self.uifile = None
        self.autopurge = True
        self.proxies = None
        self.thread_num = None
        self.save_dir = None
        self.force_http = False
        self.main()

    def _get_logger(self, name):
        '''获取logger'''
        fmt = LogFormatter(
            fmt='[%(levelname)1.1s %(asctime)s] %(name)s: %(message)s')
        return setup_logger(name, logfile=devnull, formatter=fmt, disableStderrLogger=True)

    def _get_pic_list(self, page):
        '''请求图片列表API'''
        url = f'https://yande.re/post.json?limit=100&page={page}&tags={self.tags}'
        return loads(get(url, verify=not Flags.NO_CHECK_CERTIFICATE, proxies=self.proxies).text)

    def _path(self, pic):
        '''根据图片元数据和保存位置生成对应路径'''
        return join(self.save_dir, '%d.%s' % (pic['id'], pic['file_ext']))

    def _get_size(self, pic):
        '''获取文件大小 用于检查是否下载完了'''
        return getsize(self._path(pic))


def _convert(size):
    '''转换为人类可读单位'''
    # 参考: https://bui.csdn.net/mp624183768/article/details/84892999
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

# 无聊的全局变量们

__author__ = 'cloudwindy'

# 基本单位
kb = 1024
mb = 1024 * 1024
gb = 1024 * 1024 * 1024
tb = 1024 * 1024 * 1024 * 1024

if __name__ == '__main__':
    init()
    Application()
