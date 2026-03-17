from llm_local.core.runtime import build_runtime_summary


def test_build_runtime_summary_defaults_to_macos_local() -> None:
    summary = build_runtime_summary({}, platform_name="Darwin", python_version="3.12.2")

    assert summary.platform_name == "Darwin"
    assert summary.execution_target == "macos-local"
    assert summary.python_version == "3.12.2"
    assert summary.cuda_visible_devices is None
    assert summary.slurm_job_id is None


def test_build_runtime_summary_detects_linux_hpc_gpu_context() -> None:
    summary = build_runtime_summary(
        {"CUDA_VISIBLE_DEVICES": "0", "SLURM_JOB_ID": "12345"},
        platform_name="Linux",
        python_version="3.12.2",
    )

    assert summary.platform_name == "Linux"
    assert summary.execution_target == "linux-hpc-gpu"
    assert summary.cuda_visible_devices == "0"
    assert summary.slurm_job_id == "12345"
