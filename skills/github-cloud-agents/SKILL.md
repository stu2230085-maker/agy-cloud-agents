---
name: github-cloud-agents
description: >-
  Use this skill whenever the user wants to delegate coding tasks, features, bug fixes, or tests to GitHub Cloud Coding Agents (Copilot SWE Agent, Claude Code Agent, OpenAI Codex Agent, Google Jules), configure main branch protection, or review and merge Pull Requests created by GitHub agents.
---

# GitHub Cloud Coding Agents Orchestration Skill

This skill provides a portable, multi-device workflow and zero-dependency Python CLI helper (`scripts/gh_cloud_agent.py`) to orchestrate GitHub's cloud coding agents (`copilot-swe-agent`, `anthropic-code-agent`, `openai-code-agent`, and `jules`) via `gh` CLI and GraphQL API.

## 1. Quick Commands via `scripts/gh_cloud_agent.py`

Always prefer running the bundled helper script [gh_cloud_agent.py](./scripts/gh_cloud_agent.py) so you don't have to hardcode repository IDs or worry about bash backtick escaping in issue bodies.

### A. Discover Repository Node ID & Assignable Agent Bot IDs

```bash
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py actors --repo <OWNER/REPO>
```

### B. Create an Issue & Assign Cloud Agents (`copilot`, `claude`, `codex`, `jules`)

1. Write the markdown issue specification to a temporary file (e.g., `/tmp/issue_spec.md`) using `write_file`.
2. Run `assign`:

```bash
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py assign \
  --repo <OWNER/REPO> \
  --title "feat: <clear task title>" \
  --body-file /tmp/issue_spec.md \
  --agents copilot
```
*(You can pass `--agents copilot,claude`, `--agents copilot,codex`, or `--jules` to also attach the `jules` label.)*

### C. Check Agent Pull Request Progress

```bash
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py status --repo <OWNER/REPO>
```
- When an agent is still working, its Draft PR title starts with `[WIP]`.
- Once `[WIP]` is removed from the PR title, the cloud agent has finished committing and testing its changes.

### D. Review Diff & Merge Completed Pull Request

1. Inspect the PR diff:
   ```bash
   gh pr diff <PR_NUMBER> --repo <OWNER/REPO>
   ```
2. Mark ready for review, post an LGTM review comment, and squash-merge:
   ```bash
   python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py merge \
     --repo <OWNER/REPO> \
     --pr <PR_NUMBER> \
     --comment "LGTM! Verified implementation and tests." \
     --admin
   ```

### E. Enable `main` Branch Protection

```bash
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py protect-main \
  --repo <OWNER/REPO> \
  --branch main
```

---

## 2. Raw GraphQL Reference (Fallback)

If you ever need to call `gh api graphql` directly without the helper script:

- Header required for Bot assignment: `-H "GraphQL-Features: issues_copilot_assignment_api_support"`
- Common Bot Node IDs:
  - `copilot-swe-agent`: `BOT_kgDOC9w8XQ`
  - `anthropic-code-agent`: `BOT_kgDODnPHJg`
  - `openai-code-agent`: `BOT_kgDODnSAjQ`

Always pass GraphQL payloads via `--input <json_file>` to prevent shell expansion of backticks in Markdown code blocks.
