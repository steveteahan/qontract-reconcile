import time
from collections.abc import (
    Callable,
    Mapping,
    MutableMapping,
)
from typing import (
    Any,
    Optional,
)
from unittest.mock import create_autospec

import httpretty as _httpretty
import pytest
from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError

from reconcile.gql_definitions.fragments.vault_secret import VaultSecret
from reconcile.utils.models import data_default_none
from reconcile.utils.state import State


@pytest.fixture
def patch_sleep(mocker):
    yield mocker.patch.object(time, "sleep")


@pytest.fixture()
def httpretty():
    with _httpretty.enabled(allow_net_connect=False):
        _httpretty.reset()
        yield _httpretty


@pytest.fixture
def secret_reader(mocker) -> None:
    mock_secretreader = mocker.patch(
        "reconcile.utils.secret_reader.SecretReader", autospec=True
    )
    mock_secretreader.read.return_value = "secret"
    mock_secretreader.read_secret.return_value = "secret"
    return mock_secretreader


@pytest.fixture
def s3_state_builder() -> Callable[[Mapping], State]:
    """
    Example input data:
    {
        "get": {
            # This maps data being returned by get
            "path/to/item": {
                "some_key": "content",
                "other_content": "content",
            },
            "other/path": {
                "other": "data",
            },
        },
        "ls": [
            "/path/item1",
            "/path/item2",
        ]
    }
    """

    def builder(data: Mapping) -> State:
        def get(key: str, *args) -> dict:
            try:
                return data["get"][key]
            except KeyError:
                if args:
                    return args[0]
                raise

        state = create_autospec(spec=State)
        state.get = get
        state.ls.side_effect = [data["ls"]]
        return state

    return builder


@pytest.fixture
def vault_secret():
    return VaultSecret(
        path="path/test",
        field="key",
        format=None,
        version=None,
    )


@pytest.fixture
def data_factory() -> Callable[
    [type[BaseModel], Optional[MutableMapping[str, Any]]], MutableMapping[str, Any]
]:
    """Set default values to None."""

    def _data_factory(
        klass: type[BaseModel], data: Optional[MutableMapping[str, Any]] = None
    ) -> MutableMapping[str, Any]:
        return data_default_none(klass, data or {})

    return _data_factory


class GQLClassFactoryError(Exception):
    pass


@pytest.fixture
def gql_class_factory() -> Callable[
    [type[BaseModel], Optional[MutableMapping[str, Any]]], BaseModel
]:
    """Create a GQL class from a fixture and set default values to None."""

    def _gql_class_factory(
        klass: type[BaseModel], data: Optional[MutableMapping[str, Any]] = None
    ) -> BaseModel:
        try:
            return klass(**data_default_none(klass, data or {}))
        except ValidationError as e:
            msg = "[gql_class_factory] Your given data does not match the class ...\n"
            msg += "\n".join([str(m) for m in list(e.raw_errors)])
            raise GQLClassFactoryError(msg) from e

    return _gql_class_factory
