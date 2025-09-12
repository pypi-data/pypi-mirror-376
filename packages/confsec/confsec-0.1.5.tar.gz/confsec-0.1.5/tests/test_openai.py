import os
import pytest
from unittest.mock import Mock, patch

from confsec.openai import OpenAI
from confsec.client.client import ConfsecClient


@pytest.fixture
def mock_dependencies():
    """Fixture that sets up all the mock dependencies for OpenAI tests."""
    with patch("confsec.openai.ConfsecClient") as mock_confsec_client, patch(
        "confsec.openai._OpenAI"
    ) as mock_openai:
        mock_client_instance = Mock(spec=ConfsecClient)
        mock_confsec_client.return_value = mock_client_instance
        mock_http_client = Mock()
        mock_client_instance.get_http_client.return_value = mock_http_client

        mock_openai_instance = Mock()
        mock_openai_instance.chat = Mock()
        mock_openai_instance.completions = Mock()
        mock_openai.return_value = mock_openai_instance

        yield {
            "mock_confsec_client": mock_confsec_client,
            "mock_client_instance": mock_client_instance,
            "mock_http_client": mock_http_client,
            "mock_openai": mock_openai,
            "mock_openai_instance": mock_openai_instance,
        }


class TestOpenAIInitialization:
    def test_with_explicit_api_key(self, mock_dependencies):
        mocks = mock_dependencies

        openai_client = OpenAI(api_key="test_api_key")

        mocks["mock_confsec_client"].assert_called_once_with(api_key="test_api_key")
        mocks["mock_openai"].assert_called_once_with(
            api_key="test_api_key",
            base_url="http://confsec.invalid/v1",
            http_client=mocks["mock_http_client"],
        )
        assert openai_client.chat is mocks["mock_openai_instance"].chat
        assert openai_client.completions is mocks["mock_openai_instance"].completions

    def test_with_environment_variable_api_key(self, mock_dependencies):
        mocks = mock_dependencies

        with patch.dict(os.environ, {"CONFSEC_API_KEY": "env_api_key"}):
            _ = OpenAI()

            mocks["mock_confsec_client"].assert_called_once_with(api_key="env_api_key")
            mocks["mock_openai"].assert_called_once_with(
                api_key="env_api_key",
                base_url="http://confsec.invalid/v1",
                http_client=mocks["mock_http_client"],
            )

    def test_missing_api_key_raises_key_error(self):
        # Ensure CONFSEC_API_KEY is not in environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(KeyError, match="CONFSEC_API_KEY"):
                OpenAI()

    def test_explicit_api_key_overrides_environment(self, mock_dependencies):
        mocks = mock_dependencies

        with patch.dict(os.environ, {"CONFSEC_API_KEY": "env_api_key"}):
            _ = OpenAI(api_key="explicit_key")

            mocks["mock_confsec_client"].assert_called_once_with(api_key="explicit_key")
            mocks["mock_openai"].assert_called_once_with(
                api_key="explicit_key",
                base_url="http://confsec.invalid/v1",
                http_client=mocks["mock_http_client"],
            )


class TestResourceManagement:
    def test_close_calls_confsec_client_close(self, mock_dependencies):
        mocks = mock_dependencies

        openai_client = OpenAI(api_key="test_key")
        openai_client.close()

        mocks["mock_client_instance"].close.assert_called_once()

    def test_context_manager_calls_close(self, mock_dependencies):
        mocks = mock_dependencies

        with OpenAI(api_key="test_key") as _:
            pass

        mocks["mock_client_instance"].close.assert_called_once()


class TestConfsecClientProperty:
    def test_confsec_client_property_returns_client_instance(self, mock_dependencies):
        mocks = mock_dependencies

        openai_client = OpenAI(api_key="test_key")

        assert openai_client.confsec_client is mocks["mock_client_instance"]


class TestConfigurationEdgeCases:
    def test_empty_config_vs_none(self, mock_dependencies):
        mocks = mock_dependencies

        # Test with None config
        _ = OpenAI(api_key="test_key", confsec_config=None)
        # Test with empty dict config
        _ = OpenAI(api_key="test_key", confsec_config={})

        # Both should result in the same call to ConfsecClient
        # Both calls should pass only the api_key parameter
        assert mocks["mock_confsec_client"].call_count == 2
        for call in mocks["mock_confsec_client"].call_args_list:
            assert call == ((), {"api_key": "test_key"})

    def test_partial_config(self, mock_dependencies):
        mocks = mock_dependencies

        partial_config = {"concurrent_requests_target": 5, "env": "staging"}

        _ = OpenAI(api_key="test_key", confsec_config=partial_config)  # type: ignore

        mocks["mock_confsec_client"].assert_called_once_with(
            api_key="test_key",
            concurrent_requests_target=5,
            env="staging",
        )
