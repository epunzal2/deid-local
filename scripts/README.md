# Scripts

Place thin wrappers and explicit environment bootstrap helpers here.

- `bootstrap_mac.sh`: create a local macOS virtual environment, install
  `requirements-mac.txt`, build `llama-cpp-python` with Metal enabled, and install
  `vllm` from `scratch/vllm-source`
- `bootstrap_hpc.sh`: create a virtual environment and install
  `requirements-hpc.txt` with uv's `unsafe-best-match` index strategy, then build
  `llama-cpp-python` with CUDA enabled

Thin wrappers live here and call into package code under `src/`.

Current deployment wrappers:

- `scripts/deployment/macos/setup_llama_cpp.sh`
- `scripts/deployment/macos/verify_llama_cpp_e2e.sh`
- `scripts/deployment/macos/verify_vllm_e2e.sh`
- `scripts/deployment/macos/run_chat_window.sh`
- `scripts/deployment/hpc/setup_env.sh`
- `scripts/deployment/hpc/fetch_model.sh`
- `scripts/deployment/hpc/check_vllm_status.sh`
- `scripts/deployment/hpc/stop_vllm_serve.sh`
- `scripts/deployment/hpc/verify_vllm_serve.sh`
- `scripts/deployment/hpc/llama_cpp_smoke.sbatch`
- `scripts/deployment/hpc/vllm_smoke.sbatch`
- `scripts/deployment/hpc/vllm_serve.sbatch`
- `scripts/deployment/hpc/submit_llama_cpp_smoke.sh`
- `scripts/deployment/hpc/submit_vllm_smoke.sh`
- `scripts/deployment/hpc/submit_vllm_serve.sh`

The HPC `verify_vllm_serve.sh` wrapper stores timestamped test logs under
`verification/`.
