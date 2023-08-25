import multiprocessing
import threading

import psutil

# 检查当前活动的进程数量
active_processes = len(multiprocessing.active_children())
print(f"当前活动的进程数量: {active_processes}")

# 使用psutil获取正在运行的进程数量
# running_processes = len(psutil.process_iter())
# print(f"正在运行的进程数量: {running_processes}")

# 检查当前活动的线程数量
active_threads = len(threading.enumerate())
print(f"当前活动的线程数量: {active_threads}")
