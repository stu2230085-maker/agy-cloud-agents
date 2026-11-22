#!/usr/bin/env python3
"""Zero-dependency CLI helper for orchestrating GitHub Cloud Coding Agents via `gh` CLI."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence

AGENT_ALIASES: dict[str, str] = {
    "copilot": "copilot-swe-agent",
    "copilot-swe-agent": "copilot-swe-agent",
    "claude": "anthropic-code-agent",
    "anthropic": "anthropic-code-agent",
    "anthropic-code-agent": "anthropic-code-agent",
    "codex": "openai-code-agent",
    "openai": "openai-code-agent",
    "openai-code-agent": "openai-code-agent",
}

FALLBACK_BOT_IDS: dict[str, str] = {
    "copilot-swe-agent": "BOT_kgDOC9w8XQ",
    "anthropic-code-agent": "BOT_kgDODnPHJg",
    "openai-code-agent": "BOT_kgDODnSAjQ",
}


def parse_owner_repo(repo_str: str) -> tuple[str, str]:
    """Parse an 'owner/repo' string into `(owner, repo)`."""
    parts = [p.strip() for p in repo_str.strip().split("/") if p.strip()]
    if len(parts) != 2:
        raise ValueError(f"Expected repository in 'owner/repo' format, got: {repo_str!r}")
    return parts[0], parts[1]


def run_gh_json(args: list[str], input_data: dict[str, Any] | None = None) -> Any:
    """Execute a `gh` command, optionally passing JSON via `--input`, and parse JSON output."""
    cmd = ["gh", *args]
    if input_data is not None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as tmp:
            json.dump(input_data, tmp, ensure_ascii=False)
            tmp_path = Path(tmp.name)
        try:
            cmd.extend(["--input", str(tmp_path)])
            completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
        finally:
            tmp_path.unlink(missing_ok=True)
    else:
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)

    stdout = completed.stdout.strip()
    return json.loads(stdout) if stdout else {}


def fetch_repo_and_actors(owner: str, name: str) -> dict[str, Any]:
    """Query GitHub GraphQL API for repository Node ID and assignable actors."""
    payload = {
        "query": (
            "query GetRepoActors($owner: String!, $name: String!) {"
            "  repository(owner: $owner, name: $name) {"
            "    id"
            "    nameWithOwner"
            "    url"
            "    suggestedActors(capabilities: [CAN_BE_ASSIGNED], first: 20) {"
            "      nodes {"
            "        login"
            "        __typename"
            "        ... on Bot { id }"
            "        ... on User { id }"
            "      }"
            "    }"
            "  }"
            "}"
        ),
        "variables": {"owner": owner, "name": name},
    }
    response = run_gh_json(["api", "graphql"], input_data=payload)
    repo_data = response.get("data", {}).get("repository")
    if not repo_data:
        raise RuntimeError(f"Repository '{owner}/{name}' not found or inaccessible")

    actors: dict[str, dict[str, str]] = {}
    for node in repo_data.get("suggestedActors", {}).get("nodes", []):
        if node and "login" in node and "id" in node:
            actors[node["login"]] = {
                "login": node["login"],
                "id": node["id"],
                "type": node.get("__typename", "Unknown"),
            }
    return {
        "repository_id": repo_data["id"],
        "name_with_owner": repo_data["nameWithOwner"],
        "url": repo_data["url"],
        "actors": actors,
    }


def resolve_agent_ids(requested_agents: Sequence[str], discovered_actors: dict[str, dict[str, str]]) -> list[str]:
    """Resolve short agent names (`copilot`, `claude`, `codex`) or raw `BOT_...` IDs into GraphQL Node IDs."""
    resolved: list[str] = []
    for raw in requested_agents:
        token = raw.strip()
        if not token:
            continue
        if token.startswith("BOT_") or token.startswith("U_"):
            if token not in resolved:
                resolved.append(token)
            continue

        canonical_login = AGENT_ALIASES.get(token.lower(), token)
        actor_info = discovered_actors.get(canonical_login)
        if actor_info:
            node_id = actor_info["id"]
        elif canonical_login in FALLBACK_BOT_IDS:
            node_id = FALLBACK_BOT_IDS[canonical_login]
        else:
            raise ValueError(
                f"Unknown agent '{token}'. Available actors: {', '.join(sorted(discovered_actors.keys()))}"
            )
        if node_id not in resolved:
            resolved.append(node_id)
    return resolved


def build_create_issue_payload(
    repo_id: str,
    title: str,
    body: str,
    assignee_ids: list[str],
) -> dict[str, Any]:
    """Build the GraphQL mutation payload for creating and assigning an issue."""
    return {
        "query": (
            "mutation CreateAndAssignAgentIssue($repoId: ID!, $title: String!, $body: String!, $assigneeIds: [ID!]!) {"
            "  createIssue(input: {"
            "    repositoryId: $repoId,"
            "    title: $title,"
            "    body: $body,"
            "    assigneeIds: $assigneeIds"
            "  }) {"
            "    issue {"
            "      id"
            "      number"
            "      title"
            "      url"
            "      assignees(first: 10) {"
            "        nodes { login }"
            "      }"
            "    }"
            "  }"
            "}"
        ),
        "variables": {
            "repoId": repo_id,
            "title": title,
            "body": body,
            "assigneeIds": assignee_ids,
        },
    }


def build_branch_protection_payload(ci_contexts: list[str] | None = None) -> dict[str, Any]:
    """Build the REST payload for protecting a branch against force-pushes and deletions."""
    required_checks = (
        {"strict": false_val(), "contexts": ci_contexts}
        if ci_contexts
        else None
    )
    return {
        "required_status_checks": required_checks,
        "enforce_admins": False,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": False,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 0,
        },
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
        "required_conversation_resolution": True,
    }


def false_val() -> bool:
    """Return boolean False (helper for type clarity)."""
    return False


def cmd_actors(repo: str) -> int:
    """Print repository Node ID and assignable cloud agents."""
    owner, name = parse_owner_repo(repo)
    info = fetch_repo_and_actors(owner, name)
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0


def cmd_assign(
    repo: str,
    title: str,
    body_text: str,
    agents_csv: str,
    add_jules_label: bool = False,
) -> int:
    """Create a GitHub Issue and assign it to the requested cloud coding agents."""
    owner, name = parse_owner_repo(repo)
    info = fetch_repo_and_actors(owner, name)
    requested = [item.strip() for item in agents_csv.split(",") if item.strip()]
    assignee_ids = resolve_agent_ids(requested, info["actors"])

    payload = build_create_issue_payload(
        repo_id=info["repository_id"],
        title=title,
        body=body_text,
        assignee_ids=assignee_ids,
    )
    res = run_gh_json(
        ["api", "graphql", "-H", "GraphQL-Features: issues_copilot_assignment_api_support"],
        input_data=payload,
    )
    issue = res.get("data", {}).get("createIssue", {}).get("issue", {})

    if add_jules_label and issue.get("number"):
        subprocess.run(
            [
                "gh",
                "label",
                "create",
                "jules",
                "--repo",
                f"{owner}/{name}",
                "--color",
                "7B61FF",
                "--description",
                "Delegate issue to Google Jules coding agent",
                "--force",
            ],
            check=False,
            capture_output=True,
        )
        subprocess.run(
            [
                "gh",
                "issue",
                "edit",
                str(issue["number"]),
                "--repo",
                f"{owner}/{name}",
                "--add-label",
                "jules",
            ],
            check=False,
            capture_output=True,
        )

    print(json.dumps(issue, ensure_ascii=False, indent=2))
    return 0


def cmd_status(repo: str) -> int:
    """List open Pull Requests and indicate whether cloud agents have completed work."""
    owner, name = parse_owner_repo(repo)
    prs = run_gh_json(
        [
            "pr",
            "list",
            "--repo",
            f"{owner}/{name}",
            "--state",
            "open",
            "--json",
            "number,title,state,isDraft,mergeable,headRefName,url",
        ]
    )
    enriched = []
    for pr in prs:
        title = pr.get("title", "")
        is_wip = title.strip().upper().startswith("[WIP]")
        enriched.append(
            {
                **pr,
                "agent_completed": not is_wip,
            }
        )
    print(json.dumps(enriched, ensure_ascii=False, indent=2))
    return 0


def cmd_merge(repo: str, pr_number: int, comment: str, use_admin: bool) -> int:
    """Mark a cloud agent PR ready for review, post an LGTM review comment, and squash-merge it."""
    owner, name = parse_owner_repo(repo)
    repo_slug = f"{owner}/{name}"

    subprocess.run(["gh", "pr", "ready", str(pr_number), "--repo", repo_slug], check=False)
    subprocess.run(
        ["gh", "pr", "review", str(pr_number), "--repo", repo_slug, "--comment", "--body", comment],
        check=True,
    )
    merge_cmd = ["gh", "pr", "merge", str(pr_number), "--repo", repo_slug, "--squash", "--delete-branch"]
    if use_admin:
        merge_cmd.append("--admin")
    subprocess.run(merge_cmd, check=True)
    return 0


def cmd_protect_main(repo: str, branch: str, ci_contexts: list[str] | None) -> int:
    """Configure branch protection on `branch` (default: `main`)."""
    owner, name = parse_owner_repo(repo)
    payload = build_branch_protection_payload(ci_contexts=ci_contexts)
    res = run_gh_json(
        ["api", "-X", "PUT", f"repos/{owner}/{name}/branches/{branch}/protection"],
        input_data=payload,
    )
    print(
        json.dumps(
            {
                "protected_branch": branch,
                "repository": f"{owner}/{name}",
                "url": res.get("url"),
                "allow_force_pushes": res.get("allow_force_pushes", {}).get("enabled", False),
                "allow_deletions": res.get("allow_deletions", {}).get("enabled", False),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="gh_cloud_agent",
        description="Orchestrate GitHub Cloud Coding Agents (Copilot, Claude, Codex, Jules) via gh CLI.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_actors = sub.add_parser("actors", help="Discover repository Node ID and assignable agent Bot IDs")
    p_actors.add_argument("--repo", required=True, help="Repository in 'owner/repo' format")

    p_assign = sub.add_parser("assign", help="Create an Issue and assign it to cloud coding agents")
    p_assign.add_argument("--repo", required=True, help="Repository in 'owner/repo' format")
    p_assign.add_argument("--title", required=True, help="Issue title")
    body_group = p_assign.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--body", help="Issue body markdown string")
    body_group.add_argument("--body-file", help="Path to markdown file containing the Issue body")
    p_assign.add_argument(
        "--agents",
        default="copilot",
        help="Comma-separated agent aliases (copilot,claude,codex) or BOT_ Node IDs (default: copilot)",
    )
    p_assign.add_argument("--jules", action="store_true", help="Also create and attach the 'jules' label")

    p_status = sub.add_parser("status", help="List open Pull Requests and check if [WIP] is finished")
    p_status.add_argument("--repo", required=True, help="Repository in 'owner/repo' format")

    p_merge = sub.add_parser("merge", help="Mark PR ready, post review comment, and squash-merge")
    p_merge.add_argument("--repo", required=True, help="Repository in 'owner/repo' format")
    p_merge.add_argument("--pr", type=int, required=True, help="Pull Request number")
    p_merge.add_argument(
        "--comment",
        default="LGTM! Verified implementation and tests.",
        help="Review comment body",
    )
    p_merge.add_argument("--admin", action="store_true", help="Use --admin flag when merging into protected branch")

    p_protect = sub.add_parser("protect-main", help="Enable branch protection on main")
    p_protect.add_argument("--repo", required=True, help="Repository in 'owner/repo' format")
    p_protect.add_argument("--branch", default="main", help="Branch name to protect (default: main)")
    p_protect.add_argument(
        "--ci-check",
        action="append",
        dest="ci_checks",
        help="Optional required status check context name (can be specified multiple times)",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entrypoint for `gh_cloud_agent.py`."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "actors":
        return cmd_actors(args.repo)
    if args.command == "assign":
        body_text = (
            Path(args.body_file).read_text(encoding="utf-8")
            if args.body_file
            else str(args.body)
        )
        return cmd_assign(args.repo, args.title, body_text, args.agents, add_jules_label=args.jules)
    if args.command == "status":
        return cmd_status(args.repo)
    if args.command == "merge":
        return cmd_merge(args.repo, args.pr, args.comment, args.admin)
    if args.command == "protect-main":
        return cmd_protect_main(args.repo, args.branch, args.ci_checks)
    return 1


if __name__ == "__main__":
    sys.exit(main())
