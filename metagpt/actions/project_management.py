#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : project_management.py
"""
import json
from typing import List

from metagpt.actions import ActionOutput
from metagpt.actions.action import Action
from metagpt.config import CONFIG
from metagpt.const import SYSTEM_DESIGN_FILE_REPO, TASK_FILE_REPO, WORKSPACE_ROOT
from metagpt.schema import Document, Documents
from metagpt.utils.common import CodeParser
from metagpt.utils.get_template import get_template
from metagpt.utils.json_to_markdown import json_to_markdown

templates = {
    "json": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are a project manager; the goal is to break down tasks according to PRD/technical design, give a task list, and analyze task dependencies to start with the prerequisite modules
Requirements: Based on the context, fill in the following missing information, each section name is a key in json. Here the granularity of the task is a file, if there are any missing files, you can supplement them
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## Required Python third-party packages: Provided in requirements.txt format

## Required Other language third-party packages: Provided in requirements.txt format

## Full API spec: Use OpenAPI 3.0. Describe all APIs that may be used by both frontend and backend.

## Logic Analysis: Provided as a Python list[list[str]. the first is filename, the second is class/method/function should be implemented in this file. Analyze the dependencies between the files, which work should be done first

## Task list: Provided as Python list[str]. Each str is a filename, the more at the beginning, the more it is a prerequisite dependency, should be done first

## Shared Knowledge: Anything that should be public like utils' functions, config's variables details that should make clear first. 

## Anything UNCLEAR: Provide as Plain text. Make clear here. For example, don't forget a main entry. don't forget to init 3rd party libs.

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example,
and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": '''
{
    "Required Python third-party packages": [
        "flask==1.1.2",
        "bcrypt==3.2.0"
    ],
    "Required Other language third-party packages": [
        "No third-party ..."
    ],
    "Full API spec": """
        openapi: 3.0.0
        ...
        description: A JSON object ...
     """,
    "Logic Analysis": [
        ["game.py","Contains..."]
    ],
    "Task list": [
        "game.py"
    ],
    "Shared Knowledge": """
        'game.py' contains ...
    """,
    "Anything UNCLEAR": "We need ... how to start."
}
''',
    },
    "markdown": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are a project manager; the goal is to break down tasks according to PRD/technical design, give a task list, and analyze task dependencies to start with the prerequisite modules
Requirements: Based on the context, fill in the following missing information, note that all sections are returned in Python code triple quote form seperatedly. Here the granularity of the task is a file, if there are any missing files, you can supplement them
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## Required Python third-party packages: Provided in requirements.txt format

## Required Other language third-party packages: Provided in requirements.txt format

## Full API spec: Use OpenAPI 3.0. Describe all APIs that may be used by both frontend and backend.

## Logic Analysis: Provided as a Python list[list[str]. the first is filename, the second is class/method/function should be implemented in this file. Analyze the dependencies between the files, which work should be done first

## Task list: Provided as Python list[str]. Each str is a filename, the more at the beginning, the more it is a prerequisite dependency, should be done first

## Shared Knowledge: Anything that should be public like utils' functions, config's variables details that should make clear first. 

## Anything UNCLEAR: Provide as Plain text. Make clear here. For example, don't forget a main entry. don't forget to init 3rd party libs.

""",
        "FORMAT_EXAMPLE": '''
---
## Required Python third-party packages
```python
"""
flask==1.1.2
bcrypt==3.2.0
"""
```

## Required Other language third-party packages
```python
"""
No third-party ...
"""
```

## Full API spec
```python
"""
openapi: 3.0.0
...
description: A JSON object ...
"""
```

## Logic Analysis
```python
[
    ["game.py", "Contains ..."],
]
```

## Task list
```python
[
    "game.py",
]
```

## Shared Knowledge
```python
"""
'game.py' contains ...
"""
```

## Anything UNCLEAR
We need ... how to start.
---
''',
    },
}
OUTPUT_MAPPING = {
    "Required Python third-party packages": (List[str], ...),
    "Required Other language third-party packages": (List[str], ...),
    "Full API spec": (str, ...),
    "Logic Analysis": (List[List[str]], ...),
    "Task list": (List[str], ...),
    "Shared Knowledge": (str, ...),
    "Anything UNCLEAR": (str, ...),
}


