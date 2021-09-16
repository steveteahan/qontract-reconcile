from typing import Dict, Any

from slack_sdk import WebClient

from reconcile.utils import gql

from reconcile import queries

from reconcile.utils.secret_reader import SecretReader


SLACK_WORKSPACE_QUERY = """
{
  slack_workspaces_v1{
    name
    token {
      path
      field
      format
      version
    }
  }
}
"""


class Settings:

    def __init__(self):
        self._settings = queries.get_app_interface_settings()
        self._gql_api = gql.get_api()
        self._secret_reader = SecretReader(settings=self._settings)

    @property
    def slack_workspaces(self) -> Dict[str, Any]:
        return self._gql_api.query(SLACK_WORKSPACE_QUERY)

    def get_slack_token(self, workspace_name: str) -> str:
        workspace = self.slack_workspaces[workspace_name]
        return self._secret_reader.read(workspace['token'])

    def get_slack_client(self, workspace_name: str) -> WebClient:
        return WebClient(token=self.get_slack_token(workspace_name))
