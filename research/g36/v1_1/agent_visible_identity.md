# Agent-visible identity — G36 vs G36-v1.1

Tool: `tools/g36_v11/agent_visible_identity.py` → `agent_visible_identity.json`.

- **Source comparison: PASS.** 16 agent-visible artefacts (instruction, Dockerfile, the whole workspace
  tree including the warehouse database), **0 differing**. Manifest digest `7eea3d3745160c89` for both.
- **Built-image `/workspace` comparison: NOT RUN.** It needs both images built, and the build stage
  was not reached because calibration halted first.
