"""
Yande.re Crawler - A crawler to get pictures automatically
from Yande.re.
"""

import ssl
from ssl                   import _create_unverified_context
from os                    import makedirs
from os.path               import exists
from sys                   import maxsize
from time                  import time, sleep
from json                  import loads
from logging               import getLogger
from hashlib               import md5
from threading             import Thread, enumerate as enum
from http.client           import IncompleteRead, RemoteDisconnected
from urllib.error          import URLError, HTTPError
from urllib.parse          import urlencode
from urllib.request        import urlopen
from multiprocessing.dummy import Pool

__author__ = 'cloudwindy'
__version__ = '1.9'

__all__ = ['Main']

# Prevent SSLError
ssl._create_default_https_context=_create_unverified_context

class Main:
    def __init__(self, page_list, tags, thread_num, save_dir):
        self.page_list = page_list
        self.tags = tags        
        self.thread_num = thread_num
        self.save_dir = save_dir
        self.log = getLogger('Main')
        self.log.info('YandeCrawler 1.9')
        if thread_num > 5:
            self.log.warning('Option thread_num is bigger than 5')
            self.log.warning('And this may cause some problems')
        if tags == '':
            self.log.warning('Option tags not specified')
            self.log.warning('Default tag is wildcard')

    def run(self):
        try:
            pool = Pool(self.thread_num)
            if not exists(self.save_dir):
                makedirs(self.save_dir)
            for page in self.page_list:
                self.log.info('Page %d: Getting metadata' % page)
                url = 'https://yande.re/post.json?limit=100&page=%d&tags=%s' % (page, self.tags)
                pic_list = loads(urlopen(url).read().decode())
                # Exit when this is the last page
                if len(pic_list) <= 0:
                    self.log.info('Page %d: Empty. Exiting' % page)
                    break
                # Sort by size, the first is the smallest
                pic_list.sort(key = lambda pic_list: pic_list['file_size'], reverse = False)
                # Fill savepath and _id
                i = 0
                while i < len(pic_list):
                    v = pic_list[i]
                    pic_list[i]['save_path'] = '%s%d.%s' % (self.save_dir, v['id'], v['file_ext'])
                    pic_list[i]['_id'] = i
                    i += 1
                # Remove duplicates
                for pic in pic_list:
                    if exists(pic['save_path']):
                        pic_list.remove(pic)
                if len(pic_list) > 0:
                    self.log.info('Page %d: Got. Total %d pics' % (page, len(pic_list)))
                    self.log.info('Page %d: Working' % page)
                    pool.map(Task, pic_list)
                self.log.info('Page %d: Done' % page)
        except KeyboardInterrupt:
            self.log.info('Interrupted by user. Exiting.')
        except HTTPError as e:
            o = e.reason
            self.log.error('HTTPError %d %s' % (o.errno, o.strerror))
        except URLError as e:
            o = e.reason
            self.log.error('URLError %d %s' % (o.errno, o.strerror))
        except Exception:
            self.log.exception('Error happens')
        pool.close()
        self.log.info('Waiting for tasks')
        pool.join()
        self.log.info('Control exited')

class Task:
    def __init__(self, pic):
        self.tags = pic['tags']
        self.url = pic['file_url']
        self.md5 = pic['md5']
        self.file_size = pic['file_size']
        self.save_path = pic['save_path']
        self.log = getLogger('T' + str(pic['_id']).rjust(3))
        try:
            self.log.info('Task start. Size: %s' % self.convert(self.file_size))
            self.get()
            if self.check():
                self.save()
            else:
                self.log.warning('Integrity check fail')
                self.__init__(pic)
            self.log.info('Task done. Speed: %s/s' % self.convert(self.speed))
        except ConnectionAbortedError as e:
            self.log.warning('Connection aborted')
            self.__init__(pic)
        except ConnectionResetError as e:
            self.log.warning('Connection reset')
            self.__init__(pic)
        except IncompleteRead as e:
            self.log.warning('Incomplete read')
            self.__init__(pic)
        except HTTPError as e:
            o = e.reason
            self.log.error('HTTPError %d %s' % (o.errno, o.strerror))
        except URLError as e:
            o = e.reason
            self.log.error('URLError %d %s' % (o.errno, o.strerror))
            self.__init__(pic)
        except Exception:
            self.log.exception('Error happens')

    def get(self):
        start_time = time()
        self.pic = urlopen(self.url).read()
        end_time = time()
        exec_time = end_time - start_time
        self.speed = len(self.pic) / exec_time # bytes / sec
        
    def check(self):
        checker = md5()
        checker.update(self.pic)
        result_md5 = checker.hexdigest()
        return result_md5 == self.md5

    def save(self):
        file = open(self.save_path, 'wb')
        file.write(self.pic)
        file.close()

    def convert(self, size):
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