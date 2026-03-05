from deid_local.core.llm_settings import (
    DEFAULT_TEST_MODEL_PATH,
    LLMSettingsOverrides,
    load_runtime_settings,
)


def test_load_runtime_settings_prefers_deid_values_over_legacy_aliases() -> None:
    settings = load_runtime_settings(
        {
            "DEID_LLM_PROVIDER": "vllm",
            "LLM_PROVIDER": "llama_cpp",
            "DEID_VLLM_BASE_URL": "http://preferred:9000",
            "VLLM_BASE_URL": "http://legacy:8000",
            "DEID_VLLM_MODEL": "preferred-model",
            "VLLM_MODEL": "legacy-model",
            "DEID_LLM_MAX_RETRIES": "5",
        }
    )

    assert settings.provider_name == "vllm"
    assert settings.base_url == "http://preferred:9000"
    assert settings.model == "preferred-model"
    assert settings.max_retries == 5


def test_load_runtime_settings_applies_explicit_overrides_first() -> None:
    settings = load_runtime_settings(
        {"DEID_LLM_PROVIDER": "llama_cpp", "DEID_LLAMA_CTX": "2048"},
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


def test_load_runtime_settings_derives_vllm_health_url_from_legacy_port() -> None:
    settings = load_runtime_settings(
        {
            "DEID_LLM_PROVIDER": "vllm",
            "VLLM_HEALTH_PORT": "8081",
        }
    )

    assert settings.health_url == "http://127.0.0.1:8081/healthz"


def test_load_runtime_settings_uses_repo_local_model_path_by_default() -> None:
    settings = load_runtime_settings({})

    assert settings.provider_name == "llama_cpp"
    assert settings.model_path == DEFAULT_TEST_MODEL_PATH


def test_sanitized_dict_redacts_api_keys() -> None:
    settings = load_runtime_settings(
        {"DEID_LLM_PROVIDER": "openai_http", "DEID_OPENAI_API_KEY": "secret-token"}
    )

    assert settings.sanitized_dict()["api_key"] == "<redacted>"
