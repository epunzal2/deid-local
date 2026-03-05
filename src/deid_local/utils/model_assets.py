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
