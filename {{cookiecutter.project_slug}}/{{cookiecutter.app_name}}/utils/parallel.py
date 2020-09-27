# coding: utf-8

"""
Parallelization tools based on joblib, and tqdm for progress
"""


from multiprocessing import cpu_count
import contextlib
import joblib

from .progress import tqdm, HAS_TQDM


def get_njobs(n: int=None, default_setaside: int=2):
    if n is None:
        n = cpu_count() - default_setaside
    elif n < 0:
        n = cpu_count() + n
    return max(1, n)


class ParallelEnvironment:
    def __init__(self, func: callable):
        self.func = func
        self._prepared = False

    def prepare_env(self):
        pass

    def __call__(self, x, *args, **kwargs):
        if not self._prepared:
            self.prepare_env()
            self._prepared = True
        return self.func(x, *args, **kwargs)


@contextlib.contextmanager
def tqdm_joblib(iterable=None, **kw):
    """Context manager to patch joblib to report into tqdm progress bar given as argument
    
    Usage:
        >>> with tqdm_joblib(total=200) as pbar:
        >>>     Parallel(n_jobs=2)(delayed(func)(args) for i in range(200))
    
    source: https://stackoverflow.com/a/58936697
    """
    pbar = tqdm(iterable, **kw)

    class TqdmBatchCompletionCallback:
        def __init__(self, time, index, parallel):
            self.index = index
            self.parallel = parallel

        def __call__(self, index):
            pbar.update()
            if self.parallel._original_iterator is not None:
                self.parallel.dispatch_next()

    old_batch_callback = joblib.parallel.BatchCompletionCallBack
    joblib.parallel.BatchCompletionCallBack = TqdmBatchCompletionCallback
    try:
        yield pbar
    finally:
        joblib.parallel.BatchCompletionCallBack = old_batch_callback
        pbar.close()


def parallelize(func: callable, iterable, func_args: tuple=None, func_kwargs: dict=None, njobs=None, no_progress=False, **pbar_kw):
    """
    parallelize a function, distributing calls to multiple processes
    """
    if func_args is None:
        func_args = ()
    if func_kwargs is None:
        func_kwargs = {}
    njobs = get_njobs(njobs)

    if 'total' not in pbar_kw:
        try:
            n = len(iterable)
            pbar_kw['total'] = n
        except TypeError:
            pass

    delayed = joblib.delayed

    if no_progress or not HAS_TQDM:
        res = joblib.Parallel(n_jobs=njobs)(
            delayed(func)(x, *func_args, **func_kwargs)
            for x in iterable
        )
    else:
        with tqdm_joblib(**pbar_kw):
            res = joblib.Parallel(n_jobs=njobs)(
                delayed(func)(x, *func_args, **func_kwargs)
                for x in iterable
            )
    return res
