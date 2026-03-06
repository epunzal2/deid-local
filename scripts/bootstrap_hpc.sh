#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/bootstrap_hpc.sh [--python PYTHON] [--venv-dir PATH] [--python-platform PLATFORM] [--index-strategy STRATEGY] [--uv-cache-dir PATH] [--tmp-dir PATH] [--skip-llama-cpp] [--llama-cpp-cuda-arch ARCHES] [--help]

Create a uv-managed virtual environment for Linux HPC use and install
requirements-hpc.txt, then optionally install llama-cpp-python with CUDA enabled.

Options:
  --python PYTHON         Python version/interpreter for uv (default: 3.12.9)
  --venv-dir PATH         Virtual environment path (default: .venv)
  --python-platform VALUE Target platform tag for uv resolution
                          (default: x86_64-manylinux2014)
  --index-strategy VALUE  uv index strategy for requirements install
                          (default: unsafe-best-match)
  --uv-cache-dir PATH     uv cache directory (default: \$UV_CACHE_DIR or
                          /scratch/\$USER/.cache/uv or <repo>/.cache/uv)
  --tmp-dir PATH          temp directory for build/extract steps
                          (default: \$TMPDIR or /scratch/\$USER/tmp or
                          <repo>/.tmp)
  --skip-llama-cpp        Skip CUDA build/install for llama-cpp-python
  --llama-cpp-cuda-arch   Explicit CMake CUDA arch list for llama-cpp build
                          (default: 70;80;89)
  --help                  Show this help text and exit
EOF
}

python_spec="3.12.9"
venv_dir=".venv"
python_platform="x86_64-manylinux2014"
index_strategy="unsafe-best-match"
uv_cache_dir=""
tmp_dir=""
skip_llama_cpp="false"
llama_cpp_cuda_arch="70;80;89"

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
    --python-platform)
      python_platform="${2:?missing value for --python-platform}"
      shift 2
      ;;
    --index-strategy)
      index_strategy="${2:?missing value for --index-strategy}"
      shift 2
      ;;
    --uv-cache-dir)
      uv_cache_dir="${2:?missing value for --uv-cache-dir}"
      shift 2
      ;;
    --tmp-dir)
      tmp_dir="${2:?missing value for --tmp-dir}"
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
scratch_root="/scratch/${USER:-}"

if [[ -z "${uv_cache_dir}" ]]; then
  if [[ -n "${UV_CACHE_DIR:-}" ]]; then
    uv_cache_dir="${UV_CACHE_DIR}"
  elif [[ -n "${USER:-}" && -d "${scratch_root}" && -w "${scratch_root}" ]]; then
    uv_cache_dir="${scratch_root}/.cache/uv"
  else
    uv_cache_dir="${repo_root}/.cache/uv"
  fi
fi
if [[ -z "${tmp_dir}" ]]; then
  if [[ -n "${TMPDIR:-}" ]]; then
    tmp_dir="${TMPDIR}"
  elif [[ -n "${USER:-}" && -d "${scratch_root}" && -w "${scratch_root}" ]]; then
    tmp_dir="${scratch_root}/tmp"
  else
    tmp_dir="${repo_root}/.tmp"
  fi
fi

mkdir -p "${uv_cache_dir}" "${tmp_dir}"
export UV_CACHE_DIR="${uv_cache_dir}"
export TMPDIR="${tmp_dir}"

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
  --python-platform "${python_platform}" \
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
Python platform used: ${python_platform}
Index strategy used: ${index_strategy}
UV cache dir: ${UV_CACHE_DIR}
TMPDIR: ${TMPDIR}
llama-cpp-python CUDA build: ${llama_cpp_status}
llama-cpp CUDA architectures: ${llama_cpp_cuda_arch}
Activate with:
  source "${venv_path}/bin/activate"
EOF
