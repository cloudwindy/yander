# 许可: GNU General Public License v3

from atexit          import register
from traceback       import format_exc
from multiprocessing import Process, Manager

from colorama import Fore, Back, Style, init as colorma_init

__author__ = 'cloudwindy'

class _InternalColors:
    '''
    内部颜色组
    '''
    CAPTION = Style.RESET_ALL + Fore.LIGHTBLACK_EX
    PRINT = Style.NORMAL
    NOTE = Fore.LIGHTBLUE_EX
    WAIT = Fore.LIGHTBLACK_EX
    SUCC = Fore.LIGHTGREEN_EX
    WARN = Fore.BLACK + Back.YELLOW
    FAIL = Fore.LIGHTWHITE_EX + Back.RED
    ASK = Fore.WHITE + Back.BLUE
    CONFIRM = Fore.LIGHTRED_EX + Back.YELLOW
    NO = Fore.LIGHTWHITE_EX + Back.LIGHTBLACK_EX
    END = Style.RESET_ALL

GLOBAL_QUEUE = None

def init():
    '''自动deinit 无需手动执行'''
    colorma_init(autoreset=True)
    global GLOBAL_QUEUE
    GLOBAL_QUEUE = Manager().Queue()
    UIManager().start()
    register(deinit)

def deinit():
    GLOBAL_QUEUE.put((None, None, True))

class UIManager(Process):
    '''
    交互接口管理器
    '''

    def __init__(self):
        Process.__init__(self)
        global GLOBAL_QUEUE
        self.queue = GLOBAL_QUEUE
    def run(self):
        while True:
            msg, no_new_line, stop = self.queue.get()
            if stop:
                return
            print(''.join(msg if isinstance(msg, str) else ''.join(msg)), end='' if no_new_line else None)


class UIPrinter(_InternalColors):
    '''
    基础用户交互接口
    '''
    def __init__(self, name):
        self.name = name
    def qprint(self, prompt, msg, no_new_line=False):
        '''统一输出 请勿直接调用'''
        GLOBAL_QUEUE.put((
            (*prompt, ' ', self.CAPTION, self.name, ': ', self.END, msg), no_new_line, False))
    def print(self, msg, no_new_line=False):
        '''一般消息'''
        self.qprint((self.PRINT, '[ ] '), msg, no_new_line)
    def note(self, msg, no_new_line=False):
        '''提示'''
        self.qprint((self.NOTE, '[*] '), msg, no_new_line)
    def wait(self, msg, no_new_line=False):
        '''请稍候'''
        self.qprint((self.WAIT, '[.] '), msg, no_new_line)
    def succ(self, msg, no_new_line=False):
        '''成功'''
        self.qprint((self.SUCC, '[+] '), msg, no_new_line)
    def no(self, msg, no_new_line=False):
        '''操作未完成'''
        self.qprint((self.NO, '[=] '), msg, no_new_line)
    def warn(self, msg, no_new_line=False):
        '''警告'''
        self.qprint((self.WARN, '[!] '), msg, no_new_line)
    def fail(self, msg, no_new_line=False):
        '''错误'''
        self.qprint((self.FAIL, '[-] '), msg, no_new_line)
    def ask(self, msg, no_new_line=True):
        '''一般询问'''
        self.qprint((self.ASK, '[?] '), msg, no_new_line)
    def confirm(self, msg, no_new_line=True):
        '''确认询问'''
        self.qprint((self.CONFIRM, '[?] '), msg, no_new_line)
    def ex(self, msg):
        '''带调试信息的错误'''
        self.qprint((self.FAIL, '[-] '), (msg, '\n', format_exc()))

class UILogger(UIPrinter):
    '''
    兼容logging库标准接口
    '''
    def __init__(self, name):
        UIPrinter.__init__(self, name)
        self.debug     = self.print
        self.info      = self.note
        self.warning   = self.warn
        self.error     = self.fail
        self.fatal     = self.fail
        self.critical  = self.fail
        self.exception = self.ex
