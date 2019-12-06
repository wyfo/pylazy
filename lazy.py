from contextvars import ContextVar
from functools import partial, wraps
from inspect import iscoroutinefunction, signature
from typing import Any, Callable, Dict, Tuple, TypeVar, overload

Func = TypeVar("Func", bound=Callable)

CacheKey = Tuple[Any, ...]
CacheDict = Dict[CacheKey, Any]

ctx_cache: ContextVar[Dict[Callable, CacheDict]] = \
    ContextVar("pylazy_context_cache")  # ContextVar must be globally defined
ctx_cache.set({})


def args_to_key(parameters, args, kwargs) -> CacheKey:
    return (*args, *(
        kwargs.get(param.name, param.default)
        for param in (*parameters.values(),)[len(args):]
    ))


@overload
def lazy(func: Func) -> Func:
    ...


@overload
def lazy(*, global_: bool = False) -> Callable[[Func], Func]:
    ...


def lazy(func: Func = None, *, global_: bool = False):  # type: ignore
    if func is None:
        return partial(lazy, global_=global_)
    params = signature(func).parameters
    if global_:
        cache: CacheDict = {}
        if iscoroutinefunction(func):
            async def wrapper(*args, **kwargs):
                key = args_to_key(params, args, kwargs)
                if key not in cache:
                    cache[key] = await func(*args, **kwargs)
                return cache[key]
        else:
            def wrapper(*args, **kwargs):
                key = args_to_key(params, args, kwargs)
                if key not in cache:
                    cache[key] = func(*args, **kwargs)
                return cache[key]
    else:
        ctx_cache.get()[func] = {}
        if iscoroutinefunction(func):
            async def wrapper(*args, **kwargs):
                key = args_to_key(params, args, kwargs)
                cache: CacheDict = ctx_cache.get()[func]
                if key in cache:
                    return cache[key]
                tmp = await func(*args, **kwargs)
                ctx_cache.set({**ctx_cache.get(), func: {**cache, key: tmp}})
                return tmp

        else:
            def wrapper(*args, **kwargs):
                key = args_to_key(params, args, kwargs)
                cache: CacheDict = ctx_cache.get()[func]
                if key in cache:
                    return cache[key]
                tmp = func(*args, **kwargs)
                ctx_cache.set({**ctx_cache.get(), func: {**cache, key: tmp}})
                return tmp
    return wraps(func)(wrapper)


def glazy(func: Func) -> Func:
    return lazy(global_=True)(func)
