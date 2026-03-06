#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/bootstrap_hpc.sh [--python PYTHON] [--venv-dir PATH] [--index-strategy STRATEGY] [--skip-llama-cpp] [--llama-cpp-cuda-arch ARCHES] [--help]

Create a uv-managed virtual environment for Linux HPC use and install
requirements-hpc.txt, then optionally install llama-cpp-python with CUDA enabled.

Options:
  --python PYTHON         Python version/interpreter for uv (default: 3.12.9)
  --venv-dir PATH         Virtual environment path (default: .venv)
  --index-strategy VALUE  uv index strategy for requirements install
                          (default: unsafe-best-match)
  --skip-llama-cpp        Skip CUDA build/install for llama-cpp-python
  --llama-cpp-cuda-arch   Explicit CMake CUDA arch list for llama-cpp build
                          (example: 80 or 70;80;90). If unset, CMake uses
                          native detection, which requires a visible GPU.
  --help                  Show this help text and exit
EOF
}

python_spec="3.12.9"
venv_dir=".venv"
index_strategy="unsafe-best-match"
skip_llama_cpp="false"
llama_cpp_cuda_arch=""

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
    --llama-cpp-cuda-arch)
      llama_cpp_cuda_arch="${2:?missing value for --llama-cpp-cuda-arch}"
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
venv_path="${repo_root}/${venv_dir}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install uv before running this bootstrap script." >&2
  exit 1
fi

uv venv --managed-python --python "${python_spec}" "${venv_path}"
# shellcheck disable=SC1091
source "${venv_path}/bin/activate"

# Prefer GNU toolchain when available for any unavoidable native builds.
if [[ -z "${CC:-}" ]] && command -v gcc >/dev/null 2>&1; then
  export CC="gcc"
fi
if [[ -z "${CXX:-}" ]] && command -v g++ >/dev/null 2>&1; then
  export CXX="g++"
fi

uv pip install \
  --python "${venv_path}/bin/python" \
  --index-strategy "${index_strategy}" \
  --only-binary vllm \
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

  if [[ -z "${llama_cpp_cuda_arch}" ]]; then
    if ! command -v nvidia-smi >/dev/null 2>&1 || ! nvidia-smi -L >/dev/null 2>&1; then
      cat >&2 <<'EOF'
No visible GPU detected on this node, so CMake cannot use CUDA_ARCHITECTURES=native.

Choose one:
  1) Skip llama.cpp CUDA build for now:
     scripts/bootstrap_hpc.sh --skip-llama-cpp

  2) Run bootstrap on a GPU node (recommended for native detection), e.g.:
     srun -p gpu --gres=gpu:1 --time=00:30:00 --pty bash
     module load cuda/12.1
     scripts/bootstrap_hpc.sh

  3) Provide explicit architectures when building on a non-GPU node:
     scripts/bootstrap_hpc.sh --llama-cpp-cuda-arch "70;80;90"
EOF
      exit 1
    fi
  fi

  cmake_args="-DGGML_CUDA=on"
  if [[ -n "${llama_cpp_cuda_arch}" ]]; then
    cmake_args="${cmake_args} -DCMAKE_CUDA_ARCHITECTURES=${llama_cpp_cuda_arch}"
  fi

  CMAKE_ARGS="${cmake_args}" FORCE_CMAKE=1 CUDACXX="$(command -v nvcc)" \
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
