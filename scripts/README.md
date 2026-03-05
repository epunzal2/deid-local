# Scripts

Place thin wrappers and explicit environment bootstrap helpers here.

- `bootstrap_mac.sh`: create a local macOS virtual environment, install
  `requirements-mac.txt`, build `llama-cpp-python` with Metal enabled, and install
  `vllm` from `scratch/vllm-source`
- `bootstrap_hpc.sh`: create a virtual environment and install
  `requirements-hpc.txt`, then build `llama-cpp-python` with CUDA enabled

Thin wrappers live here and call into package code under `src/`.

Current deployment wrappers:

- `scripts/deployment/macos/setup_llama_cpp.sh`
- `scripts/deployment/hpc/setup_env.sh`
- `scripts/deployment/hpc/llama_cpp_smoke.sbatch`
- `scripts/deployment/hpc/vllm_smoke.sbatch`
- `scripts/deployment/hpc/submit_llama_cpp_smoke.sh`
- `scripts/deployment/hpc/submit_vllm_smoke.sh`
