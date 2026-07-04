# AGENTS.md

## What this is

Translation overlay tool for "Tokimeki Memorial: Forever With You" (PS1). Reads game text via visual character recognition, matches against a CSV translation database, and displays translated text in an overlay. Falls back to machine translation (DeepL/OpenAI/Google) for untranslated lines.

## Setup

- Python 3.11 required
- `pip install -e . --config-settings editable_mode=compat` — editable install for dev
- Entry point: `xeupiu` CLI command (defined in `pyproject.toml`)

## Run

- `xeupiu` — launches GUI control panel + overlay
- `xeupiu --screenshot <path>` — saves debug screenshot of game window and exits

## Packaging

- `./package_executable.sh` (Linux) or `package_executable.bat` (Windows)
- Uses PyInstaller; copies `data/` dirs and `config_generic.json` into `dist/xeupiu/`

## Architecture

- `src/xeupiu/xeupiu.py` — CLI entry, tkinter control panel, main loop
- `src/xeupiu/app.py` — core orchestrator: screenshot → OCR → translate → overlay
- `src/xeupiu/config.py` — reads `config.json`, singleton `CONFIG` object
- `src/xeupiu/poorcr.py` — visual character recognition engine
- `src/xeupiu/{linux,windows}/screenshot.py` — platform-specific window capture
- `src/xeupiu/translator.py` — machine translation backend (DeepL/OpenAI/Google)
- `data/texts/*.csv` — translation databases (names, text, notebook, confessions, epilogues)
- `scripts/char_db_script.py` — generates character image DB from source PNGs

## graphify

- Knowledge graph lives in `graphify-out/` (graph.json, GRAPH_REPORT.md, graph.html)
- Auto-rebuilds on every commit via git post-commit hook
- To query: `graphify query "<question>"` or open `graphify-out/graph.html` in browser
- To rebuild manually: `graphify .` or `graphify --update` for incremental
- Before answering codebase questions, check the graph first — it has community detection and cross-file relationships you won't find by grepping

## Gotchas

- `config.json` contains API keys — never commit. `config_generic.json` is the clean template.
- `data/characters/` is gitignored — needed only for `char_db_script.py`
- No test suite, no linter, no type checker configured
- Platform branching via `sys.platform` checks (Windows vs Linux) in config and screenshot modules
- Config paths are relative to CWD, not the package install location
- `config.json` is read/written at runtime by `Configuration.save()` — changes persist
