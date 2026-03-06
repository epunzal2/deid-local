#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/bootstrap_hpc.sh [--python PYTHON] [--venv-dir PATH] [--index-strategy STRATEGY] [--skip-llama-cpp] [--help]

Create a uv-managed virtual environment for Linux HPC use and install
requirements-hpc.txt, then optionally install llama-cpp-python with CUDA enabled.

Options:
  --python PYTHON         Python version/interpreter for uv (default: 3.12.9)
  --venv-dir PATH         Virtual environment path (default: .venv)
  --index-strategy VALUE  uv index strategy for requirements install
                          (default: unsafe-best-match)
  --skip-llama-cpp        Skip CUDA build/install for llama-cpp-python
  --help                  Show this help text and exit
EOF
}

python_spec="3.12.9"
venv_dir=".venv"
index_strategy="unsafe-best-match"
skip_llama_cpp="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      python_spec="${2:?missing value for --python}"
      shift 2
      ;;
    --venv-dir)
      venv_dir="${2:?missing value for --venv-dir}"
      shift 2
      ;;
    --index-strategy)
      index_strategy="${2:?missing value for --index-strategy}"
      shift 2
      ;;
    --skip-llama-cpp)
      skip_llama_cpp="true"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
venv_path="${repo_root}/${venv_dir}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install uv before running this bootstrap script." >&2
  exit 1
fi

uv venv --managed-python --python "${python_spec}" "${venv_path}"
# shellcheck disable=SC1091
source "${venv_path}/bin/activate"

uv pip install \
  --python "${venv_path}/bin/python" \
  --index-strategy "${index_strategy}" \
  -r "${repo_root}/requirements-hpc.txt"

if [[ "${skip_llama_cpp}" == "false" ]]; then
  if ! command -v nvcc >/dev/null 2>&1; then
    cat >&2 <<'EOF'
CUDA compiler (nvcc) not found.
Load your cluster CUDA module in this shell before installing llama-cpp-python:
  module load cuda/12.1

Or rerun with --skip-llama-cpp if you only need the vLLM runtime path.
EOF
    exit 1
  fi

  CMAKE_ARGS="-DGGML_CUDA=on" FORCE_CMAKE=1 CUDACXX="$(command -v nvcc)" \
    uv pip install \
      --python "${venv_path}/bin/python" \
      --no-binary llama-cpp-python \
      llama-cpp-python
fi

llama_cpp_status="installed"
if [[ "${skip_llama_cpp}" == "true" ]]; then
  llama_cpp_status="skipped"
fi

cat <<EOF
HPC environment bootstrapped in ${venv_path}
Index strategy used: ${index_strategy}
llama-cpp-python CUDA build: ${llama_cpp_status}
Activate with:
  source "${venv_path}/bin/activate"
EOF
