# エージェント運用 & GitHub クラウドエージェント連携ガイドライン

- **デフォルト方針（Antigravity 優先）**:
  - 通常の実装・機能追加・テスト・Git/PR 操作は、GitHub 側のエージェントトークン枠（Premium Requests）を消費しない **Antigravity 自身（または Antigravity 内蔵のバックグラウンド・サブエージェント `invoke_subagent` / 並列 `swarm`）** で直接実行すること。
- **GitHub Cloud Coding Agents (`copilot-swe-agent` / `Claude` / `Codex` / `Jules`) 連携**:
  - ユーザーから明示的に「GitHubのクラウドエージェントに指示を出して」「Copilot / Claude / Codex に実装させて」等の依頼があった場合は、`github-cloud-agents` スキルおよび付属の `gh_cloud_agent.py`（または `gh api graphql`）を使用して操作すること。

---

## 1. 利用可能なクラウドエージェント (Bot Login & 役割)

対象リポジトリの Issue に Assignee として以下のクラウドエージェント Bot を指定すると、GitHub Actions クラウド環境上でエージェントが自律起動し、ブランチ作成・実装・Draft PR 作成を自動実行します。

| エージェント名 | GraphQL `login` | 主な Node ID 例 | 特徴 |
| :--- | :--- | :--- | :--- |
| **Copilot** | `copilot-swe-agent` | `BOT_kgDOC9w8XQ` | GitHub Copilot SWE Agent（即時 Draft PR を立ち上げる主力エージェント） |
| **Claude** | `anthropic-code-agent` | `BOT_kgDODnPHJg` | Anthropic Claude Code Agent（`copilot-swe-agent` と併用アサイン推奨） |
| **Codex** | `openai-code-agent` | `BOT_kgDODnSAjQ` | OpenAI Code Agent（`copilot-swe-agent` と併用アサイン推奨） |
| **Jules** | *(Label トリガー)* | `--label jules` | Google Jules GitHub App 導入済みリポジトリで `jules` ラベル付与時に起動 |

---

## 2. ヘルパー CLI (`gh_cloud_agent.py`) による簡単操作

どのデバイス・リポジトリでもシェルエスケープ問題を起こさずに操作できるよう、`~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py` がインストールされています。

```bash
# 1. リポジトリの Node ID と利用可能なクラウドエージェント一覧を取得
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py actors --repo <OWNER/REPO>

# 2. Issue を作成してクラウドエージェント (copilot / claude / codex) に自動アサイン
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py assign \
  --repo <OWNER/REPO> \
  --title "feat: Add new endpoint" \
  --body-file /tmp/issue_body.md \
  --agents copilot,claude

# 3. クラウドエージェントが作成した PR の進行状況（[WIP] 解消有無）を確認
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py status --repo <OWNER/REPO>

# 4. 完了した PR の Draft 解除・レビューコメント投稿・Squash マージを一括実行
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py merge \
  --repo <OWNER/REPO> \
  --pr <PR_NUMBER> \
  --admin

# 5. main ブランチ保護設定（Force Push 禁止・削除禁止・PR 必須化）を有効化
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py protect-main --repo <OWNER/REPO>
```
