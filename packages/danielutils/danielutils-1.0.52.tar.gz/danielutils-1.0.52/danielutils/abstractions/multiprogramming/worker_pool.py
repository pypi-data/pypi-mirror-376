from queue import Queue
from typing import Optional, Any, Type as t_type, Tuple as Tuple, List as List
from threading import Semaphore
from .worker import Worker
from ...reflection import get_python_version

if get_python_version() >= (3, 9):
    from builtins import type as t_type, tuple as Tuple, list as List  # type:ignore


class WorkerPool:
    """A worker pool class
    """

    def __init__(self, num_workers: int, worker_class: t_type[Worker], w_kwargs: dict, global_variables: dict) -> None:
        self.num_workers = num_workers
        self.global_variables: dict = global_variables
        self.q: Queue[Tuple[Any]] = Queue()
        self.worker_class = worker_class
        self.workers: List[Worker] = []
        self.sem = Semaphore(0)
        self.w_kwargs = w_kwargs

    def submit(self, job: Any) -> None:
        """submit a job to the pool
        the object can be anything you want as long as you use it 
        correctly in your implemented worker class

        Args:
            job (Any): job object
        """
        # we create a tuple to signal that it is indeed a job object and we haven't just got None
        # see Worker._loop
        self.q.put((job,))
        self.sem.release()

    def _acquire(self) -> Optional[Tuple[Any]]:
        """acquire a new job from the pool

        Returns:
            Optional[tuple[Any]]: optional tuple of job object
        """
        self.sem.acquire()
        if self.q.unfinished_tasks > 0:
            return self.q.get()
        return None

    def start(self) -> None:
        """starts running the pool of workers
        """
        for i in range(self.num_workers):
            w = self.worker_class(i, self, **self.w_kwargs)
            w.run()
            self.workers.append(w)

    def _notify(self) -> None:
        """a function that the worker calls after finishing processing a job object (Any)
        this function is called automatically from Worker.work()
        """
        self.q.task_done()
        if self.q.unfinished_tasks <= 0:
            self.sem.release(self.num_workers)

    def join(self) -> None:
        """
        waits for all the workers to finish and will return afterwards
        Returns:
            None
        """
        for w in self.workers:
            w.thread.join()


__all__ = [
    "WorkerPool"
]
