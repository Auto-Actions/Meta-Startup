#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of ExtEnv&Env

import pytest

from metagpt.environment.api.env_api import EnvAPIAbstract
from metagpt.environment.base_env import (
    Environment,
    mark_as_readable,
    mark_as_writeable,
    env_read_api_registry,
    env_write_api_registry
)


class ForTestEnv(Environment):
    value: int = 0

    @mark_as_readable
    def read_api_no_parms(self):
        return self.value

    @mark_as_readable
    def read_api(self, a: int, b: int):
        return a + b

    @mark_as_writeable
    def write_api(self, a: int, b: int):
        self.value = a + b

    @mark_as_writeable
    async def async_read_api(self, a: int, b: int):
        return a + b


@pytest.mark.asyncio
async def test_ext_env():
    env = ForTestEnv()
    assert len(env_read_api_registry) > 0
    assert len(env_write_api_registry) > 0

    _ = await env.step(EnvAPIAbstract(api_name="write_api", kwargs={"a": 5, "b": 10}))
    assert env.value == 15

    with pytest.raises(ValueError):
        await env.observe("not_exist_api")

    assert await env.observe("read_api_no_parms") == 15
    assert await env.observe(EnvAPIAbstract(api_name="read_api", kwargs={"a": 5, "b": 5})) == 10
