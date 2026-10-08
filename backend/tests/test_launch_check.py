"""
Unit tests for launch_check.py -- no LLM, no Mongo, no network.

Fixtures are two real blueprints HIC generated (generated content only):
- reentry_before / lead_radar_before: the code exactly as HIC returned it,
  with no Launch Path.
- reentry_after: the same system after a first-timer walk-through -- fixed
  bot, dependency file, start command, settings template, and a Launch Path
  that was followed from a clean install to "Streak: 1".
"""
import copy
import json
from pathlib import Path

from launch_check import check_launch_path

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIXTURES / f"{name}.json").read_text())


def thin_path(**extra):
    """The kind of Launch Path a first-timer can't follow."""
    step = {"step": "Deploy it", "do": "Deploy to Railway.", "uses_files": ["checkin_bot.py"]}
    lp = {"goal": "Bot is live", "steps": [step]}
    lp.update(extra)
    return lp


def test_blueprint_with_no_launch_path_is_flagged():
    result = check_launch_path(load("reentry_before"))
    assert result["ok"] is False
    assert result["has_launch_path"] is False
    assert "No Launch Path" in result["problems"][0]


def test_walked_through_reentry_blueprint_passes():
    result = check_launch_path(load("reentry_after"))
    assert result == {"ok": True, "has_launch_path": True, "problems": []}


def test_thin_path_on_original_reentry_code_names_every_gap():
    bp = load("reentry_before")
    bp["launch_path"] = thin_path()
    problems = check_launch_path(bp)["problems"]
    joined = "\n".join(problems)
    assert "Step 1 (Deploy it) doesn't say how you'll know it worked." in problems
    assert "schema.sql is included, but no step says what to do with it." in problems
    assert "checkin_bot.py needs SUPABASE_DB_URL" in joined
    assert "checkin_bot.py uses the flask package, but nothing says to install it." in problems
    assert "checkin_bot.py uses the psycopg2 package, but nothing says to install it." in problems
    assert "There's no final test that proves the whole thing works." in problems


def test_lead_radar_needs_requests_installed():
    bp = load("lead_radar_before")
    bp["launch_path"] = {
        "steps": [
            {"step": "Run it", "do": "Run python lead_radar.py", "uses_files": ["lead_radar.py"], "check": "It prints Done."}
        ],
        "done_test": "leads.db has rows",
    }
    problems = check_launch_path(bp)["problems"]
    assert problems == ["lead_radar.py uses the requests package, but nothing says to install it."]


def test_step_pointing_at_a_missing_file_is_flagged():
    bp = load("reentry_after")
    bp["launch_path"]["steps"][0]["uses_files"].append("seed_resources.sql")
    problems = check_launch_path(bp)["problems"]
    assert problems == ["Step 1 (Put the files on GitHub) uses seed_resources.sql, but that file isn't included."]


def test_removing_the_dependency_file_is_caught():
    bp = load("reentry_after")
    bp["executable_output"]["artifacts"] = [
        a for a in bp["executable_output"]["artifacts"] if a["filename"] != "requirements.txt"
    ]
    for step in bp["launch_path"]["steps"]:
        step["uses_files"] = [f for f in step["uses_files"] if f != "requirements.txt"]
        step["do"] = step["do"].replace("requirements.txt, ", "")
    problems = check_launch_path(bp)["problems"]
    assert "checkin_bot.py uses the twilio package, but nothing says to install it." in problems
    assert "checkin_bot.py uses the werkzeug package, but nothing says to install it." in problems


def test_unexplained_env_var_is_caught():
    bp = load("reentry_after")
    bot = next(a for a in bp["executable_output"]["artifacts"] if a["filename"] == "checkin_bot.py")
    bot["content"] += '\nSENTRY_DSN = os.environ["SENTRY_DSN"]\n'
    problems = check_launch_path(bp)["problems"]
    assert problems == ["checkin_bot.py needs SENTRY_DSN, but no step says where to get it or where to set it."]


def test_python_that_does_not_parse_is_caught():
    bp = copy.deepcopy(load("reentry_after"))
    bot = next(a for a in bp["executable_output"]["artifacts"] if a["filename"] == "checkin_bot.py")
    bot["content"] = "def broken(:\n    pass\n"
    problems = check_launch_path(bp)["problems"]
    assert problems == ["checkin_bot.py isn't valid Python (line 1), so it won't run as written."]


def test_javascript_packages_and_env_vars():
    bp = {
        "executable_output": {"artifacts": [{
            "filename": "server.js", "language": "javascript",
            "content": 'const express = require("express");\nconst fs = require("fs");\n'
                       'const { helper } = require("./helper");\nconst key = process.env.STRIPE_KEY;\n',
        }]},
        "launch_path": {
            "steps": [{"step": "Start", "do": "node server.js", "uses_files": ["server.js"], "check": "It listens"}],
            "done_test": "curl localhost:3000",
        },
    }
    problems = check_launch_path(bp)["problems"]
    assert problems == [
        "server.js needs STRIPE_KEY, but no step says where to get it or where to set it.",
        "server.js uses the express package, but nothing says to install it.",
    ]


def test_empty_or_missing_content_does_not_crash():
    assert check_launch_path({})["has_launch_path"] is False
    assert check_launch_path(None)["ok"] is False


def test_settings_with_a_default_are_not_flagged():
    bp = {
        "executable_output": {"artifacts": [
            {"filename": "app.py", "language": "python", "content":
                'import os\nPORT = int(os.environ.get("PORT", 5000))\nTZ = os.getenv("TZ_NAME", "UTC")\n'
                'KEY = os.getenv("API_KEY")\n'},
            {"filename": "index.js", "language": "javascript", "content":
                'const port = process.env.PORT || 3000;\nconst mode = process.env.MODE ?? "dev";\n'
                'const secret = process.env.SECRET;\n'},
        ]},
        "launch_path": {
            "steps": [{"step": "Run", "do": "python app.py and node index.js", "uses_files": ["app.py", "index.js"],
                       "check": "Both start"}],
            "done_test": "Both respond",
        },
    }
    assert check_launch_path(bp)["problems"] == [
        "app.py needs API_KEY, but no step says where to get it or where to set it.",
        "index.js needs SECRET, but no step says where to get it or where to set it.",
    ]
