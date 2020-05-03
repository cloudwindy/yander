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
from ssl                   import _create_unverified_context
from sys                   import maxsize
from os                    import chdir, makedirs, remove
from os.path               import exists, join, getsize
from json                  import loads
from hashlib               import md5
from argparse              import ArgumentParser
from contextlib            import contextmanager
from multiprocessing.dummy import Pool

# 依赖安装提示
try:
	from tqdm              import tqdm
	from tqdm.contrib      import DummyTqdmFile
	from logzero           import LogFormatter, setup_logger
	from requests          import Session, get
	from requests.adapters import HTTPAdapter
except ImportError:
	print('''
严重错误: Yande.re 下载工具缺少一些必要的依赖

tqdm     - 用于显示进度
logzero  - 用于记录日志
requests - 用于发起请求

请运行以下的命令以安装这些依赖
pip3 install tqdm logzero requests
''')
	exit()

__author__ = 'cloudwindy'
__version__ = '2.2'

# 基本单位
kb = 1024
mb = 1024 * 1024
gb = 1024 * 1024 * 1024
tb = 1024 * 1024 * 1024 * 1024

stop = False
CHUNK_SIZE = 1 * kb

# 日志格式
log_format = '%(color)s[%(levelname)1.1s %(asctime)s] %(name)s:%(end_color)s %(message)s'
formatter = LogFormatter(fmt=log_format)

def main_download_mode(tags):
	log = _get_logger('主程序')
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
	stop = True
	pool.close()
	log.info('正在等待任务结束')
	try:
		pool.join()
	except KeyboardInterrupt:
		print()
		log.warning('正在强制停止全部任务')
		log.warning('当前正在下载的任务将被丢弃')
	log.info('下载工具已退出')

def main_verify_mode(tags):
	for page in range(1, maxsize):
		pic_list = _get_pic_list(page, tags)
		if len(pic_list) <= 0:
			_get_logger('页面 %d' % page).info('已到达最后一页 准备退出')
			return
		#for pic in pic_list[:]:
		#	if exists(_path(pic)):
		#		if _get_size(pic) != pic['file_size']:
		#			pic_list.remove(pic)
		with _redirect_tqdm() as orig_opt:
			for pic in tqdm(pic_list,
							file = orig_opt,
							desc = '页面 %d' % page,
							dynamic_ncols=True):
				with open(_path(pic), 'rb') as f:
					realmd5 = md5(f.read()).hexdigest()
					if realmd5 != pic['md5']:
						remove(_path(pic))
					
# 获取页面元数据
def get_page(page, pool, tags):
	log = _get_logger('页面 %d' % page)
	log.info('正在获取元数据')
	pic_list = _get_pic_list(page, tags)
	# 检测 图片数量
	if len(pic_list) <= 0:
		log.info('已到达最后一页 准备退出')
		return True
	# 移除 重复图片
	for pic in pic_list[:]:
		# 如果图片已有大小等于元数据 移出下载列表
		if exists(_path(pic)):
			if _get_size(pic) == pic['file_size']:
				pic_list.remove(pic)
	# 排序 从大到小排列
	pic_list.sort(key = lambda pic_list: pic_list['file_size'], reverse=True)
	if len(pic_list) > 0:
		log.debug('已获取元数据. 共 %d 张图片' % len(pic_list))
		log.info('下载开始')
		pool.map(get_pic, pic_list)
		log.info('下载完毕')
	else:
		log.info('已跳过')

# 下载单张图片
# 由于 Yande.re 不支持, 断点续传功能已移除
def get_pic(pic):
<<<<<<< Updated upstream
	if stop:
		return
	log = _get_logger('图片' + str(pic['id']))
	try:
		req = Session()
		req.mount('http://', HTTPAdapter(max_retries=0))
		req.mount('https://', HTTPAdapter(max_retries=0))
		res = req.get(pic['file_url'], 
					  stream=True,
					  timeout=10,
					  verify=verify,
					  proxies=proxies)
		with open(_path(pic), 'wb') as f:
			with tqdm(unit='B',
				 unit_scale=True,
				 desc='图片' + str(pic['id']),
				 total=pic['file_size'],
				 leave=False,
				 dynamic_ncols=True) as pbar:
				for chunk in res.iter_content(chunk_size=CHUNK_SIZE):
					if chunk:
						pbar.update(f.write(chunk))
					else:
						break
		return
	except Exception as e:
