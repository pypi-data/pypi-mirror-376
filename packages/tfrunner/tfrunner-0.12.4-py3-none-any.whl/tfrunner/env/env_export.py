import json
from typing import Any
import os

from tfrunner.projects.base import TfrunnerConfig, ProjectConfig


class EnvExporter:

    @classmethod
    def export(cls, config: TfrunnerConfig, project_config: ProjectConfig) -> None:
        config_env = config.env or {}
        project_env = project_config.env or {}
        env: dict[str, Any] = {**project_env, **config_env}
        for k, v in env.items():
            value = v if isinstance(v, str) else json.dumps(v)
            os.environ[f"TF_VAR_{k.lower()}"] = value
