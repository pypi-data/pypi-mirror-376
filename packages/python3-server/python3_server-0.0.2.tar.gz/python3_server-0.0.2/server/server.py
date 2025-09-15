import urllib3
import functools
import platform
import subprocess
from log import log

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def enter_and_leave_function(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if args:
            if kwargs:
                log.info(f"begin to run function {func.__name__},args is {args},kwargs is {kwargs}")
            else:
                log.info(f"begin to run function {func.__name__},args is {args}")
        else:
            if kwargs:
                log.info(f"begin to run function {func.__name__},kwargs is {kwargs}")
            else:
                log.info(f"begin to run function {func.__name__}")
        try:
            result = func(*args, **kwargs)
            log_str=f"finish run function {func.__name__},result type is {type(result)}, and result is {result}"
            log.info(log_str)
            return result
        except Exception as e:
            log.error(f"failed to run functon {func.__name__} error message is : {e}")
            raise e
    return wrapper

class ExecResult:
    def __init__(self,stdout,stderr,exit_code):
        self.stdout=stdout
        self.stderr=stderr
        self.exit_code=exit_code

class Server():
    def __init__(self,home="/home/my_home"):
        self.__platform = platform.system()
        if self.__platform == "linux":
            log.info(f"Current platform is {self.__platform}.")
        else:
            raise RuntimeError(f"Currently do not support {self.__platform} only support linux.")
        try:
            rs=self.exec_command(f"mkdir -p {home}")
            if rs.exit_code != 0:
                raise RuntimeError(f"failed to create home directory {home}, error message is {rs.stderr}")
            self.__home=home
        except Exception as e:
            log.error(f"failed to create home directory {home}, error message is {e}")
            raise e

    @enter_and_leave_function
    def exec_command(self, command):
        log.info(f"begin to exec command {command}")
        try:
            result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
            log.info(f"stdout is {result.stdout}, stderr is {result.stderr}, exit_code is {result.returncode}")
            rs = ExecResult(stdout=result.stdout, stderr=result.stderr, exit_code=result.returncode)
            return rs
        except subprocess.CalledProcessError as e:
            log.warning(f"failed to run command {command},stderr is {e.stderr}, exit_code is {e.returncode}")
            rs = ExecResult(stdout=e.stdout, stderr=e.stderr, exit_code=e.returncode)
            return rs