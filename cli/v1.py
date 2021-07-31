"""
cli.v1 - 控制台UI库 第一版 不支持多线程
许可证: GNU General Public License v3
"""

from traceback import format_exc

from colorama import Fore, Back, Style, init as colorama_init

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
	CONFIRM = Fore.BLACK + Back.YELLOW
	NO = Fore.LIGHTWHITE_EX + Back.LIGHTBLACK_EX
	ARROW = Fore.LIGHTWHITE_EX
	RIGHT = Fore.LIGHTWHITE_EX + Back.GREEN
	END = Style.RESET_ALL


COLORAMA_INITED = False


def init():
	global COLORAMA_INITED
	if not COLORAMA_INITED:
		colorama_init(True)
		COLORAMA_INITED = True


def deinit():
	"""向后兼容cli2"""
	return None


class UIPrinter(InternalColors):
	"""
	基础用户交互接口
	queue: 向后兼容cli2
	"""

	def __init__(self, name):
		global COLORAMA_INITED
		if not COLORAMA_INITED:
			colorama_init(True)
			COLORAMA_INITED = True
		self.cprint = lambda prompt, msg, no_new_line=False: print(
			prompt + f'{self.CAPTION} {name}:{self.END}', msg, end='' if no_new_line else None)

	def print(self, msg, no_new_line=False):
		"""一般消息"""
		self.cprint(f'{self.PRINT}[ ]', msg, no_new_line)

	def note(self, msg, no_new_line=False):
		"""提示"""
		self.cprint(f'{self.NOTE}[*]', msg, no_new_line)

	def wait(self, msg, no_new_line=False):
		"""请稍候"""
		self.cprint(f'{self.WAIT}[.]', msg, no_new_line)

	def succ(self, msg, no_new_line=False):
		"""成功"""
		self.cprint(f'{self.SUCC}[+]', msg, no_new_line)

	def warn(self, msg, no_new_line=False):
		"""警告"""
		self.cprint(f'{self.WARN}[!]', msg, no_new_line)

	def fail(self, msg, no_new_line=False):
		"""错误"""
		self.cprint(f'{self.FAIL}[-]', msg, no_new_line)

	def ask(self, msg, no_new_line=True):
		"""一般询问"""
		self.cprint(f'{self.ASK}[?]', msg, no_new_line)

	def no(self, msg, no_new_line=False):
		"""操作未完成"""
		self.cprint(f'{self.NO}[=]', msg, no_new_line)

	def confirm(self, msg, no_new_line=True):
		"""确认"""
		self.cprint(f'{self.CONFIRM}[?]', msg, no_new_line)

	def up(self, msg, no_new_line=False):
		self.cprint(f'{self.ARROW}[^]', msg, no_new_line)

	def down(self, msg, no_new_line=False):
		self.cprint(f'{self.ARROW}[v]', msg, no_new_line)

	def left(self, msg, no_new_line=False):
		self.cprint(f'{self.ARROW}[<]', msg, no_new_line)

	def right(self, msg, no_new_line=False):
		self.cprint(f'{self.RIGHT}[>]', msg, no_new_line)

	def x(self, msg, no_new_line=False):
		self.cprint(f'{self.ARROW}[X]', msg, no_new_line)

	def ex(self, msg, no_new_line=False):
		"""带调试信息的错误"""
		self.cprint(f'{self.FAIL}[-]', f'{msg}\n{format_exc()}', no_new_line)
