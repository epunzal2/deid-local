# Scripts

Place thin wrappers and explicit environment bootstrap helpers here.

- `bootstrap_mac.sh`: create a local macOS virtual environment, install
  `requirements-mac.txt`, build `llama-cpp-python` with Metal enabled, and install
  `vllm` from `scratch/vllm-source`
- `bootstrap_hpc.sh`: create a virtual environment and install
  `requirements-hpc.txt`, then build `llama-cpp-python` with CUDA enabled
