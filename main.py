#!/bin/env python3
# -*- coding: utf-8 -*-

# Python版本提示
import sys
if sys.version_info.major != 3:
	print('''
 严重错误: Yande.re 下载工具必须使用 Python 3

 如果您使用的操作系统是 Windows:
 请访问 https://www.python.org/downloads/windows/
 找到 Latest Python 3 Release
 找到 Files 章节并点击 Windows x86-64 executable installer
 请以管理员权限运行下载后的文件

 如果您使用的操作系统是 Debian & Ubuntu:
 请运行以下命令
 sudo apt install -y python3

 如果您使用的操作系统是 Red Hat & CentOS:
 请运行以下命令
 sudo yum install -y python3

 如果您使用的操作系统是 Arch Linux:
 请运行以下命令
 sudo pacman -S python3
	''')
	exit()

# Python内置库
import ssl
from os                    import chdir, makedirs, remove
from ssl                   import _create_unverified_context
from sys                   import maxsize
from time                  import time
from json                  import loads
from os.path               import exists, join, getsize
from hashlib               import md5
from argparse              import ArgumentParser
from contextlib            import contextmanager
from multiprocessing.dummy import Pool

# 依赖安装提示

missing = []
try:
	from tqdm              import tqdm
	from tqdm.contrib      import DummyTqdmFile
except ImportError:
	missing.append('tqdm')

try:
	from logzero           import setup_logger, LogFormatter
except ImportError:
	missing.append('logzero')

try:
	from requests          import Session, get
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

__author__ = 'cloudwindy'

# 基本单位
kb = 1024
mb = 1024 * 1024
gb = 1024 * 1024 * 1024
tb = 1024 * 1024 * 1024 * 1024

CHUNK_SIZE = 16 * kb

# 日志格式
LOG_FORMAT = LogFormatter(fmt='%(color)s[%(levelname)1.1s %(asctime)s] %(name)s:%(end_color)s %(message)s')
RECORD_FORMAT = LogFormatter(fmt='[%(levelname)1.1s %(asctime)s] %(name)s: %(message)s')

