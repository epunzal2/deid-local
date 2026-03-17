# HPC GLIBC and Partition Compatibility Note

This note captures a cluster-specific compatibility finding from manual validation
on 2026-03-06.

## Finding

Different GPU partitions are running different base OS/libc stacks:

- Login node example (`amarel3`): `glibc 2.34`
- Legacy GPU partition node example (`gpu020`): `glibc 2.17`

When dependencies were resolved on a newer-glibc node and then executed on an older
glibc GPU node, imports failed with errors similar to:

```text
ImportError: /lib64/libc.so.6: version `GLIBC_2.28' not found
```

## Direction

Target the RHEL9 GPU partition for deployment and validation:

- `gpu-redhat`

The HPC vLLM submission defaults in this repository are set to `gpu-redhat`.
Bootstrap defaults also target modern manylinux (`x86_64-manylinux_2_28`) resolution
to match the RHEL9 GPU environment.

Legacy `gpu`/CentOS7-style nodes are not the default deployment target in this repo.

## Operational Guidance

1. Submit serving jobs to `gpu-redhat` explicitly when needed:
   - `scripts/deployment/hpc/submit_vllm_serve.sh --partition gpu-redhat ...`
2. Keep environment bootstrapping aligned with compute compatibility by using the
   repository bootstrap script defaults.
3. If troubleshooting ABI issues, compare `glibc` directly on login and compute
   nodes:

```bash
ldd --version | head -n1
getconf GNU_LIBC_VERSION
```
