#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def detect_mode_from_text(text: str) -> str:
    t = text
    if any(kw in t for kw in ("programming",)):
        return "vnext"
    if any(kw in t for kw in ("module ", "session ", "vars {", "imports ", "components {", "realized {", "achievements {")):
        return "vnext"
    if any(kw in t for kw in ("WOD ", "BLOCK ", "AMRAP", "EMOM", "RFT", "FT")):
        return "legacy"
    return "legacy"


def cmd_lint(args):
    p = Path(args.file)
    text = p.read_text()
    mode = args.mode or detect_mode_from_text(text)
    # language-first only
    # Prefer programming lint if block present; else validate
    from wodcraft.lang.core import ProgrammingLinter, parse_vnext
    if "programming" in text:
        ast = parse_vnext(text)
        reports = []
        for blk in ast.get("programming", []):
            data = blk.get("data", {})
            issues = ProgrammingLinter().lint(data)
            reports.append({"programming": data.get("macrocycle", {}).get("name"), "issues": issues})
        print(json.dumps({"reports": reports}, indent=2))
        return 2 if any(any(i.get("level") == "error" for i in r.get("issues", [])) for r in reports) else 0
    else:
        # Lint modules: find common structural issues
        try:
            ast = parse_vnext(text)
        except Exception as e:
            print(f"✗ Invalid syntax: {e}")
            return 1
        issues = []
        modules = ast.get("modules", [])
        for m in modules:
            mid = m.get("id", "<module>")
            body = m.get("body")
            comps = []
            # Flatten containers
            def collect(node):
                if isinstance(node, dict):
                    t = node.get("type")
                    if t in ("WARMUP","WOD","SKILL","STRENGTH"):
                        comps.append(node)
                    elif t in ("MODULE_BODY","BODY"):
                        for ch in node.get("children", []):
                            collect(ch)
                    else:
                        # attempt to collect nested dicts
                        for v in node.values():
                            collect(v)
                elif isinstance(node, list):
                    for v in node: collect(v)
            collect(body)
            if not comps:
                issues.append(("warning","M101", f"Module '{mid}' has no components"))
            for c in comps:
                ct = c.get("type")
                if ct == "WOD":
                    mv = c.get("movements") or []
                    if not mv:
                        issues.append(("warning","M102", f"WOD in '{mid}' has no movements"))
                elif ct == "WARMUP":
                    bl = c.get("blocks") or []
                    if not bl:
                        issues.append(("warning","M103", f"Warmup in '{mid}' has no blocks"))
                elif ct in ("SKILL","STRENGTH"):
                    wk = c.get("work") or {}
                    lines = wk.get("lines") or []
                    if not lines:
                        issues.append(("warning","M104", f"{ct.title()} in '{mid}' has no work lines"))
        if issues:
            for lvl, code, msg in issues:
                print(f"{lvl.upper()} {code} {args.file}: {msg}")
        else:
            print("✓ Valid WODCraft syntax")
        # Treat warnings as success
        return 0


def cmd_parse(args):
    text = Path(args.file).read_text()
    mode = args.mode or detect_mode_from_text(text)
    if mode == "legacy":
        # Legacy not supported in clean mode — fallback to language parser
        from wodcraft.lang.core import parse_vnext
        ast = parse_vnext(text)
    else:
        from wodcraft.lang.core import parse_vnext
        ast = parse_vnext(text)
    print(json.dumps(ast, indent=2))
    return 0


def cmd_run(args):
    # legacy only
    print("Legacy 'run' not supported in clean language-first mode.")
    return 1


def cmd_export(args):
    # legacy only, thin shim to JSON/HTML/ICS via existing module
    print("Legacy 'export' not supported in clean language-first mode.")
    return 1


def cmd_validate(args):
    text = Path(args.file).read_text()
    from wodcraft.lang.core import parse_vnext
    try:
        parse_vnext(text)
        print("✓ Valid WODCraft vNext syntax")
        return 0
    except Exception as e:
        print(f"✗ Invalid syntax: {e}")
        return 1


def cmd_session(args):
    from wodcraft.lang.core import parse_vnext, FileSystemResolver, SessionCompiler
    text = Path(args.file).read_text()
    ast = parse_vnext(text)
    if not ast.get("sessions"):
        print("✗ No session found in file")
        return 1
    resolver = FileSystemResolver(Path(args.modules_path))
    compiler = SessionCompiler(resolver)
    session_ast = ast["sessions"][0]
    compiled = compiler.compile_session(session_ast)
    if args.format == "json":
        print(compiler.export_json(compiled))
    elif args.format == "ics":
        print(compiler.export_ics(compiled))
    else:
        print(json.dumps(compiled, indent=2))
    return 0


def cmd_results(args):
    from wodcraft.lang.core import parse_vnext, FileSystemResolver, SessionCompiler, TeamRealizedAggregator
    text = Path(args.file).read_text()
    ast = parse_vnext(text)
    if not ast.get("sessions"):
        print("✗ No session found in file")
        return 1
    resolver = FileSystemResolver(Path(args.modules_path))
    compiler = SessionCompiler(resolver)
    session_ast = ast["sessions"][0]
    compiled = compiler.compile_session(session_ast)
    results = compiled.get("session", {}).get("results")
    if not results:
        results = TeamRealizedAggregator().aggregate(session_ast, compiled.get("session", {})) or {}
    print(json.dumps({"results": results}, indent=2))
    return 0


def cmd_catalog_build(args):
    # thin wrapper
    from scripts.build_catalog import main as build
    build()
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wodc", description="Unified WODCraft CLI (legacy + vNext)")
    sub = ap.add_subparsers(dest="cmd")

    p_parse = sub.add_parser("parse")
    p_parse.add_argument("file")
    p_parse.add_argument("--mode", choices=["legacy", "vnext"])
    p_parse.set_defaults(func=cmd_parse)

    p_lint = sub.add_parser("lint")
    p_lint.add_argument("file")
    p_lint.add_argument("--mode", choices=["legacy", "vnext"])
    p_lint.set_defaults(func=cmd_lint)

    p_run = sub.add_parser("run")
    p_run.add_argument("file")
    p_run.add_argument("--format", choices=["text", "json"], default="text")
    p_run.set_defaults(func=cmd_run)

    p_export = sub.add_parser("export")
    p_export.add_argument("file")
    p_export.add_argument("--to", choices=["json", "html", "ics"], required=True)
    p_export.set_defaults(func=cmd_export)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("file")
    p_validate.set_defaults(func=cmd_validate)

    p_session = sub.add_parser("session")
    p_session.add_argument("file")
    p_session.add_argument("--modules-path", default="modules")
    p_session.add_argument("--format", choices=["json", "ics"], default="json")
    p_session.set_defaults(func=cmd_session)

    p_results = sub.add_parser("results")
    p_results.add_argument("file")
    p_results.add_argument("--modules-path", default="modules")
    p_results.set_defaults(func=cmd_results)

    p_cat = sub.add_parser("catalog")
    p_cat_sub = p_cat.add_subparsers(dest="cat_cmd")
    p_cat_build = p_cat_sub.add_parser("build")
    p_cat_build.set_defaults(func=cmd_catalog_build)

    args = ap.parse_args(argv)
    if not hasattr(args, "func"):
        ap.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
