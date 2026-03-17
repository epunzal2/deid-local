from llm_local.core.llm_settings import (
    DEFAULT_TEST_MODEL_PATH,
    LLMSettingsOverrides,
    load_runtime_settings,
)


def test_load_runtime_settings_uses_primary_env_vars() -> None:
    settings = load_runtime_settings(
        {
            "LLM_PROVIDER": "vllm",
            "VLLM_BASE_URL": "http://preferred:9000",
            "VLLM_MODEL": "preferred-model",
            "LLM_MAX_RETRIES": "5",
        }
    )

    assert settings.provider_name == "vllm"
    assert settings.base_url == "http://preferred:9000"
    assert settings.model == "preferred-model"
    assert settings.max_retries == 5


def test_load_runtime_settings_applies_explicit_overrides_first() -> None:
    settings = load_runtime_settings(
        {"LLM_PROVIDER": "llama_cpp", "LLAMA_CTX": "2048"},
        overrides=LLMSettingsOverrides(
            provider_name="openai_http",
            base_url="http://override:1234",
            model="override-model",
            max_tokens=777,
        ),
    )

    assert settings.provider_name == "openai_http"
    assert settings.base_url == "http://override:1234"
    assert settings.model == "override-model"
    assert settings.max_tokens == 777


def test_load_runtime_settings_uses_repo_local_model_path_by_default() -> None:
    settings = load_runtime_settings({})

    assert settings.provider_name == "llama_cpp"
    assert settings.model_path == DEFAULT_TEST_MODEL_PATH


def test_sanitized_dict_redacts_api_keys() -> None:
    settings = load_runtime_settings(
        {"LLM_PROVIDER": "openai_http", "OPENAI_API_KEY": "secret-token"}
    )

    assert settings.sanitized_dict()["api_key"] == "<redacted>"


def test_vllm_model_path_takes_precedence_over_vllm_model() -> None:
    settings = load_runtime_settings(
        {
            "LLM_PROVIDER": "vllm",
            "VLLM_MODEL_PATH": "/shared/models/local-weights",
            "VLLM_MODEL": "remote-model",
        }
    )

    assert settings.model == "/shared/models/local-weights"
