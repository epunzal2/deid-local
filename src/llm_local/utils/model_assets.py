"""Helpers for fetching and verifying local model assets."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def download_model_asset(repo_id: str, filename: str, output_dir: str | Path) -> Path:
    """Download a model asset from Hugging Face into a local output directory."""

    hf_hub_download = _import_hf_download()
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    downloaded_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=str(destination),
        local_dir_use_symlinks=False,
    )
    return Path(downloaded_path)


def download_hf_snapshot(
    repo_id: str,
    output_dir: str | Path,
    *,
    token: str | None = None,
    revision: str | None = None,
) -> Path:
    """Download a Hugging Face repository snapshot into a local output directory."""

    snapshot_download = _import_hf_snapshot_download()
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    download_kwargs: dict[str, object] = {
        "repo_id": repo_id,
        "local_dir": str(destination),
        "local_dir_use_symlinks": False,
    }
    if token is not None:
        download_kwargs["token"] = token
    if revision is not None:
        download_kwargs["revision"] = revision
    downloaded_path = snapshot_download(**download_kwargs)
    return Path(downloaded_path)


def verify_model_asset(path: str | Path) -> Path | None:
    """Return the path when the asset exists, otherwise `None`."""

    candidate = Path(path)
    return candidate if candidate.exists() else None


def _import_hf_download() -> Any:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:  # pragma: no cover - exercised via runtime behavior
        raise RuntimeError(
            "huggingface_hub is not installed. Install the optional `models` extra."
        ) from exc
    return hf_hub_download


def _import_hf_snapshot_download() -> Any:
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:  # pragma: no cover - exercised via runtime behavior
        raise RuntimeError(
            "huggingface_hub is not installed. Install the optional `models` extra."
        ) from exc
    return snapshot_download
