"""
Launch check: does a blueprint tell a first-timer how to get its code running?

Deterministic -- no LLM. The prompt asks the model for a launch_path that
uses every file, explains every environment variable and installs every
package; this module checks the model actually did, so the blueprint page
can say so plainly instead of leaving someone stuck with a file and a Copy
button.

Checks:
- there is a launch_path with steps and a done_test
- every step says how to tell it worked
- steps only use files that exist, and every file is used by some step
- every Python file parses
- every environment variable the code requires (no default) is explained in the path
- every third-party package the code imports is installed somewhere
"""
import ast
import json
import re
import sys

# Import name -> the name people actually install, where they differ.
PIP_NAME_ALIASES = {
    "cv2": "opencv",
    "PIL": "pillow",
    "bs4": "beautifulsoup4",
    "sklearn": "scikit-learn",
    "yaml": "pyyaml",
    "dateutil": "python-dateutil",
    "dotenv": "python-dotenv",
    "jwt": "pyjwt",
}

# Python 3.10+. On older interpreters the package check for Python is skipped
# rather than flagging every standard-library import.
PY_STDLIB = getattr(sys, "stdlib_module_names", None)

NODE_BUILTINS = {
    "assert", "buffer", "child_process", "crypto", "dns", "events", "fs", "http", "https",
    "net", "os", "path", "process", "querystring", "readline", "stream", "timers", "url",
    "util", "zlib", "worker_threads",
}

# Only settings the code can't run without: os.environ["X"], or .get/getenv
# with no default. os.environ.get("PORT", 5000) needs nothing from the user.
_PY_ENV = re.compile(
    r"""os\.environ\[\s*["']([A-Z][A-Z0-9_]*)["']\s*\]"""
    r"""|os\.(?:environ\.get|getenv)\(\s*["']([A-Z][A-Z0-9_]*)["']\s*\)"""
)
_JS_ENV = re.compile(
    r"""process\.env\.([A-Z][A-Z0-9_]*)\b(?!\s*(?:\|\||\?\?))"""
    r"""|process\.env\[\s*["']([A-Z][A-Z0-9_]*)["']\s*\](?!\s*(?:\|\||\?\?))"""
)
_INSTALL_CMD = re.compile(
    r"""(?:pip3?\s+install|npm\s+(?:install|i)|yarn\s+add|pnpm\s+add|poetry\s+add)\s+([\w\-.\[\]=<>~@/ ]+)"""
)
_PROSE_AFTER_COMMAND = re.compile(r"\s(?:then|and|to|in|from|with|so|if)\s|\.\s|\.$")
_JS_IMPORT = re.compile(r"""(?:require\(\s*|from\s+|import\s+)["']([^"'./][^"']*)["']""")


def _is_python(a: dict) -> bool:
    return (a.get("language") or "").lower() == "python" or (a.get("filename") or "").endswith(".py")


def _is_js(a: dict) -> bool:
    lang = (a.get("language") or "").lower()
    return lang in ("javascript", "typescript") or (a.get("filename") or "").endswith((".js", ".ts", ".mjs"))


def _python_imports(code: str) -> set:
    mods = set()
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.Import):
            mods.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            mods.add(node.module.split(".")[0])
    return mods


def _js_packages(code: str) -> set:
    pkgs = set()
    for spec in _JS_IMPORT.findall(code):
        if spec.startswith("node:"):
            continue
        # "@scope/pkg/sub" -> "@scope/pkg", "pkg/sub" -> "pkg"
        parts = spec.split("/")
        name = "/".join(parts[:2]) if spec.startswith("@") else parts[0]
        if name not in NODE_BUILTINS:
            pkgs.add(name)
    return pkgs


def check_launch_path(content: dict) -> dict:
    """Return {"ok": bool, "has_launch_path": bool, "problems": [plain-language strings]}."""
    content = content or {}
    artifacts = (content.get("executable_output") or {}).get("artifacts") or []
    lp = content.get("launch_path")
    problems = []

    if not isinstance(lp, dict) or not lp.get("steps"):
        problems.append(
            "No Launch Path: this blueprint doesn't say how to get its files running. "
            "Regenerate it to get step-by-step instructions."
        )
        return {"ok": False, "has_launch_path": isinstance(lp, dict), "problems": problems}

    steps = [s for s in lp.get("steps") or [] if isinstance(s, dict)]
    filenames = [a.get("filename") for a in artifacts if a.get("filename")]
    used = set()

    for i, step in enumerate(steps, 1):
        label = f"Step {i} ({step.get('step') or 'untitled'})"
        if not (step.get("check") or "").strip():
            problems.append(f"{label} doesn't say how you'll know it worked.")
        for f in step.get("uses_files") or []:
            if f in filenames:
                used.add(f)
            else:
                problems.append(f"{label} uses {f}, but that file isn't included.")

    for f in filenames:
        if f not in used:
            problems.append(f"{f} is included, but no step says what to do with it.")

    if not (lp.get("done_test") or "").strip():
        problems.append("There's no final test that proves the whole thing works.")

    # Env vars count as explained if the path mentions them anywhere. Packages
    # only count as installed if they're in a dependency file or an install
    # command -- "sign up for Twilio" doesn't install the twilio package.
    path_text = json.dumps(lp).lower()
    install_text = " ".join(
        (a.get("content") or "").lower()
        for a in artifacts
        if (a.get("filename") or "").lower() in ("requirements.txt", "package.json", "pyproject.toml")
    ) + " " + " ".join(_PROSE_AFTER_COMMAND.split(cmd)[0] for cmd in _INSTALL_CMD.findall(path_text))
    local_modules = {f.rsplit(".", 1)[0] for f in filenames}

    for a in artifacts:
        code = a.get("content") or ""
        name = a.get("filename") or "a file"
        env_vars = set()
        packages = set()
        if _is_python(a):
            try:
                mods = _python_imports(code)
            except SyntaxError as e:
                problems.append(f"{name} isn't valid Python (line {e.lineno}), so it won't run as written.")
                mods = set()
            if PY_STDLIB is not None:
                packages = {m for m in mods if m not in PY_STDLIB and m not in local_modules}
            env_vars = {next(g for g in m if g) for m in _PY_ENV.findall(code)}
        elif _is_js(a):
            packages = {p for p in _js_packages(code) if p not in local_modules}
            env_vars = {next(g for g in m if g) for m in _JS_ENV.findall(code)}

        for var in sorted(env_vars):
            if var.lower() not in path_text:
                problems.append(f"{name} needs {var}, but no step says where to get it or where to set it.")
        for pkg in sorted(packages):
            install_name = PIP_NAME_ALIASES.get(pkg, pkg).lower()
            if pkg.lower() not in install_text and install_name not in install_text:
                problems.append(f"{name} uses the {pkg} package, but nothing says to install it.")

    return {"ok": not problems, "has_launch_path": True, "problems": problems}
