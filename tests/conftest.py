#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/1 12:10
@Author  : alexanderwu
@File    : conftest.py
"""

import asyncio
import logging
import re
from unittest.mock import Mock

import pytest

from metagpt.config import CONFIG, Config
from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.utils.git_repository import GitRepository


class Context:
    def __init__(self):
        self._llm_ui = None
        self._llm_api = LLM(provider=CONFIG.get_default_llm_provider_enum())

    @property
    def llm_api(self):
        # 1. 初始化llm，带有缓存结果
        # 2. 如果缓存query，那么直接返回缓存结果
        # 3. 如果没有缓存query，那么调用llm_api，返回结果
        # 4. 如果有缓存query，那么更新缓存结果
        return self._llm_api


@pytest.fixture(scope="package")
def llm_api():
    logger.info("Setting up the test")
    _context = Context()

    yield _context.llm_api

    logger.info("Tearing down the test")


@pytest.fixture(scope="function")
def mock_llm():
    # Create a mock LLM for testing
    return Mock()


@pytest.fixture(scope="session")
def proxy():
    pattern = re.compile(
        rb"(?P<method>[a-zA-Z]+) (?P<uri>(\w+://)?(?P<host>[^\s\'\"<>\[\]{}|/:]+)(:(?P<port>\d+))?[^\s\'\"<>\[\]{}|]*) "
    )

    async def pipe(reader, writer):
        while not reader.at_eof():
            writer.write(await reader.read(2048))
        writer.close()

    async def handle_client(reader, writer):
        data = await reader.readuntil(b"\r\n\r\n")
        print(f"Proxy: {data}")  # checking with capfd fixture
        infos = pattern.match(data)
        host, port = infos.group("host"), infos.group("port")
        port = int(port) if port else 80
        remote_reader, remote_writer = await asyncio.open_connection(host, port)
        if data.startswith(b"CONNECT"):
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        else:
            remote_writer.write(data)
        await asyncio.gather(pipe(reader, remote_writer), pipe(remote_reader, writer))

    server = asyncio.get_event_loop().run_until_complete(asyncio.start_server(handle_client, "127.0.0.1", 0))
    return "http://{}:{}".format(*server.sockets[0].getsockname())


# see https://github.com/Delgan/loguru/issues/59#issuecomment-466591978
@pytest.fixture
def loguru_caplog(caplog):
    class PropogateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    logger.add(PropogateHandler(), format="{message}")
    yield caplog


# init & dispose git repo
@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_git_repo(request):
    CONFIG.git_repo = GitRepository(local_path=DEFAULT_WORKSPACE_ROOT / "unittest")
    CONFIG.git_reinit = True

    # Destroy git repo at the end of the test session.
    def fin():
        CONFIG.git_repo.delete_repository()

    # Register the function for destroying the environment.
    request.addfinalizer(fin)


@pytest.fixture(scope="session", autouse=True)
def init_config():
    Config()