class WriteTasks(Action):
    def __init__(self, name="CreateTasks", context=None, llm=None):
        super().__init__(name, context, llm)

    def _save(self, context, rsp):
        if context[-1].instruct_content:
            ws_name = context[-1].instruct_content.dict()["Python package name"]
        else:
            ws_name = CodeParser.parse_str(block="Python package name", text=context[-1].content)
        file_path = WORKSPACE_ROOT / ws_name / "docs/api_spec_and_tasks.md"
        file_path.write_text(json_to_markdown(rsp.instruct_content.dict()))

        # Write requirements.txt
        requirements_path = WORKSPACE_ROOT / ws_name / "requirements.txt"
        requirements_path.write_text("\n".join(rsp.instruct_content.dict().get("Required Python third-party packages")))

    async def run(self, with_messages, format=CONFIG.prompt_format):
        system_design_file_repo = CONFIG.git_repo.new_file_repository(SYSTEM_DESIGN_FILE_REPO)
        changed_system_designs = system_design_file_repo.changed_files

        tasks_file_repo = CONFIG.git_repo.new_file_repository(TASK_FILE_REPO)
        changed_tasks = tasks_file_repo.changed_files
        change_files = Documents()
        # 根据docs/system_designs/下的git head diff识别哪些task文档需要重写
        for filename in changed_system_designs:
            system_design_doc = await system_design_file_repo.get(filename)
            task_doc = await tasks_file_repo.get(filename)
            if task_doc:
                task_doc = await self._merge(system_design_doc, task_doc)
            else:
                rsp = await self._run(system_design_doc.content)
                task_doc = Document(root_path=TASK_FILE_REPO, filename=filename, content=rsp.instruct_content.json())
            await tasks_file_repo.save(
                filename=filename, content=task_doc.content, dependencies={system_design_doc.root_relative_path}
            )
            await self._update_requirements(task_doc)
            change_files.docs[filename] = task_doc

        # 根据docs/tasks/下的git head diff识别哪些task文件被用户修改了，需要重写
        for filename in changed_tasks:
            if filename in change_files.docs:
                continue
            system_design_doc = await system_design_file_repo.get(filename)
            task_doc = await tasks_file_repo.get(filename)
            task_doc = await self._merge(system_design_doc, task_doc)
            await tasks_file_repo.save(
                filename=filename, content=task_doc.content, dependencies={system_design_doc.root_relative_path}
            )
            await self._update_requirements(task_doc)
            change_files.docs[filename] = task_doc

        # 等docs/tasks/下所有文件都处理完才发publish message，给后续做全局优化留空间。
        return ActionOutput(content=change_files.json(), instruct_content=change_files)

    async def _run(self, context, format=CONFIG.prompt_format):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context, format_example=format_example)
        rsp = await self._aask_v1(prompt, "task", OUTPUT_MAPPING, format=format)
        self._save(context, rsp)
        return rsp

    async def _merge(self, system_design_doc, task_dock) -> Document:
        return task_dock

    async def _update_requirements(self, doc):
        m = json.loads(doc.content)
        packages = set(m.get("Required Python third-party packages", set()))
        file_repo = CONFIG.git_repo.new_file_repository()
        filename = "requirements.txt"
        requirement_doc = await file_repo.get(filename)
        if not requirement_doc:
            requirement_doc = Document(filename=filename, root_path=".", content="")
        lines = requirement_doc.content.splitlines()
        for pkg in lines:
            if pkg == "":
                continue
            packages.add(pkg)
        await file_repo.save(filename, content="\n".join(packages))


class AssignTasks(Action):
    async def run(self, *args, **kwargs):
        # Here you should implement the actual action
        pass
