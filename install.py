#!/usr/bin/env python3
"""Cross-platform installer for Antigravity GitHub Cloud Agents rules, skills, and helper scripts."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Sequence


def install_customizations(
    repo_root: Path,
    home_dir: Path,
    workspace_dir: Path | None = None,
    install_rule: bool = True,
) -> dict[str, list[str]]:
    """Copy skill and rule files into global (`~/.gemini/config/`) and optional workspace locations."""
    installed_files: list[str] = []

    src_skill_dir = repo_root / "skills" / "github-cloud-agents"
    src_rule_file = repo_root / "rules" / "GEMINI.md"

    if not src_skill_dir.is_dir():
        raise FileNotFoundError(f"Skill directory not found: {src_skill_dir}")
    if not src_rule_file.is_file():
        raise FileNotFoundError(f"Rule file not found: {src_rule_file}")

    # 1. Global Skill: ~/.gemini/config/skills/github-cloud-agents
    global_skill_dest = home_dir / ".gemini" / "config" / "skills" / "github-cloud-agents"
    _copy_tree(src_skill_dir, global_skill_dest, installed_files)

    # 2. Workspace Skill & Rule (if workspace_dir is provided)
    if workspace_dir is not None:
        ws_skill_dest = workspace_dir / ".agents" / "skills" / "github-cloud-agents"
        _copy_tree(src_skill_dir, ws_skill_dest, installed_files)

        if install_rule:
            ws_rule_dest = workspace_dir / "GEMINI.md"
            ws_rule_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_rule_file, ws_rule_dest)
            installed_files.append(str(ws_rule_dest))

    return {"installed": installed_files}


def _copy_tree(src_dir: Path, dest_dir: Path, record_list: list[str]) -> None:
    """Recursively copy `src_dir` into `dest_dir` and mark scripts executable."""
    for src_path in src_dir.rglob("*"):
        if src_path.is_dir() or "__pycache__" in src_path.parts:
            continue
        rel = src_path.relative_to(src_dir)
        target = dest_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, target)
        if target.suffix == ".py":
            target.chmod(0o755)
        record_list.append(str(target))


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser for `install.py`."""
    parser = argparse.ArgumentParser(
        prog="install.py",
        description="Install Antigravity GitHub Cloud Agents skill and rules on this device.",
    )
    parser.add_argument(
        "--home",
        default=str(Path.home()),
        help="Target user home directory (default: current user's home directory)",
    )
    parser.add_argument(
        "--workspace",
        default=str(Path.home()),
        help="Target workspace directory for .agents/skills and GEMINI.md (default: user home directory)",
    )
    parser.add_argument(
        "--no-workspace",
        action="store_true",
        help="Only install global skill under ~/.gemini/config/skills/",
    )
    parser.add_argument(
        "--no-rule",
        action="store_true",
        help="Skip copying GEMINI.md into the workspace root",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entrypoint for `install.py`."""
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent
    home_dir = Path(args.home).expanduser().resolve()
    workspace_dir = None if args.no_workspace else Path(args.workspace).expanduser().resolve()

    result = install_customizations(
        repo_root=repo_root,
        home_dir=home_dir,
        workspace_dir=workspace_dir,
        install_rule=not args.no_rule,
    )
    print("✓ Installed Antigravity GitHub Cloud Agents customizations:")
    for path_str in result["installed"]:
        print(f"  - {path_str}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
