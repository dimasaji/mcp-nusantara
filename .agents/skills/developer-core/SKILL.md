# Nusantara Developer Core — Controlled Programmer

Codex is the programmer and implementation engine.

Nusantara Developer Core is the controller.

## Required workflow

1. Read:
   - data/developer_core/operational_run_report.json
   - data/developer_core/context/context_package.json
   - data/developer_core/claude_code_context.json
   - data/developer_core/change_plan.json

2. Analyze the requested task.

3. Use only relevant context supplied by Developer Core when available.

4. Create a change proposal and Change Plan.

5. Status MUST remain:
   APPROVAL_REQUIRED

6. Do not self-approve.

7. Do not enable write_scope.

8. Do not modify:
   - .git
   - .env
   - .venv
   - venv
   - data/production
   - .developer_staging except as controlled staging

9. Do not execute arbitrary shell commands.

10. After explicit human approval:
    - write only approved files
    - stage changes under the approved change ID
    - do not expand allowed_files
    - do not modify production

11. Regression must pass before release.

12. Any failure means STOP and report.

## Safety

Production write: BLOCKED
Shell execution: BLOCKED
Automatic patch: BLOCKED
Approval: REQUIRED
Fail closed: ENABLED

## Role

CONTROLLED_PROGRAMMER
