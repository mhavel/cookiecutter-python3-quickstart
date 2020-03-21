# coding=utf-8

"""
Logging tools
"""

import os
from pathlib import Path
import logging
import logging.handlers
from logging import Logger


PKG_NAME_ = Path(__file__).parent.parent.name


logging.captureWarnings(True)
logging.addLevelName(25, 'PROGRESS')


def get_logger(name: str, filename: str=None, console: bool=True, **kwargs):
    """
    Return a logger, with a number of handlers attached to it (file and/or console

    Args:
        name (str): name of the logger
        filename (str): if provided, create a Rotating File Handler with given file name
        console (bool=True): if True, create a console handler
        **kwargs: options

    Keyword Args (for `filename`, file handler):
        root (str): if given, used as the parent directory for `filename` (default: .)
        file_max_bytes (int=5e6): maximum size per file, in Bytes (octets)
        file_backup_count (int=5): number of files kept in the rotation
        file_level (str|int='DEBUG'): logging level for the file handler
        file_formatter (str='%(asctime)s - %(name)-18s: %(levelname)-8s %(message)s'): format of the message

    Keyword Args (for `console`, console handler):
        console_level (str='DEBUG'): logging level for the console handler
        console_formatter (str='%(name)-18s: %(levelname)-8s %(message)s'): format of the message

    Returns:
        logger (logging.Logger): the logger
    """
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        # do not add new handlers if already some defined
        return logger

    logger.setLevel(logging.INFO)

    # -- file log --
    if filename is not None:
        # root = kwargs.pop('root', os.getcwd())
        # if not os.path.isdir(root):
        #     os.makedirs(root)
        # fh = logging.handlers.RotatingFileHandler(os.path.join(root, filename),
        #                                           maxBytes=kwargs.pop('file_max_bytes', int(5e6)),
        #                                           backupCount=kwargs.pop('file_backup_count', 5))
        # fh.setLevel(getattr(logging, kwargs.pop('file_level', 'DEBUG')))
        # formatter = logging.Formatter(kwargs.pop('file_formatter',
        #                                          '%(asctime)s - %(name)-18s: %(levelname)-8s %(message)s'))
        # fh.setFormatter(formatter)
        # logger.addHandler(fh)
        logger.addHandler(file_handler(filename, **kwargs))

    # -- console log --
    if console:
        # console = logging.StreamHandler()
        # console.setLevel(getattr(logging, kwargs.pop('console_level', 'DEBUG')))
        # formatter = logging.Formatter(kwargs.pop('console_formatter', '%(name)-18s: %(levelname)-8s %(message)s'))
        # console.setFormatter(formatter)
        # logger.addHandler(console)
        logger.addHandler(console_handler(**kwargs))

    return logger


def file_handler(filename: str, root: str=None, file_max_bytes: int=5e6, file_backup_count: int=5,
                 file_level='DEBUG', file_formatter='%(asctime)s - %(name)-18s: %(levelname)-8s %(message)s',
                 **kwargs):
    if root is None:
        root = os.getcwd()
    elif not os.path.isdir(root):
        os.makedirs(root)
    fh = logging.handlers.RotatingFileHandler(os.path.join(root, filename),
                                              maxBytes=int(file_max_bytes),
                                              backupCount=file_backup_count)
    fh.setLevel(getattr(logging, file_level))
    formatter = logging.Formatter(file_formatter)
    fh.setFormatter(formatter)
    return fh


def console_handler(console_level='DEBUG', console_formatter='%(name)-18s: %(levelname)-8s %(message)s', **kwargs):
    console = logging.StreamHandler()
    console.setLevel(getattr(logging, console_level))
    formatter = logging.Formatter(console_formatter)
    console.setFormatter(formatter)
    return console


def get_sub_logger(sub_name, filename=None, **kwargs):
    """Same as `get_logger` function but makes sure the logger has package's name for its root"""
    prefix = PKG_NAME_ + '.'
    if sub_name.lower().startswith(prefix.lower()):
        name = prefix + sub_name[len(prefix):]
    else:
        name = prefix + sub_name

    return get_logger(name, filename=filename, **kwargs)


