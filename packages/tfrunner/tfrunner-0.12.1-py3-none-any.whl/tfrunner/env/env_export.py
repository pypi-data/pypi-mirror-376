from typing import Any
import os

from tfrunner.projects.base import TfrunnerConfig, ProjectConfig


class EnvExporter:

    @classmethod
    def export(cls, config: TfrunnerConfig, project_config: ProjectConfig) -> None:
        config_env = config.env | {}
        project_env = project_config.env | {}
        env: dict[str, Any] = {**project_env, **config_env}
        for k, v in env.items():
            os.environ[k] = v