class Application:
	def main(self):
		'''主程序'''
		parser = ArgumentParser(description = 'Yande.re 爬虫')
		parser.add_argument('-v',
							'--version',
							action = 'version',
							version = 'Yande.re 爬虫 by %s' % __author__)
		parser.add_argument('-p',
							'--prefix',
							type = chdir,
							default = '.',
							help = '指定工作路径')
		parser.add_argument('-c',
							'--conf',
							type = open,
							default = './config.json',
							help = '指定配置文件路径')
		parser.add_argument('-V',
							'--verify',
							action='store_true',
							default = False,
							help = '检查文件完整性')
		args = parser.parse_args()
		log = self._get_logger('初始化')
		log.info('Yande.re %s工具' % ('校验' if args.verify else '下载'))
		conf = loads(args.conf.read())
		args.conf.close()
		# - 必选参数 thread_num 线程数量
		self.thread_num = conf['thread_num']
		# - 必选参数 save_dir 保存路径
		self.save_dir = conf['save_dir']
		# - 可选参数 tags 主标签
		# 默认值: 不指定标签
		self.tags = conf.get('tags')
		log.warning('未指定标签 默认处理所有图片') if not self.tags else ... 
		# - 可选参数 except_tags 排除的标签
		# 默认值: 不排除标签
		self.except_tags = '-' + conf['except_tags'].replace('-', '+-') if conf.get('except_tags') else None
		log.warning('未排除标签 不会自动过滤猎奇等类型图片') if not self.except_tags else ...
		# - 必选参数 start 起始页码
		start = conf['start']
		self.start = start
		# - 可选参数 end 结束页码
		# 默认值: 处理直到最后一页
		end = conf['end'] if conf.get('end') and not conf.get('end') < 0 else maxsize
		log.warning('程序将处理到最后一页') if not conf.get('end') else ...
		# 特殊值: 为 0 时只下载 start 指定的页面
		end = start + 1 if start == end else end
		log.warning('程序将仅处理第 %d 页' % start) if start == end else ...
		self.end = end
		# - 可选参数 proxy_addr 代理地址
		if conf.get('proxy') and conf.get('proxy_addr'):
			addr = conf['proxy_addr']
			self.proxies = {
				'http': 'http://' + addr,
				'https': 'http://' + addr
			}
			log.warning('已启用 HTTP(S) 代理: %s' % addr)
		# - 可选参数 no_check_certificate 不检查证书
		# 默认值: 检查证书
		self.verify = not conf.get('no_check_certificate')
		log.warning('已禁用 SSL 证书认证') if not self.verify else ...
		# - 可选参数 log 日志路径
		# 默认值: 不记录日志
		logfile = conf.get('log')
		self.logfile = logfile
		# - 可选参数 log_autopurge 自动清空日志
		# 默认值: 不清空日志
		if conf.get('log_autopurge') and exists(logfile):
			remove(logfile)
			log.warning('已删除旧日志: ' + logfile)
		if args.verify:
			self.verify_mode()
		else:
			self.download_mode()

	def download_mode(self):
		'''下载模式: 自动下载所有图片'''
		log = self._get_logger('主程序')
		pool = Pool(self.thread_num)
		if not exists(self.save_dir):
			log.debug('保存路径不存在: ' + self.save_dir)
			log.debug('已创建文件夹' + self.save_dir)
			makedirs(self.save_dir)
		for page in range(self.start, self.end):
			try:
				if self.get_page(page, pool):
					break
			except KeyboardInterrupt:
				print()
				log.info('用户已关闭程序 退出')
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
			log.warning('当前正在下载的任务将被丢弃')
		log.info('下载工具已退出')

	def verify_mode(self):
		'''校验模式: 验证图片完整性 不通过则删除'''
		main_log = self._get_logger('主程序')
		if not exists(self.save_dir):
			main_log.error('请先下载再校验')
			return
		for page in range(self.start, self.end):
			page_log = self._get_logger('页面 %d' % page)
			pic_list = self._get_pic_list(page)
			if len(pic_list) <= 0:
				page_log.info('已到达最后一页 退出')
				return
			for pic in tqdm(pic_list,
							desc = '页面 %d' % page,
							dynamic_ncols=True):
					pic_log = self._get_logger('图片 %d' % pic['id'], record=True)
					try:
						realmd5 = None
						with open(self._path(pic), 'rb') as f:
							realmd5 = md5(f.read()).hexdigest()
						if realmd5 != pic['md5']:
							path = self._path(pic)
							remove(path)
							pic_log.warning('%s != %s' % (realmd5, pic['md5']))
					except FileNotFoundError:
						pass
					except Exception:
						pic_log.exception('')
		main_log.info('校验工具已退出')

	def get_page(self, page, pool):
		'''获取页面元数据'''
		log = self._get_logger('页面 %d' % page)
		log.info('正在获取元数据')
		pic_list = self._get_pic_list(page)
		# 检测 图片数量
		if len(pic_list) <= 0:
			log.info('已到达最后一页 退出')
			return True
		log.debug('已获取元数据')
		log.debug('正在移除重复图片...')
		for pic in pic_list[:]:
			# 如果图片已有大小等于元数据 移出下载列表
			if exists(self._path(pic)):
				if self._get_size(pic) == pic['file_size']:
					pic_list.remove(pic)
		if len(pic_list) <= 0:
			log.info('已下载完毕 跳过')
			return
		log.debug('正在进行大小排序...')
		# 排序 从大到小排列
		pic_list.sort(key = lambda pic_list: pic_list['file_size'], reverse=True)
		log.debug('共 %d 张图片' % len(pic_list))
		log.info('下载开始')
		pool.map(self.get_pic, pic_list)
		log.info('下载完毕')

	def get_pic(self, pic):
		'''
		下载单张图片
		由于 Yande.re 不支持, 断点续传功能已移除
		'''
		log = self._get_logger('图片' + str(pic['id']), record=True)
		try:
			log.info('下载开始 大小: %s' % self._convert(pic['file_size']))
			# 禁用自动重试
			req = Session()
			req.mount('http://', HTTPAdapter(max_retries=0))
			req.mount('https://', HTTPAdapter(max_retries=0))
			t1 = time()
			# 向图片地址发起请求
			res = req.get(pic['file_url'],
						stream=True,
						timeout=30,
						verify=self.verify,
						proxies=self.proxies)
			# HTTP 状态码检查
			res.raise_for_status()
			t2 = time()
			log.info('连接完成 用时: %d毫秒' % int((t2 - t1) * 100))
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
					for chunk in res.iter_content(chunk_size=CHUNK_SIZE):
						# 判断区块是否为空
						if chunk:
							# 区块写入文件并更新进度条
							pbar.update(f.write(chunk))
						else:
							# 空区块 下载完成
							break
			t3 = time()
			speed = self._convert(pic['file_size'] / (t3-t2))
			log.info("下载完成 速度: %s/s", speed)
		except Exception:
			# 错误重试
			log.exception('正在重试...')
			self.get_pic(pic)

	def __init__(self):
		# 预定义所有参数
		self.start = None
		self.end = None
		self.tags = None
		self.except_tags = None
		self.logfile = None
		self.autopurge = True
		self.verify = True
		self.proxies = None
		self.thread_num = None
		self.save_dir = None
		self.force_http = False
		self.main()
	
	def _get_logger(self, name, record = False):
		'''获取Logger'''
		if record:
			logger = setup_logger(name, logfile=self.logfile, formatter=RECORD_FORMAT, disableStderrLogger=True)
		else:
			logger = setup_logger(name, formatter=LOG_FORMAT)
		return logger

	def _get_pic_list(self, page):
		'''请求图片列表API'''
		url = 'https://yande.re/post.json?limit=100&page=%d&tags=%s' % (page, self.tags)
		return loads(get(url, verify=self.verify, proxies=self.proxies).text)

	def _path(self, pic):
		'''根据图片元数据和保存位置生成对应路径'''
		return join(self.save_dir, '%d.%s' % (pic['id'], pic['file_ext']))

	def _get_size(self, pic):
		'''获取文件大小 用于检查是否下载完了'''
		return getsize(self._path(pic))

	def _convert(self, size):
		'''转换为人类可读单位'''
		# 参考: https://blog.csdn.net/mp624183768/article/details/84892999
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

	@contextmanager
	def _redirect_tqdm(self):
		'''标准输出及错误重定向到进度条'''
		# 参考: https://github.com/tqdm/tqdm#redirecting-writing
		orig_out_err = sys.stdout, sys.stderr
		try:
			sys.stdout, sys.stderr = map(DummyTqdmFile, orig_out_err)
			yield orig_out_err[0]
		# Relay exceptions
		except Exception as exc:
			raise exc
		# Always restore sys.stdout/err if necessary
		finally:
			sys.stdout, sys.stderr = orig_out_err

if __name__ == '__main__':
	Application()
