# WODCraft

English | [Français](README.fr.md)

WODCraft is a Domain‑Specific Language (DSL) to describe, validate, and export Workouts of the Day (WODs). It ships a single, unified CLI to parse, lint, compile sessions, and export (JSON/ICS), with support for tracks and gender through a movements catalog.

## Why
- Standardize how WODs are written, readable by coaches and tools.
- Automate useful formats: timer timeline, calendar, web, API.
- Normalize variants (tracks, dual reps/cals/loads) via a JSON catalog.
- Provide a solid base for AI agents to analyze/generate WODs.

## DSL at a Glance
```wod
WOD "Team Mixer"
TEAM 2
TRACKS [RX, INTERMEDIATE, SCALED]
CAP 20:00

BUYIN {
  400m run;
}

BLOCK AMRAP 12:00 WORK split:any {
  12 wall_balls @9kg SYNC;
  10 box_jumps @24in;
  200m run;
}

CASHOUT {
  50 double_unders @each;
}
```
The full grammar and rules are in WODCraft_spec.md (source of truth).

## Features
- Parser → structured JSON AST.
- Linter → errors/warnings (e.g., E010 REST>0, E020 EMOM without slots, W001 unknown movement, W002 suspicious load, W050 alias).
- Resolution → applies `--track`/`--gender` and an optional JSON `--catalog`.
- Timeline → `run` produces an event sequence (text or JSON).
- Export → `export` to `json`, `html`, `ics`.
- Formatting → `fmt` (minimal safe normalization of `.wod` files).

## Quick Setup
- Python 3 recommended. Isolated env:
  - `make install` (creates `.venv` and installs `requirements.txt`)
  - or `pip install -r requirements.txt`

## CLI Usage (unified)
- Validate: `wodc validate examples/language/team_realized_session.wod`
- Parse: `wodc parse examples/language/team_realized_session.wod`
- Session → JSON/ICS: `wodc session examples/language/team_realized_session.wod --modules-path modules --format json`
- Results aggregate: `wodc results examples/language/team_realized_session.wod --modules-path modules`
- Catalog build: `wodc catalog build`

Makefile shortcuts: `make help` (venv, install, test, catalog-build, vnext-validate, vnext-session, vnext-results, build-dist).

## Tests
- Run: `make test` or `pytest -q`
- Coverage includes: parser, lint (E/W), resolution (catalog/gender), timeline, formatter.

## Spec and Architecture
- DSL spec: see `WODCraft_spec.md`.
- Unified CLI: `src/wodcraft/cli.py` (entrypoint `wodc`).
- Language core: `src/wodcraft/lang/core.py` (façade over vNext core).
- vNext core: `wodc_vnext/core.py` (modules/sessions/types), slated to be merged under `src/`.
- Examples under `examples/` and modules under `modules/`. Movements catalog at `data/movements_catalog.json`.

## Editor Support
- VS Code/Windsurf extension (local): see `editor/wodcraft-vscode/` for syntax highlighting and snippets.
- Quick dev run: `code --extensionDevelopmentPath=./editor/wodcraft-vscode .`

## Examples (Language / Programming)
- `examples/language/programming_plan.wod`: minimal “Coach Programming” block
- `examples/language/team_realized_session.wod`: session with team + realized events for aggregation

## Roadmap
- Advanced formatter (indentation/blocks), macros and shorthands (`21-15-9`).
- Versioned grammar and canonical `wodc fmt`.
- Executable timer for gym use.

## Contributing
- Read `AGENTS.md` (conventions, structure, commands).
- Open focused PRs with CLI examples and export artifacts.

## 📜 License

- **Code (DSL, tools, generators)** : [Apache 2.0](./LICENSE)  
- **Content (docs, movement list, examples, images/videos)** : [CC-BY-SA 4.0](./LICENSE-docs)  

In summary:  
You can freely use WODCraft in your projects, including commercial ones, as long as you cite the source.  
Content (movements, docs, etc.) must remain open and under the same CC-BY-SA license.

---

© 2025 Nicolas Caussin - caussin@aumana-consulting.com
