#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:47
@Author  : alexanderwu
@File    : test_environment.py
"""

import pytest
from pathlib import Path

from metagpt.actions import UserRequirement
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.manager import Manager
from metagpt.roles import Architect, ProductManager, Role
from metagpt.schema import Message


serdeser_path = Path(__file__).absolute().parent.joinpath("../data/serdeser_storage")


@pytest.fixture
def env():
    return Environment()


def test_add_role(env: Environment):
    role = ProductManager(name="Alice",
                          profile="product manager",
                          goal="create a new product",
                          constraints="limited resources")
    env.add_role(role)
    assert env.get_role(role.profile) == role


def test_get_roles(env: Environment):
    role1 = Role(name="Alice",
                 profile="product manager",
                 goal="create a new product",
                 constraints="limited resources")
    role2 = Role(name="Bob",
                 profile="engineer",
                 goal="develop the new product",
                 constraints="short deadline")
    env.add_role(role1)
    env.add_role(role2)
    roles = env.get_roles()
    assert roles == {role1.profile: role1, role2.profile: role2}


@pytest.mark.asyncio
async def test_publish_and_process_message(env: Environment):
    product_manager = ProductManager(name="Alice",
                                     profile="Product Manager",
                                     goal="做AI Native产品",
                                     constraints="资源有限")
    architect = Architect(name="Bob",
                          profile="Architect",
                          goal="设计一个可用、高效、较低成本的系统，包括数据结构与接口",
                          constraints="资源有限，需要节省成本")

    env.add_roles([product_manager, architect])
    env.set_manager(Manager())
    env.publish_message(Message(role="User", content="需要一个基于LLM做总结的搜索引擎", cause_by=UserRequirement))

    await env.run(k=2)
    logger.info(f"{env.history=}")
    assert len(env.history) > 10
