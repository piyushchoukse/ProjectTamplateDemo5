#!/usr/bin/env python3
"""Generate a basic iOS project folder structure and optionally create a Jira bug."""

from __future__ import annotations

import argparse
import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Folder structure helpers
# ---------------------------------------------------------------------------


def parse_features(raw: str | None) -> list[str]:
    if not raw:
        return []
    features: list[str] = []
    for item in raw.split(","):
        name = item.strip()
        if not name:
            continue
        normalized = name[:1].upper() + name[1:]
        if normalized not in features:
            features.append(normalized)
    return features


def build_structure(features: list[str], include_tests: bool) -> list[str]:
    folders = [
        "App",
        "Resources/Assets.xcassets",
        "Resources/Localizations",
        "Core/Models",
        "Core/Networking",
        "Core/Utilities",
        "Core/Extensions",
        "Modules",
        "Services",
        "SupportingFiles/Configs",
        "SupportingFiles/Constants",
    ]

    for feature in features:
        folders.extend(
            [
                f"Modules/{feature}/View",
                f"Modules/{feature}/ViewModel",
                f"Modules/{feature}/Model",
            ]
        )

    if include_tests:
        folders.extend(["Tests/UnitTests", "Tests/UITests"])

    return folders


def create_structure(base_path: Path, folders: list[str]) -> None:
    for folder in folders:
        (base_path / folder).mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Jira helpers
# ---------------------------------------------------------------------------


def _jira_auth_header(email: str, api_token: str) -> str:
    credentials = f"{email}:{api_token}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def create_jira_bug(
    jira_url: str,
    email: str,
    api_token: str,
    project_key: str,
    summary: str,
    description: str,
) -> dict:
    """Create a Bug issue in the given Jira project and return the response JSON."""
    url = jira_url.rstrip("/") + "/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            },
            "issuetype": {"name": "Bug"},
        }
    }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": _jira_auth_header(email, api_token),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise SystemExit(
            f"Jira API error {exc.code}: {exc.reason}\n{body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach Jira at '{jira_url}': {exc.reason}") from exc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a basic iOS project structure from user input "
            "and optionally file a Bug on a Jira board."
        )
    )
    parser.add_argument(
        "project_name",
        nargs="?",
        help="Project folder name. If omitted, you will be prompted.",
    )
    parser.add_argument(
        "--base-path",
        default=".",
        help="Where to create the project folder (default: current directory).",
    )
    parser.add_argument(
        "--features",
        default="",
        help="Comma-separated feature module names (e.g. Auth,Profile).",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Create UnitTests and UITests folders.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow using an existing non-empty project directory.",
    )

    jira = parser.add_argument_group(
        "Jira",
        "Options for filing a Bug on a Jira board. "
        "Credentials can also be supplied via environment variables "
        "JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY.",
    )
    jira.add_argument("--jira-url", help="Jira instance base URL (e.g. https://yourorg.atlassian.net).")
    jira.add_argument("--jira-email", help="Atlassian account email used for API authentication.")
    jira.add_argument("--jira-api-token", help="Jira API token (generated at id.atlassian.com).")
    jira.add_argument("--jira-project", help="Jira project key where the Bug will be created (e.g. MYAPP).")
    jira.add_argument(
        "--skip-jira",
        action="store_true",
        help="Skip Jira bug creation even if credentials are available.",
    )

    return parser.parse_args()


def main() -> None:
    args = get_args()

    # --- Project name ---
    project_name = args.project_name or input("Project name: ").strip()
    if not project_name:
        raise SystemExit("Project name is required.")

    # --- Build folder structure ---
    features = parse_features(args.features)
    root = Path(args.base_path).expanduser().resolve() / project_name

    if root.exists() and any(root.iterdir()) and not args.force:
        raise SystemExit(
            f"Directory '{root}' already exists and is not empty. Use --force to continue."
        )

    root.mkdir(parents=True, exist_ok=True)
    structure = build_structure(features, include_tests=args.include_tests)
    create_structure(root, structure)

    print(f"Created iOS template at: {root}")
    if features:
        print("Added feature modules:", ", ".join(features))

    # --- Jira bug creation ---
    if args.skip_jira:
        return

    jira_url = args.jira_url or os.environ.get("JIRA_URL", "")
    jira_email = args.jira_email or os.environ.get("JIRA_EMAIL", "")
    jira_api_token = args.jira_api_token or os.environ.get("JIRA_API_TOKEN", "")
    jira_project = args.jira_project or os.environ.get("JIRA_PROJECT_KEY", "")

    missing: list[str] = []
    if not jira_url:
        missing.append("jira-url / JIRA_URL")
    if not jira_email:
        missing.append("jira-email / JIRA_EMAIL")
    if not jira_api_token:
        missing.append("jira-api-token / JIRA_API_TOKEN")
    if not jira_project:
        missing.append("jira-project / JIRA_PROJECT_KEY")

    if missing:
        print(
            "\nSkipping Jira bug creation – missing credential(s): "
            + ", ".join(missing)
            + "\nPass them via CLI flags or environment variables, or use --skip-jira to suppress this message."
        )
        return

    summary = f"[{project_name}] Initial project scaffolding"
    description = (
        f"iOS project '{project_name}' was scaffolded using the iOS template generator.\n\n"
        f"Root path: {root}\n"
        f"Feature modules: {', '.join(features) if features else 'none'}\n"
        f"Tests included: {'yes' if args.include_tests else 'no'}\n\n"
        "Please review the generated structure and update this bug with any "
        "issues found during project setup."
    )

    print("\nCreating Jira bug …")
    result = create_jira_bug(
        jira_url=jira_url,
        email=jira_email,
        api_token=jira_api_token,
        project_key=jira_project,
        summary=summary,
        description=description,
    )

    issue_key = result.get("key", "<unknown>")
    issue_url = jira_url.rstrip("/") + "/browse/" + issue_key
    print(f"Jira bug created: {issue_key}  →  {issue_url}")


if __name__ == "__main__":
    main()
