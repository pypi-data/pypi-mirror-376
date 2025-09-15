import requests
import typer

from tfrunner.env.tfvars_env_loader import TfVarsEnvLoader
from tfrunner.utils import load_env_var

from .base import SecretsBackend, SecretsBackendSpec


class GitlabSecretsBackendSpec(SecretsBackendSpec):
    # Url of the Gitlab instance. Use https://gitlab.com unless
    # using Gitlab self-hosted.
    url: str
    # Id of the project to store secrets backend in
    project_id: int
    # Name of the environment variable to fetch Gitlab token from
    token_var: str


class GitlabSecretsBackend(SecretsBackend):
    """
    Fetches GitLab CI variables inside of a GitLab project.

    Loads them as env variables and returns them.
    """

    @classmethod
    def run(
        cls,
        environment: str,
        config: GitlabSecretsBackendSpec,
    ) -> dict[str, str]:
        typer.echo("==> Using Gitlab secrets backend. Loading CI variables...")
        typer.echo(f"=> Gitlab environment: {environment}")
        response: list[dict] = cls.__make_gitlab_request(
            url=config.url, project_id=config.project_id, token_var=config.token_var
        )
        vars: dict[str, str] = cls.__extract_vars_from_response(environment, response)
        TfVarsEnvLoader.load(vars)
        typer.echo(f"=> Loaded variables: {list(vars.keys())}")
        return vars

    @classmethod
    def __make_gitlab_request(
        cls, url: str, project_id: int, token_var: str
    ) -> list[dict]:
        api_url: str = "{}/api/v4/projects/{}/variables".format(url, project_id)
        headers: dict[str, str] = {"PRIVATE-TOKEN": load_env_var(token_var)}
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"""
            Failed to fetch CI variables.
            Gitlab url: {url}
            Project: {project_id}
            Status code: {response.status_code}
            Response: {response.text}
            """
            )

    @staticmethod
    def __extract_vars_from_response(
        environment: str, response: list[dict]
    ) -> dict[str, str]:
        return {
            item["key"]: item["value"]
            for item in response
            # Filter variables for the specific environment or for all environments
            if item["environment_scope"] == environment
            or item["environment_scope"] == "*"
        }
