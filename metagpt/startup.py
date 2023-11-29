#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio

import typer

from metagpt.config import CONFIG

app = typer.Typer()


@app.command()
def startup(
    idea: str = typer.Argument(..., help="Your innovative idea, such as 'Create a 2048 game.'"),
    investment: float = typer.Option(3.0, help="Dollar amount to invest in the AI company."),
    n_round: int = typer.Option(5, help="Number of rounds for the simulation."),
    code_review: bool = typer.Option(True, help="Whether to use code review."),
    run_tests: bool = typer.Option(False, help="Whether to enable QA for adding & running tests."),
    implement: bool = typer.Option(True, help="Enable or disable code implementation."),
    project_name: str = typer.Option("", help="Unique project name, such as 'game_2048'."),
    inc: bool = typer.Option(False, help="Incremental mode. Use it to coop with existing repo."),
    project_path: str = typer.Option(
        help="Specify the directory path of the old version project to fulfill the " "incremental requirements."
    ),
    reqa_file: str = typer.Option(help="Specify the source file name for rewriting the quality test code."),
):
    """Run a startup. Be a boss."""
    from metagpt.roles import (
        Architect,
        Engineer,
        ProductManager,
        ProjectManager,
        QaEngineer,
    )
    from metagpt.team import Team

    # Use in the PrepareDocuments action according to Section 2.2.3.5.1 of RFC 135.
    CONFIG.project_name = project_name
    CONFIG.inc = inc
    CONFIG.project_path = project_path
    CONFIG.reqa_file = reqa_file

    company = Team()
    company.hire(
        [
            ProductManager(),
            Architect(),
            ProjectManager(),
        ]
    )

    if implement or code_review:
        company.hire([Engineer(n_borg=5, use_code_review=code_review)])

    if run_tests:
        company.hire([QaEngineer()])

    company.invest(investment)
    company.run_project(idea)
    asyncio.run(company.run(n_round=n_round))


if __name__ == "__main__":
    app()
