"""
Yande.re Crawler - A crawler to get pictures automatically
from Yande.re.
"""

import ssl
from ssl                   import _create_unverified_context
from os                    import makedirs
from os.path               import exists
from time                  import time
from json                  import loads
from logging               import getLogger
from hashlib               import md5
from http.client           import IncompleteRead
from urllib.error          import URLError, HTTPError
from urllib.request        import urlopen
from multiprocessing.dummy import Pool

__author__ = 'cloudwindy'
__version__ = '1.9'

__all__ = ['run_main']

# Prevent SSLError
ssl._create_default_https_context=_create_unverified_context

# Public functions
def run_main(page_list, tags, thread_num, save_dir):
    page_list = page_list
    tags = tags
    thread_num = thread_num
    save_dir = save_dir
    log = getLogger('Main')
    log.info('YandeCrawler %s' % __version__)
    if thread_num > 5:
        log.warning('Option thread_num is bigger than 5')
        log.warning('And this may cause some problems')
    if tags == '':
        log.info('Option tags not specified')
        log.info('Default tag is wildcard')
    try:
        pool = Pool(thread_num)
        if not exists(save_dir):
            makedirs(save_dir)
        for page in page_list:
            log.info('Page %d: Getting metadata' % page)
            url = 'https://yande.re/post.json?limit=100&page=%d&tags=%s' % (page, tags)
            pic_list = loads(urlopen(url).read().decode())
            # Exit when this is the last page
            if len(pic_list) <= 0:
                log.info('Page %d: Empty. Exiting' % page)
                break
            # Sort by size, the first is the smallest
            pic_list.sort(key = lambda pic_list: pic_list['file_size'], reverse = False)
            # Add savepath
            i = 0
            while i < len(pic_list):
                v = pic_list[i]
                pic_list[i]['save_path'] = '%s%d.%s' % (save_dir, v['id'], v['file_ext'])
                i += 1
            # Remove duplicates by savepath
            for pic in pic_list:
                if exists(pic['save_path']):
                    pic_list.remove(pic)
            # Add ID
            i = 0
            while i < len(pic_list):
                pic_list[i]['_id'] = i
                i += 1
            if len(pic_list) > 0:
                log.info('Page %d: Got. Total %d pics' % (page, len(pic_list)))
                log.info('Page %d: Working' % page)
                pool.map(get_pic, pic_list)
                log.info('Page %d: Done' % page)
    except KeyboardInterrupt:
        log.info('Interrupted by user. Exiting')
    except HTTPError as e:
        o = e.reason
        log.error('HTTPError %d %s' % (o.errno, o.strerror))
    except URLError as e:
        o = e.reason
        log.error('URLError %d %s' % (o.errno, o.strerror))
    except Exception:
        log.exception('Error happens')
    pool.close()
    log.info('Waiting for tasks')
    try:
        pool.join()
    except:
        log.warning('Exiting immediately')
        log.warning('Unsaved data droped')
    log.info('Control exited')

def get_pic(pic):
    log = getLogger('T' + str(pic['_id']).rjust(3))
    try:
        (file, speed) = _fetch_file(pic['file_url'])
        if len(file) != pic['file_size'] or _check(file, pic['md5']):
            _save(file, pic['save_path'])
            log.info('Task done. Speed: %s/s' % _convert(speed))
        else:
            log.warning('Integrity check failed')
            get_pic(pic)
    except IncompleteRead as e:
        log.warning('Incomplete read')
        get_pic(pic)
    except HTTPError as e:
        o = e.reason
        log.error('HTTPError %d %s' % (o.errno, o.strerror))
    except URLError as e:
        o = e.reason
        log.error('URLError %d %s' % (o.errno, o.strerror))
        get_pic(pic)
    except Exception:
        log.exception('Error happens')

# Private functions

def _fetch_file(url):
    start_time = time()
    file = urlopen(url).read()
    end_time = time()
    exec_time = end_time - start_time
    return file, (len(file) / exec_time) # bytes / sec

def _check(file, file_md5):
    checker = md5()
    checker.update(file)
    result_md5 = checker.hexdigest()
    return result_md5 == file_md5

def _save(file, save_path):
    file = open(save_path, 'wb')
    file.write(file)
    file.close()

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