def set_level(x: Logger, glob=None, logger=None, handlers=None, handler_types: dict=None):
    """
    Modify the logging level of `x`

    Args:
        x (Logger): the logger
        glob (str|int=None): the logging level for both the logger and the handlers
        logger (str|int=None): the logging level only for the logger
        handlers (str|int=None): the logging level for all the handlers
        handler_types (dict=None): the logging level for handlers, per type/class

    Returns:
        x (Logger): the logger
    """
    if glob is not None:
        logger = handlers = glob

    if logger is not None:
        x.setLevel(logger)

    if handlers is not None:
        for h in x.handlers:
            h.setLevel(handlers)

    if handler_types is not None:
        h = x.handlers
        for tc, lev in handler_types.items():
            tcl = tc.lower()
            if isinstance(tc, str):
                if tcl.startswith('file'):
                    for _ in h:
                        if 'file' in _.__class__.__name__.lower():
                            _.setLevel(lev)
                if tcl.startswith('console') or tcl.startswith('stream'):
                    for _ in h:
                        if 'stream' in _.__class__.__name__.lower():
                            _.setLevel(lev)
            else:
                assert isinstance(tc, logging.Handler), '`handler_types` keys must be str or Handler instances'
                for _ in h:
                    if isinstance(_, tcl):
                        _.setLevel(lev)

    return x


class LoggingContext:
    """
    Usage:
        >>> log1 = get_logger('logger_1')
        >>> log2 = get_logger('logger_2')
        >>> with LoggingContext(log1, log2):
        >>>     log1.info('message with modified logger (level, handlers, filters, ...)')
        >>>     log2.debug(...)
        >>> log1.info('message with original logger config')
    """
    def __init__(self, *loggers: Logger, level: (int, str, dict, tuple, list)=None,
                 handlers: (logging.Handler, tuple, list)=None,
                 filters: (logging.Filter, str, tuple, list)=None, close: bool=True):
        self.loggers = loggers
        self.level = level
        self.handlers = [handlers] if isinstance(handlers, logging.Handler) else handlers
        if filters is not None:
            if isinstance(filters, str):
                filters = [logging.Filter(filters)]
            elif isinstance(filters, logging.Filter) or callable(filters):
                filters = [filters]
            else:
                filters = [_ if isinstance(_, logging.Filter) or callable(_) else logging.Filter(_) for _ in filters]
        self.filters = filters
        self._close = close

        self.old_levels = [{'logger': _l.level, 'handlers': [_.level for _ in _l.handlers]} for _l in loggers]

    @property
    def levels(self):
        return [{'logger': _l.level, 'handlers': [_.level for _ in _l.handlers]} for _l in self.loggers]

    def enter(self):
        return self.__enter__()

    def close(self):
        return self.__exit__(None, None, None)

    def __enter__(self):
        level = self.level
        handlers = self.handlers
        filters = self.filters
        for logger in self.loggers:
            if level is not None:
                if isinstance(level, dict):
                    set_level(logger, **level)
                elif isinstance(level, (tuple, list)):
                    set_level(logger, *level)
                else:
                    logger.setLevel(level)
            if handlers is not None:
                for h in handlers:
                    logger.addHandler(h)
            if filters is not None:
                for f in filters:
                    logger.addFilter(f)
        return self

    def __exit__(self, et, ev, tb):
        filters = self.filters
        handlers = self.handlers
        close = self._close
        for logger, old_level in zip(self.loggers, self.old_levels):

            if filters is not None:
                for f in filters:
                    logger.removeFilter(f)
            if handlers is not None:
                for h in handlers:
                    logger.removeHandler(h)
                    if close:
                        h.close()
            if self.level is not None:
                logger.setLevel(old_level['logger'])
                for h, lh in zip(logger.handlers, old_level['handlers']):
                    h.setLevel(lh)
        # implicit return of None => don't swallow exceptions
