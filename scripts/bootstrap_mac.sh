#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/bootstrap_mac.sh [--python PYTHON] [--venv-dir PATH] [--help]

Create a virtual environment for local macOS use and install requirements-mac.txt,
then install llama-cpp-python with Metal enabled and vLLM from source.

Options:
  --python PYTHON    Python interpreter to use (default: python3)
  --venv-dir PATH    Virtual environment path (default: .venv)
  --help             Show this help text and exit
EOF
}

python_bin="python3"
venv_dir=".venv"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      python_bin="${2:?missing value for --python}"
      shift 2
      ;;
    --venv-dir)
      venv_dir="${2:?missing value for --venv-dir}"
      shift 2
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
vllm_src="${repo_root}/scratch/vllm-source"

"${python_bin}" -m venv "${repo_root}/${venv_dir}"
# shellcheck disable=SC1091
source "${repo_root}/${venv_dir}/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r "${repo_root}/requirements-mac.txt"
CMAKE_ARGS="-DGGML_METAL=on" FORCE_CMAKE=1 \
  python -m pip install --no-binary llama-cpp-python llama-cpp-python

mkdir -p "${repo_root}/scratch"
if [[ -d "${vllm_src}/.git" ]]; then
  git -C "${vllm_src}" pull --ff-only
else
  git clone https://github.com/vllm-project/vllm.git "${vllm_src}"
fi

python -m pip install -r "${vllm_src}/requirements/cpu.txt"
VLLM_TARGET_DEVICE=cpu python -m pip install -e "${vllm_src}"

cat <<EOF
macOS environment bootstrapped in ${repo_root}/${venv_dir}
Activate with:
  source "${repo_root}/${venv_dir}/bin/activate"
EOF
