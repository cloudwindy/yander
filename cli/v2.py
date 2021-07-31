"""
cli.v2 - 控制台UI库 第二版 支持多线程
许可证: GNU General Public License v3
"""

from atexit          import register
from traceback       import format_exc
from multiprocessing.dummy import Process, Manager

from .v1 import UIPrinter as UIPrinterV1

from colorama import Fore, Back, Style, init as colorama_init, deinit as colorama_deinit

__author__ = 'cloudwindy'

class InternalColors:
    """
    内部颜色组
    """
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

me = UIPrinterV1('UI模块')

def init():
    """初始化UI"""
    # 初始化colorama模块
    colorama_init(autoreset=True)
    # 初始化全局队列
    GlobalQueue.init()
    # 初始化交互接口管理器
    UIManager().start()
    # 注册解初始化器
    register(deinit)
    me.succ('UI模块已成功初始化')

def deinit():
    """解初始化UI"""
    # 解初始化全局队列(和交互接口管理器)
    GlobalQueue.deinit()
    # 解初始化colorama模块
    colorama_deinit()
    me.succ('UI模块已退出')

class StopSignal(Exception):
    """停止信号"""

class GlobalQueue:
    _queue = None
    _initialized = False

    @classmethod
    def init(cls):
        cls._queue = Manager().Queue()
        cls._initialized = True
    
    @classmethod
    def deinit(cls):
        cls._queue.put((None, None, True))
        cls._initialized = False
    
    @classmethod
    def initialized(cls):
        return cls._initialized

    @classmethod
    def queue(cls):
        return cls._queue
    
    @classmethod
    def put(cls, msg, no_new_line = None):
        cls._queue.put((msg, no_new_line, False))
    
    @classmethod
    def get(cls):
        msg, no_new_line, stop = cls._queue.get()
        if stop:
            raise StopSignal
        return msg, no_new_line
    

class UIManager(Process):
    """
    交互接口管理器
    """

    def __init__(self):
        Process.__init__(self)

    def run(self):
        while True:
            try:
                msg, no_new_line = GlobalQueue.get()
                if isinstance(msg, tuple) or isinstance(msg, list):
                    msg = ''.join(msg)
                end = '\n'
                if no_new_line:
                    end = ''
                print(msg, end=end)
            except StopSignal:
                return


class UIPrinter(InternalColors):
    """
    基础用户交互接口
    """
    def __init__(self, name):
        self._cli_name = name
    def qprint(self, prompt, msg, no_new_line=False):
        """统一输出 请勿直接调用"""
        if not GlobalQueue.initialized():
            me.fail('UI模块没有被初始化 一条消息没有被显示')
            return
        GlobalQueue.put(
            (*prompt, self.END, ' ', self.CAPTION, self._cli_name, ': ', self.END, msg), no_new_line)
    def print(self, msg: str, no_new_line=False):
        """一般消息"""
        self.qprint((self.PRINT, '[ ]'), msg, no_new_line)
    def note(self, msg: str, no_new_line=False):
        """提示"""
        self.qprint((self.NOTE, '[*]'), msg, no_new_line)
    def wait(self, msg: str, no_new_line=False):
        """请稍候"""
        self.qprint((self.WAIT, '[.]'), msg, no_new_line)
    def succ(self, msg: str, no_new_line=False):
        """成功"""
        self.qprint((self.SUCC, '[+]'), msg, no_new_line)
    def no(self, msg: str, no_new_line=False):
        """操作未完成"""
        self.qprint((self.NO, '[=]'), msg, no_new_line)
    def warn(self, msg: str, no_new_line=False):
        """警告"""
        self.qprint((self.WARN, '[!]'), msg, no_new_line)
    def fail(self, msg: str, no_new_line=False):
        """错误"""
        self.qprint((self.FAIL, '[-]'), msg, no_new_line)
    def ask(self, msg: str, no_new_line=True):
        """一般询问"""
        self.qprint((self.ASK, '[?]'), msg, no_new_line)
    def confirm(self, msg: str, no_new_line=True):
        """确认询问"""
        self.qprint((self.CONFIRM, '[?]'), msg, no_new_line)
    def ex(self, msg: str):
        """带调试信息的错误"""
        self.qprint((self.FAIL, '[-]'), f'{msg}\n{format_exc()}')

class UILogger(UIPrinter):
    """
    兼容logging库标准接口
    """
    def __init__(self, name):
        UIPrinter.__init__(self, name)
        self.debug     = self.print
        self.info      = self.note
        self.warning   = self.warn
        self.error     = self.fail
        self.fatal     = self.fail
        self.critical  = self.fail
        self.exception = self.ex
