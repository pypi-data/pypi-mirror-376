import os
import subprocess
from pathlib import Path
from typing import Annotated, Optional

import typer

from tfrunner.env.env_export import EnvExporter
from tfrunner.env.tfvars_env_loader import TfVarsEnvLoader
from tfrunner.projects.base import ProjectConfig, TfrunnerConfig
from tfrunner.secrets_backend.factory import SecretsBackendFactory
from tfrunner.utils import set_git_sandbox_env_var

app = typer.Typer()


@app.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    }
)
def apply(
    ctx: typer.Context,
    project: Annotated[
        Optional[str], typer.Option(help="name of the project to initialize")
    ],
    git_sandbox: Annotated[
        bool,
        typer.Option(
            help="execute terraform/tofu project in a sandbox environment of your git branch"
        ),
    ] = False,
    config_path: Annotated[
        Path,
        typer.Option(
            help="location of the config file to use for the tool's execution"
        ),
    ] = Path("tfrunner.yaml"),
) -> None:
    config = TfrunnerConfig.from_yaml(config_path)
    project_config: ProjectConfig = config.projects[project]
    _ = SecretsBackendFactory.select_and_run(
        config=config,
        project=project_config,
        environment=project,
    )
    EnvExporter.export(
        config=config,
        project_config=project_config,
    )
    TfVarsEnvLoader.select_and_load(
        config=config,
        project=project_config,
    )
    if git_sandbox:
        set_git_sandbox_env_var()
    cmds: list[str] = [config.flavour.value, "apply"] + ctx.args
    subprocess.call(cmds, cwd=project_config.path, env=os.environ.copy())
