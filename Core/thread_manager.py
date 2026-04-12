"""
线程管理器 - 统一管理后台线程
"""
import threading
from typing import Dict, Optional, Callable, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, Future


class ThreadManager:
    """
    线程管理器
    提供线程生命周期管理、取消机制、状态追踪等功能
    """
    
    _threads: Dict[str, threading.Thread] = {}
    _cancel_events: Dict[str, threading.Event] = {}
    _futures: Dict[str, Future] = {}
    _executor: Optional[ThreadPoolExecutor] = None
    _max_workers: int = 4
    
    @classmethod
    def start_thread(cls,
                     name: str,
                     target: Callable,
                     args: Tuple = (),
                     kwargs: Dict = None,
                     daemon: bool = True,
                     with_cancel_event: bool = False) -> Optional[threading.Thread]:
        """
        启动一个命名线程
        
        :param name: 纚程名称
        :param target: 目标函数
        :param args: 函数参数
        :param kwargs: 函数关键字参数
        :param daemon: 是否为守护线程
        :param with_cancel_event: 是否创建取消事件
        :return: 线程对象或 None
        """
        if kwargs is None:
            kwargs = {}
        
        if name in cls._threads and cls._threads[name].is_alive():
            cls.cancel(name)
            cls.wait(name, timeout=1.0)
        
        cancel_event = None
        if with_cancel_event:
            cancel_event = threading.Event()
            cls._cancel_events[name] = cancel_event
            kwargs['cancel_event'] = cancel_event
        
        thread = threading.Thread(
            target=target,
            args=args,
            kwargs=kwargs,
            daemon=daemon,
            name=name
        )
        cls._threads[name] = thread
        thread.start()
        
        return thread
    
    @classmethod
    def start_scan(cls,
                   target: Callable,
                   args: Tuple = (),
                   kwargs: Dict = None,
                   name: str = "scan") -> threading.Event:
        """
        启动扫描线程（带取消事件）
        
        :param target: 目标函数
        :param args: 函数参数
        :param kwargs: 函数关键字参数
        :param name: 线程名称
        :return: 取消事件对象
        """
        if kwargs is None:
            kwargs = {}
        
        if name in cls._threads and cls._threads[name].is_alive():
            cls.cancel(name)
            cls.wait(name, timeout=0.5)
        
        cancel_event = threading.Event()
        cls._cancel_events[name] = cancel_event
        kwargs['cancel_event'] = cancel_event
        
        thread = threading.Thread(
            target=target,
            args=args,
            kwargs=kwargs,
            daemon=True,
            name=name
        )
        cls._threads[name] = thread
        thread.start()
        
        return cancel_event
    
    @classmethod
    def start_generate(cls,
                       target: Callable,
                       args: Tuple = (),
                       kwargs: Dict = None,
                       name: str = "generate") -> threading.Thread:
        """
        启动生成线程
        
        :param target: 目标函数
        :param args: 函数参数
        :param kwargs: 函数关键字参数
        :param name: 线程名称
        :return: 线程对象
        """
        return cls.start_thread(name, target, args, kwargs, daemon=True)
    
    @classmethod
    def cancel(cls, name: str) -> None:
        """
        取消指定线程
        
        :param name: 线程名称
        """
        if name in cls._cancel_events:
            cls._cancel_events[name].set()
    
    @classmethod
    def is_running(cls, name: str) -> bool:
        """
        检查线程是否正在运行
        
        :param name: 线程名称
        :return: 是否正在运行
        """
        if name in cls._threads:
            return cls._threads[name].is_alive()
        return False
    
    @classmethod
    def wait(cls, name: str, timeout: Optional[float] = None) -> bool:
        """
        等待线程结束
        
        :param name: 线程名称
        :param timeout: 等待超时时间（秒）
        :return: 线程是否已结束
        """
        if name in cls._threads:
            cls._threads[name].join(timeout)
            return not cls._threads[name].is_alive()
        return True
    
    @classmethod
    def get_cancel_event(cls, name: str) -> Optional[threading.Event]:
        """
        获取线程的取消事件
        
        :param name: 线程名称
        :return: 取消事件对象或 None
        """
        return cls._cancel_events.get(name)
    
    @classmethod
    def cleanup_finished(cls) -> None:
        """
        清理已结束的线程
        """
        finished_threads = []
        for name, thread in cls._threads.items():
            if not thread.is_alive():
                finished_threads.append(name)
        
        for name in finished_threads:
            cls._threads.pop(name, None)
            cls._cancel_events.pop(name, None)
            cls._futures.pop(name, None)
    
    @classmethod
    def cancel_all(cls) -> None:
        """
        取消所有线程
        """
        for name in cls._cancel_events:
            cls._cancel_events[name].set()
    
    @classmethod
    def wait_all(cls, timeout: Optional[float] = None) -> None:
        """
        等待所有线程结束
        """
        for name, thread in cls._threads.items():
            thread.join(timeout)
    
    @classmethod
    def shutdown(cls) -> None:
        """
        关闭线程管理器
        """
        cls.cancel_all()
        cls.wait_all(timeout=2.0)
        cls._threads.clear()
        cls._cancel_events.clear()
        cls._futures.clear()
        
        if cls._executor:
            cls._executor.shutdown(wait=False)
            cls._executor = None
    
    @classmethod
    def get_active_count(cls) -> int:
        """
        获取活跃线程数量
        """
        return sum(1 for t in cls._threads.values() if t.is_alive())
    
    @classmethod
    def get_thread_names(cls) -> list:
        """
        获取所有线程名称
        """
        return list(cls._threads.keys())
    
    @classmethod
    def init_executor(cls, max_workers: int = 4) -> None:
        """
        初始化线程池执行器
        
        :param max_workers: 最大工作线程数
        """
        cls._max_workers = max_workers
        cls._executor = ThreadPoolExecutor(max_workers=max_workers)
    
    @classmethod
    def submit_task(cls, 
                    name: str,
                    target: Callable,
                    args: Tuple = (),
                    kwargs: Dict = None) -> Optional[Future]:
        """
        提交任务到线程池
        
        :param name: 任务名称
        :param target: 目标函数
        :param args: 函数参数
        :param kwargs: 函数关键字参数
        :return: Future 对象或 None
        """
        if cls._executor is None:
            cls.init_executor()
        
        if kwargs is None:
            kwargs = {}
        
        future = cls._executor.submit(target, *args, **kwargs)
        cls._futures[name] = future
        return future