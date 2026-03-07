from __future__ import annotations

from pathlib import Path

from llm_local.utils import model_assets


def test_download_model_asset_uses_hugging_face_download_helper(
    monkeypatch,
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "models"
    downloaded_file = output_dir / "test.gguf"
    calls: dict[str, object] = {}

    def _fake_download(**kwargs):  # type: ignore[no-untyped-def]
        calls.update(kwargs)
        downloaded_file.parent.mkdir(parents=True, exist_ok=True)
        downloaded_file.write_text("ok", encoding="utf-8")
        return str(downloaded_file)

    monkeypatch.setattr(model_assets, "_import_hf_download", lambda: _fake_download)

    result = model_assets.download_model_asset(
        repo_id="example/repo",
        filename="test.gguf",
        output_dir=output_dir,
    )

    assert result == downloaded_file
    assert calls["repo_id"] == "example/repo"
    assert calls["filename"] == "test.gguf"
    assert calls["local_dir"] == str(output_dir)


def test_download_hf_snapshot_uses_hugging_face_snapshot_helper(
    monkeypatch,
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "snapshots"
    downloaded_dir = output_dir / "repo"
    calls: dict[str, object] = {}

    def _fake_snapshot_download(**kwargs):  # type: ignore[no-untyped-def]
        calls.update(kwargs)
        downloaded_dir.mkdir(parents=True, exist_ok=True)
        return str(downloaded_dir)

    monkeypatch.setattr(
        model_assets,
        "_import_hf_snapshot_download",
        lambda: _fake_snapshot_download,
    )

    result = model_assets.download_hf_snapshot(
        repo_id="example/repo",
        output_dir=output_dir,
        token="token-value",
        revision="main",
    )

    assert result == downloaded_dir
    assert calls["repo_id"] == "example/repo"
    assert calls["local_dir"] == str(output_dir)
    assert calls["local_dir_use_symlinks"] is False
    assert calls["token"] == "token-value"
    assert calls["revision"] == "main"


def test_verify_model_asset_returns_none_for_missing_path(tmp_path: Path) -> None:
    missing_model = tmp_path / "missing.gguf"

    assert model_assets.verify_model_asset(missing_model) is None
