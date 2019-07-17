# coding: utf-8

from functools import wraps
import inspect


# --------------
#  Base classes
# --------------
class _BaseDecorator:
    def pre_process(self, *args, **kwargs):
        return args, kwargs

    def post_process(self, o):
        return o

    def inspect_func(self, f):
        return


class DecoratorWithArguments(_BaseDecorator):
    """
    Base class to create a decorator with arguments

    You simply need to override either of `pre_process` and/or `post_process` methods.
    As their name suggests, `pre_process` will be passed the function's arguments and keywords
    so you can modify them and return them, while `post_process` will take the function's output
    and return your modified version.

    Examples:
        >>> class basic_defaults(DecoratorWithArguments):
        >>>     def __init__(self, x=1, a=1.2):
        >>>         self.x = x
        >>>         self.a = a
        >>>
        >>>     def pre_process(self, *args, **kwargs):
        >>>         a0 = (kwargs.pop('x', self.x), kwargs.pop('a', self.a))
        >>>         na = len(args)
        >>>         if na == 0:
        >>>             a = a0
        >>>         elif na == 1:
        >>>             a = args + a0[1:]
        >>>         else:
        >>>             a = args
        >>>         return a[:2], {}
        >>>
        >>> @basic_defaults(1, a=1.2)
        >>> def func(x, a):
        >>>     return x + a
        >>>
        >>> print(func(4))  # --> 5.2
        >>> print(func())   # --> 2.2
        >>> print(func(4, -1))   # --> 3
    """
    def __init__(self, *_args, **_kwargs):
        self.args = _args
        self.kwargs = _kwargs

    def __call__(self, f):
        self.inspect_func(f)

        @wraps(f)
        def wrapped_func(*args, **kwargs):
            a, kw = self.pre_process(*args, **kwargs)
            o = f(*a, **kw)
            return self.post_process(o)

        return wrapped_func


class DecoratorWithoutArguments(_BaseDecorator):
    """
    Base class to create a decorator without arguments

    You simply need to override either of `pre_process` and/or `post_process` methods.
    As their name suggests, `pre_process` will be passed the function's arguments and keywords
    so you can modify them and return them, while `post_process` will take the function's output
    and return your modified version.

    Examples:
        >>> class basic_defaults(DecoratorWithoutArguments):
        >>>     def pre_process(self, *args, **kwargs):
        >>>         a0 = (kwargs.pop('x', 1), kwargs.pop('a', 1.2))
        >>>         na = len(args)
        >>>         if na == 0:
        >>>             a = a0
        >>>         elif na == 1:
        >>>             a = args + a0[1:]
        >>>         else:
        >>>             a = args
        >>>         return a[:2], {}
        >>>
        >>> @basic_defaults
        >>> def func(x, a):
        >>>     return x + a
        >>>
        >>> print(func(4))  # --> 5.2
        >>> print(func())   # --> 2.2
        >>> print(func(4, -1))   # --> 3
    """
    def __init__(self, f):
        self.func = f
        self.inspect_func(f)

    def __call__(self, *args, **kwargs):
        a, kw = self.pre_process(*args, **kwargs)
        o = self.func(*a, **kw)
        return self.post_process(o)


# ------------------------
#  Pre-defined decorators
# ------------------------
class defaults(DecoratorWithArguments):
    """
    A decorator to define default values of a function.
    
    Works a bit like `functools.partial` but with the decorator mechanism and in a more natural way:
    values are real defaults, and can be provided at any call-time by the user (whereas `partial` will
    *always* apply the passed values to the function calls).

    Examples:
        >>> @defaults(y=1, b=2)
        >>> def func(x, y, a, b):
        >>>     return x + y - b * a
        >>>
        >>> print(func(6, 1, 0, 2))   # --> 7
        >>> print(func(6, 3, a=0.5))  # --> 8.0

        The above example would fail with `functools.partial`, as it would consider receiving multiple values
        for the argument `y`.
    """
    def inspect_func(self, f):
        sig = inspect.signature(f)
        pos_names = []
        kw_names = []
        args_name = ''
        kwargs_name = ''
        for param in sig.parameters.values():
            if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
                pos_names.append(param.name)
            elif param.kind == param.KEYWORD_ONLY:
                kw_names.append(param.name)
            elif param.kind == param.VAR_POSITIONAL:
                args_name = param.name
            elif param.kind == param.VAR_KEYWORD:
                kwargs_name = param.name
        self.pos_names = pos_names
        self.kw_names = kw_names
        self.args_name = args_name
        self.kwargs_name = kwargs_name

        self.defaults = dict(zip(self.pos_names, self.args))
        self.defaults.update(self.kwargs)
        return

    def pre_process(self, *args, **kwargs):
        kw = self.defaults.copy()
        kw.update(zip(self.pos_names, args))
        kw.update(kwargs)
        return (), kw


# ---------
#  Helpers
# ---------
def decorate(func: callable, decorator: callable, args: tuple=None, kwargs: dict=None):
    """
    Apply `decorator` to function `func`. If `args` or `kwargs` is not None, `decorator` is called with arguments.
    Therefore to force calling a decorator with empty arguments you could do: `decorate(func, decorator, args=())`

    Args:
        func (callable): the function to be decorated
        decorator (callable): the decorator
        args (tuple=None): the arguments to be passed to the decorator
        kwargs (dict=None): the keyword arguments to be passed to the decorator

    Returns:
        fdec (callable): decorated function
    """
    a = args is not None
    k = kwargs is not None
    if a or k:
        if not a:
            args = ()
        if not k:
            kwargs = {}
        return decorator(*args, **kwargs)(func)
    else:
        return decorator(func)
