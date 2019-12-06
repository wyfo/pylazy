from asyncio import gather
from random import random

from pytest import mark

from lazy import glazy, lazy


def test_basic():
    @lazy
    def func() -> float:
        return random()

    assert func() == func()


def test_lazy_lambda():
    func = lazy(lambda: random())
    assert func() == func()


@mark.asyncio
async def test_global():
    @lazy
    async def afunc() -> float:
        return random()

    context_res = await gather(afunc(), afunc())
    assert context_res[0] != context_res[1]

    @glazy
    async def gafunc() -> float:
        return random()

    context_res = await gather(gafunc(), gafunc())
    assert context_res[0] == context_res[1]
