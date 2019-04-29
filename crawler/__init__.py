"""
Yande.re Crawler - A crawler to get pictures automatically
from Yande.re.
"""
from os                    import makedirs
from os.path               import exists
from sys                   import maxsize
from time                  import time, sleep
from json                  import loads
from logging               import getLogger
from hashlib               import md5
from threading             import Thread
from threading             import enumerate as enum
from http.client           import IncompleteRead
from urllib.error          import HTTPError
from urllib.parse          import urlencode
from urllib.request        import urlopen
from multiprocessing.dummy import Pool as ThreadPool

__author__ = 'cloudwindy'
__version__ = '1.8'

__all__ = ['Crawler']

class Crawler:
    def __init__(self, page_list, tags, except_tags, thread_num, save_dir):
        self.page_list = page_list
        self.tags = tags
        self.except_tags = except_tags
        self.thread_num = thread_num
        self.save_dir = save_dir
        self.log = getLogger('MainThread')
        self.log.info('Yande.re Crawler v1.8 by cloudwindy')

    def run(self):
        try:
            pool = ThreadPool(self.thread_num)
            if not exists(self.save_dir):
                makedirs(self.save_dir)
            for page in self.page_list:
                self.log.info('Working on page %d.' % page)
                param = {
                    'limit': 100,
                    'page': page,
                    'tags': self.tags
                }
                pic_list = loads(urlopen('http://92.222.110.68/post.json?' + urlencode(param)).read().decode())
                if len(pic_list) <= 0:
                    self.log.info('Page was empty. Exiting.')
                    break
                i = 0
                while i < len(pic_list):
                    v = pic_list[i]
                    pic_list[i]['save_path'] = '%s%d.%s' % (self.save_dir, v['id'], v['file_ext'])
                    if self.check(v):
                        pic_list.remove(v)
                    else:
                        i += 1
                self.log.info('Page contains %d downloadable pictures' % len(pic_list))
                pool.map(CrawlerTask, pic_list)
        except KeyboardInterrupt:
            self.log.info('Interrupted by user. Exiting.')
        except Exception:
            self.log.exception('Failed due to unknown error. The details are as follows:')
        pool.close()
        pool.join()
        self.log.info('Main thread exited')
    
    def check(self, pic):
        return exists(pic['save_path']) or self.tags.find(self.except_tags) != -1

class CrawlerTask:
    def __init__(self, pic):
        self.tags = pic['tags']
        self.url = pic['file_url']
        self.md5 = pic['md5']
        self.file_size = pic['file_size']
        self.save_path = pic['save_path']
        self.log = getLogger('Task' + str(pic['id']))
        try:
            self.get()
            if self.check():
                self.save()
            else:
                self.__init__(pic)
        except HTTPError:
            self.log.error('Downloading failed due to network error.')
        except Exception:
            self.log.exception('Downloading failed due to unknown error. The details are as follows:')

    def get(self):
        http_response = urlopen(self.url)
        self.log.info('Downloading started. Size: %s.' % self.convert(self.file_size))
        start_time = time()
        try:
            self.pic = http_response.read()
        except IncompleteRead as e:
            self.pic = e.partial
        end_time = time()
        exec_time = end_time - start_time
        speed = len(self.pic) / exec_time # bytes / sec
        self.log.info('Downloading completed. Speed: %s/s.' % self.convert(speed))

    def check(self):
        checker = md5()
        checker.update(self.pic)
        result_md5 = checker.hexdigest()
        if result_md5 != self.md5:
            self.log.info('MD5 check failed. MD5: %s' % result_md5)
            return False
        else:
            return True

    def save(self):
        file = open(self.save_path, 'wb')
        file.write(self.pic)
        file.close()

    def convert(self, size):
        # Reference：https://blog.csdn.net/mp624183768/article/details/84892999
        kb = 1024;
        mb = kb * 1024;
        gb = mb * 1024;
        tb = gb * 1024;
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
