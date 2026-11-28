#!/usr/bin/env python3
"""Exercise native Zsh's parse-only and normal execution paths in a temporary home."""
import subprocess, sys, tempfile
from pathlib import Path

z = sys.argv[1] if len(sys.argv) > 1 else "/AOK/native/zsh"
cases = {
    "unknown": "aok_test_unknown_command\n",
    "multiple": "aok_test_unknown_command\n:\n",
    "function": "f() { :; }\nf\n",
    "function side effect": "f() { : > marker; }\nf\n",
    "pipeline": "printf hi | cat > marker\n",
    "substitution": "x=$(printf hi > marker)\n",
    "background": ": > marker &\nwait\n",
    "timed": "time : > marker\n",
    "conditional": "if true; then : > marker; fi\n",
    "late parse error": ":\nf() {\n",
    "invalid": "f() {\n",
}
failed = 0
with tempfile.TemporaryDirectory() as d:
    home = Path(d)
    env = {"HOME": d, "PATH": "/AOK/native:/usr/bin:/bin",
           "LANG": "C.UTF-8", "TERM": "dumb"}
    for name, code in cases.items():
        for mode in ("file", "stdin", "command"):
            path = home / "case.zsh"
            path.write_text(code)
            args = [z, "-f", "-n"] + ([str(path)] if mode == "file" else
                    ["-c", code] if mode == "command" else [])
            r = subprocess.run(args, input=code if mode == "stdin" else None,
                               env=env, cwd=d, text=True, capture_output=True, timeout=30)
            invalid = name in ("invalid", "late parse error")
            parse_ok = (r.returncode != 0 and "parse error" in r.stderr
                        if invalid else r.returncode == 0 and not r.stderr)
            ok = (parse_ok and not r.stdout and not (home / "marker").exists()
                  and "subshell state did not finish" not in r.stderr)
            print(f'[{"PASS" if ok else "FAIL"}] {name} / {mode}: '
                  f'exit={r.returncode}, stderr={r.stderr.strip()!r}')
            failed += not ok
            (home / "marker").unlink(missing_ok=True)
    runtime = [
        ("f() { print OK; }; f", "OK\n"),
        ('x=$(printf OK); print -r -- "$x"', "OK\n"),
        ("(print OK)", "OK\n"),
        ("printf OK | cat", "OK"),
        ("false || print OK", "OK\n"),
        ("true && print OK", "OK\n"),
    ]
    for code, expected in runtime:
        r = subprocess.run([z, "-f", "-c", code], env=env, cwd=d,
                           text=True, capture_output=True, timeout=30)
        ok = r.returncode == 0 and r.stdout == expected and not r.stderr
        print(f'[{"PASS" if ok else "FAIL"}] runtime {code}')
        failed += not ok
sys.exit(bool(failed))
