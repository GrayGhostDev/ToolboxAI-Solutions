# ToolboxAI Solutions (monorepo)

Notes for developers

- This repository uses Pydantic v2 and `pydantic-settings` for configuration.
- The canonical settings are in `toolboxai_settings/settings.py` and both server
  wrappers import the shared `settings` instance.

IDE setup

- Point Cursor/VS Code Python interpreter to:

  /Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/venv/bin/python

- Reload the window after changing the interpreter so pyright picks up installed packages.

Running tests (local)

Install dependencies into your venv and run the settings test (Python 3.11+):

```bash
python -m pip install -r ToolboxAI-Roblox-Environment/requirements.txt
python -m pytest ToolboxAI-Roblox-Environment/tests/test_settings.py
```

Compatibility

- A small compatibility adapter exists at `toolboxai_settings/compat.py` to help
  if you must run under pydantic v1; however the shared settings are v2-first.

CI

- CI runs a lightweight matrix (Python 3.11/3.12) that executes pyright and the
  `tests/test_settings.py` test.
