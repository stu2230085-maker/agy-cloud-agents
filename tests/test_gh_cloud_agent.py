"""Unit tests for gh_cloud_agent.py helper CLI and install.py cross-device installer."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "skills" / "github-cloud-agents" / "scripts"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

import gh_cloud_agent  # noqa: E402
import install  # noqa: E402


class TestGhCloudAgentAndInstaller(unittest.TestCase):
    """Test suite for GitHub Cloud Agent CLI helpers and multi-device installer."""

    def test_parse_owner_repo(self) -> None:
        """parse_owner_repo should split valid slugs and reject malformed inputs."""
        owner, repo = gh_cloud_agent.parse_owner_repo("stu2230085-maker/py-apiforge")
        self.assertEqual(owner, "stu2230085-maker")
        self.assertEqual(repo, "py-apiforge")

        with self.assertRaises(ValueError):
            gh_cloud_agent.parse_owner_repo("invalid-slug")

    def test_resolve_agent_ids_with_aliases_and_raw_ids(self) -> None:
        """resolve_agent_ids should map copilot, claude, codex aliases to Bot Node IDs."""
        discovered = {
            "copilot-swe-agent": {"login": "copilot-swe-agent", "id": "BOT_kgDOC9w8XQ", "type": "Bot"},
            "anthropic-code-agent": {"login": "anthropic-code-agent", "id": "BOT_kgDODnPHJg", "type": "Bot"},
        }
        ids = gh_cloud_agent.resolve_agent_ids(["copilot", "claude", "codex", "BOT_custom"], discovered)
        self.assertEqual(
            ids,
            [
                "BOT_kgDOC9w8XQ",
                "BOT_kgDODnPHJg",
                "BOT_kgDODnSAjQ",
                "BOT_custom",
            ],
        )

    def test_build_create_issue_payload_preserves_backticks(self) -> None:
        """GraphQL payload builder should preserve markdown backticks without shell expansion."""
        payload = gh_cloud_agent.build_create_issue_payload(
            repo_id="R_kgDOVv6QAw",
            title="feat: Add `GET /api/v1/health`",
            body="Run `PYTHONPATH=src python3 -m unittest`",
            assignee_ids=["BOT_kgDOC9w8XQ"],
        )
        self.assertEqual(payload["variables"]["repoId"], "R_kgDOVv6QAw")
        self.assertIn("`PYTHONPATH=src python3 -m unittest`", payload["variables"]["body"])
        self.assertEqual(payload["variables"]["assigneeIds"], ["BOT_kgDOC9w8XQ"])

    def test_build_branch_protection_payload(self) -> None:
        """Branch protection payload should disable force pushes and deletions."""
        payload = gh_cloud_agent.build_branch_protection_payload(["Test on Python 3.13"])
        self.assertFalse(payload["allow_force_pushes"])
        self.assertFalse(payload["allow_deletions"])
        self.assertTrue(payload["required_conversation_resolution"])
        self.assertEqual(payload["required_status_checks"]["contexts"], ["Test on Python 3.13"])

    def test_installer_copies_skills_and_rules_to_target_directories(self) -> None:
        """install_customizations should populate global and workspace customization paths."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_home = tmp_path / "home"
            fake_ws = tmp_path / "workspace"

            result = install.install_customizations(
                repo_root=REPO_ROOT,
                home_dir=fake_home,
                workspace_dir=fake_ws,
                install_rule=True,
            )
            self.assertGreaterEqual(len(result["installed"]), 5)
            self.assertTrue(
                (fake_home / ".gemini" / "config" / "skills" / "github-cloud-agents" / "SKILL.md").is_file()
            )
            self.assertTrue(
                (
                    fake_home
                    / ".gemini"
                    / "config"
                    / "skills"
                    / "github-cloud-agents"
                    / "scripts"
                    / "gh_cloud_agent.py"
                ).is_file()
            )
            self.assertTrue(
                (fake_ws / ".agents" / "skills" / "github-cloud-agents" / "SKILL.md").is_file()
            )
            self.assertTrue((fake_ws / "GEMINI.md").is_file())


if __name__ == "__main__":
    unittest.main()
