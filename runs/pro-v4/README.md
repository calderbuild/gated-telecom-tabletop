# DeepSeek-V4-Pro runs (superseded, kept as a second-model record)

These are the first recorded runs, made with `deepseek-v4-pro` on 2026-10-05 before I switched every
agent to `deepseek-flash` for cost. The scored results in eval/ come from the Flash runs in runs/S1-S3.

- Code: the agent runs started on commit 8ebac41 (before the gate hardening in c780ee6). S2/run1 and the
  baselines ran on c780ee6 code.
- S1/run1 and S1/run3 are incomplete: I stopped them when switching models, so they have no run_end and
  `verify-log` reports them as aborted. Their chains are intact up to the stop.
- Every other log verifies (`python -m tabletop verify-log <file>`).

Use: the same gate and answer keys applied to a second model, to check the gated vs ungated contrast does
not depend on one model.