=======
	log = _get_logger('图片' + str(pic['id']))
	try:
		# 禁用自动重试
		req = Session()
		req.mount('http://', HTTPAdapter(max_retries=0))
		req.mount('https://', HTTPAdapter(max_retries=0))
		# 向图片地址发起请求
		res = req.get(url=pic['file_url'],
					  stream=True,
					  timeout=30,
					  verify=verify,
					  proxies=proxies)
		# HTTP 状态码检查
		res.raise_for_status()
		# 打开文件准备写入
		with open(_path(pic), 'wb') as f:
			# 配置进度条
			with tqdm(unit='B',
					  unit_scale=True,
					  #file=orig_opt,
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
		#log.info("下载完成")
	except Exception:
		# 错误重试
		log.exception('正在重试...')
>>>>>>> Stashed changes
		get_pic(pic)

# 私有方法

# 获取Logger
def _get_logger(name):
	return setup_logger(name, logfile=logfile, formatter=formatter)

<<<<<<< Updated upstream
def _get_pic_list(page, tags):
=======
# 请求图片列表API
def _get_pic_list(page):
>>>>>>> Stashed changes
	url = 'https://yande.re/post.json?limit=100&page=%d&tags=%s' % (page, tags)
	return loads(get(url, verify=verify, proxies=proxies).text)

# 根据图片元数据和保存位置生成对应路径
def _path(pic):
	return join(save_dir, '%d.%s' % (pic['id'], pic['file_ext']))
<<<<<<< Updated upstream

# 获取文件大小 用于检查是否下载完了
def _get_size(pic):
	return getsize(_path(pic))
=======
>>>>>>> Stashed changes

# 获取文件大小 用于检查是否下载完了
def _get_size(pic):
	return getsize(_path(pic))

# 转换为人类可读单位
def _convert(size):
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

<<<<<<< Updated upstream
=======
# 标准输出及错误重定向到进度条
>>>>>>> Stashed changes
@contextmanager
def _redirect_tqdm():
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

<<<<<<< Updated upstream
=======
tags = None
>>>>>>> Stashed changes
logfile = None
verify = True
proxies = None
thread_num = None
save_dir = None
<<<<<<< Updated upstream
=======
orig_opt = None
>>>>>>> Stashed changes
force_http = False
if __name__ == '__main__':
	parser = ArgumentParser(description = 'Yande.re 下载工具')
	parser.add_argument('-v',
						'--version',
					    action = 'version',
					    version = 'Yande.re 下载工具 v%s by %s' % (__version__, __author__))
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
	parser.add_argument('--verify',
						action='store_true',
						default = False,
						help = '检查文件完整性')
	args = parser.parse_args()
	log = _get_logger('初始化')
	log.info('Yande.re 下载工具')
	conf = loads(args.conf.read())
	args.conf.close()
<<<<<<< Updated upstream
	thread_num = conf['thread_num']
	save_dir = conf['save_dir']
=======
	tags = conf['tags']
	if tags == '':
		log.warning('未指定标签 默认处理所有图片')
	start = conf['start']
	thread_num = conf['thread_num']
	save_dir = conf['save_dir']
	if conf['end'] == -1:
		log.debug('程序将处理到最后一页')
		end = maxsize
	else:
		end = conf['end']
>>>>>>> Stashed changes
	if conf['log']:
		log.debug('已启用日志文件: ' + conf['log_file'])
		logfile = conf['log_file']
	if conf['no_check_certificate']:
		log.debug('已禁用 SSL 证书认证')
		verify = False
	if conf['proxy']:
		log.debug('已启用 HTTP(S) 代理: ' + conf['proxy_addr'])
		proxies = {
			'http': 'http://' + conf['proxy_addr'],
			'https': 'http://' + conf['proxy_addr']
		}
	if args.verify:
<<<<<<< Updated upstream
		main_verify_mode(conf['tags'])
	else:
		main_download_mode(conf['tags'])
=======
		main_verify_mode()
	else:
		main_download_mode()
>>>>>>> Stashed changes
