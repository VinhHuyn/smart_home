# Project Agent Instructions

## Purpose
This agent keeps the project documentation in sync with the current workspace. It should scan the repository regularly, detect meaningful changes, update documentation under `docs/`, and maintain an up-to-date project tree.

## Documentation Sync Skill

### Trigger
Run this skill:
- every 1 hour while the agent is active;
- after any meaningful source, configuration, dependency, or infrastructure change;
- before committing changes that affect project structure or behavior.

### Scope
Scan the current workspace root, excluding generated or noisy paths:

- `.git/`
- `node_modules/`
- `.venv/`, `venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.mypy_cache/`
- `.ruff_cache/`
- `dist/`, `build/`, `coverage/`
- log files and temporary files

The documentation directory for this project is `docs/` under the canonical repository root `D:\smart_home` (`/mnt/d/smart_home`).
Never create, write, or sync docs under typo/alternate roots such as `D:\smarthome` (`/mnt/d/smarthome`). If such a path appears, treat it as invalid duplicate and clean it up after confirming canonical files exist in `D:\smart_home\docs`.

### Required Outputs
Maintain these files:

1. `docs/PROJECT_DOC.md`
   - High-level project overview.
   - Main components and responsibilities.
   - Important configuration files.
   - Services, APIs, scripts, or entry points discovered in the workspace.
   - Notable recent changes since the last scan.
   - Any assumptions or unresolved documentation gaps.

2. `docs/PROJECT_TREE.md`
   - A readable tree structure of the project.
   - Include important files and directories.
   - Exclude noisy/generated paths listed above.
   - Add short inline notes for important directories when helpful.

3. Optional supporting docs under `docs/` when the project grows:
   - `docs/API.md` for API routes/endpoints.
   - `docs/CONFIGURATION.md` for environment variables and config files.
   - `docs/DEVELOPMENT.md` for local setup, test commands, and dev workflow.

### Hourly Workflow
1. Identify repository root and inspect current files.
2. Build or refresh the project tree.
3. Read existing documentation in `docs/` to preserve useful manual notes.
4. Detect changes using Git when available:
   - `git status --short`
   - `git diff --stat`
   - recent changed files from the working tree
5. Inspect changed or important files before documenting them.
6. Update `docs/PROJECT_DOC.md` with accurate current information.
7. Update `docs/PROJECT_TREE.md` with the current tree.
8. Do not overwrite valuable human-written documentation without preserving it.
9. Keep documentation concise, factual, and based on files that actually exist.
10. Verify the docs were written successfully.

### Suggested Commands
Use these commands as references when the runtime allows shell access:

```bash
# Show changed files
git status --short

# Show change summary
git diff --stat

# Generate a clean project tree without common noise
python3 - <<'PY'
from pathlib import Path

root = Path('.')
exclude_dirs = {
    '.git', 'node_modules', '.venv', 'venv', '__pycache__',
    '.pytest_cache', '.mypy_cache', '.ruff_cache', 'dist', 'build', 'coverage'
}
exclude_suffixes = {'.log', '.tmp', '.swp'}

lines = ['# Project Tree', '']

def walk(path: Path, prefix: str = ''):
    entries = sorted(
        [p for p in path.iterdir()
         if not (p.is_dir() and p.name in exclude_dirs)
         and not any(p.name.endswith(s) for s in exclude_suffixes)],
        key=lambda p: (not p.is_dir(), p.name.lower())
    )
    for index, entry in enumerate(entries):
        connector = '└── ' if index == len(entries) - 1 else '├── '
        lines.append(f'{prefix}{connector}{entry.name}{"/" if entry.is_dir() else ""}')
        if entry.is_dir():
            extension = '    ' if index == len(entries) - 1 else '│   '
            walk(entry, prefix + extension)

walk(root)
Path('docs').mkdir(exist_ok=True)
Path('docs/PROJECT_TREE.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
PY
```

### Documentation Quality Rules
- Prefer facts from the workspace over assumptions.
- If a file's purpose is unclear, label it as unclear rather than guessing.
- Keep generated docs stable and easy to diff.
- Do not document secrets or private tokens.
- Do not include full contents of large source files; summarize their purpose.
- If both `doc/` and `docs/` exist, prefer `docs/` unless the project clearly uses `doc/`.

### Completion Checklist
Before finishing a documentation sync, confirm:

- [ ] `docs/PROJECT_DOC.md` reflects the current workspace.
- [ ] `docs/PROJECT_TREE.md` reflects the current tree.
- [ ] Generated/noisy directories are excluded.
- [ ] Any changed files were inspected before being summarized.
- [ ] No secrets were copied into documentation.
