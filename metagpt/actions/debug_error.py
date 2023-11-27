#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:46
@Author  : alexanderwu
@File    : debug_error.py
@Modified By: mashenquan, 2023/11/27.
        1. Divide the context into three components: legacy code, unit test code, and console log.
        2. According to Section 2.2.3.1 of RFC 135, replace file data in the message with the file name.
"""
import re

from metagpt.actions.action import Action
from metagpt.config import CONFIG
from metagpt.const import TEST_CODES_FILE_REPO, TEST_OUTPUTS_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import RunCodeResult
from metagpt.utils.common import CodeParser
from metagpt.utils.file_repository import FileRepository

PROMPT_TEMPLATE = """
NOTICE
1. Role: You are a Development Engineer or QA engineer;
2. Task: You received this message from another Development Engineer or QA engineer who ran or tested your code. 
Based on the message, first, figure out your own role, i.e. Engineer or QaEngineer,
then rewrite the development code or the test code based on your role, the error, and the summary, such that all bugs are fixed and the code performs well.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the test case or script and triple quotes.
The message is as follows:
# Legacy Code
```python
{code}
```
---
# Unit Test Code
```python
{test_code}
```
---
# Console logs
```text
{logs}
```
---
Now you should start rewriting the code:
## file name of the code to rewrite: Write code with triple quoto. Do your best to implement THIS IN ONLY ONE FILE.
"""


class DebugError(Action):
    def __init__(self, name="DebugError", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, *args, **kwargs) -> str:
        output_doc = await FileRepository.get_file(filename=self.context.output_filename, relative_path=TEST_OUTPUTS_FILE_REPO)
        if not output_doc:
            return ""
        output_detail = RunCodeResult.loads(output_doc.content)
        pattern = r"Ran (\d+) tests in ([\d.]+)s\n\nOK"
        matches = re.search(pattern, output_detail.stderr)
        if matches:
            return ""

        logger.info(f"Debug and rewrite {self.context.code_filename}")
        code_doc = await FileRepository.get_file(filename=self.context.code_filename, relative_path=CONFIG.src_workspace)
        if not code_doc:
            return ""
        test_doc = await FileRepository.get_file(filename=self.context.test_filename, relative_path=TEST_CODES_FILE_REPO)
        if not test_doc:
            return ""
        prompt = PROMPT_TEMPLATE.format(code=code_doc.content, test_code=test_doc.content, logs=output_detail.stderr)

        rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=rsp)

        return code
