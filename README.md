# Antigravity × GitHub Cloud Coding Agents (`agy-cloud-agents`)

**どのデバイスからでもワンコマンドで Antigravity に GitHub クラウドコーディングエージェント（Copilot SWE Agent / Claude Code Agent / OpenAI Codex Agent / Google Jules）連携スキル・ルール・補助 CLI を導入できるポータブル設定リポジトリ**

---

## 特徴

1. **マルチデバイス・ワンコマンド導入 (`install.py`)**
   - 新しい PC・コンテナ・WSL・Chromebook などの環境でリポジトリを `git clone` して `python3 install.py` を実行するだけで、グローバル設定（`~/.gemini/config/skills/`）とワークスペース設定（`.agents/skills/`, `GEMINI.md`）を一括セットアップできます。
2. **外部依存ゼロのクラウドエージェント制御 CLI (`gh_cloud_agent.py`)**
   - **動的 Node ID 解決 (`actors`)**: リポジトリ名（`owner/repo`）を指定するだけで、GraphQL `repositoryId` とそのリポジトリにアサイン可能な全 AI エージェント（`copilot-swe-agent`, `anthropic-code-agent`, `openai-code-agent`）の Node ID を自動取得。
   - **シェルエスケープ不要の Issue 作成＆アサイン (`assign`)**: Markdown 内のバッククォート（`` `code` ``）による bash 展開エラーを完全に防ぐ一時 JSON ファイル方式で GraphQL Mutation を送信。`--agents copilot,claude,codex` や `--jules` ラベル付与にも対応。
   - **PR 進行状況確認 (`status`) & 一括レビュー・Squash マージ (`merge`)**: エージェントの実装完了（`[WIP]` 解消）の検知から、`gh pr ready`・レビューコメント投稿・`--squash --delete-branch` マージまでを1コマンドで実行。
   - **`main` ブランチ保護 (`protect-main`)**: Force Push 禁止・ブランチ削除禁止・PR 経由必須化・CI ステータスチェックをワンコマンドで適用。
3. **トークン節約のためのハイブリッド運用ルール (`rules/GEMINI.md`)**
   - 普段の実装・テスト・Git 操作は **GitHub 側のトークン枠を消費しない Antigravity 自身（または内蔵サブエージェント `invoke_subagent` / 並列 `swarm`）** で直接行い、明示的に指示したときのみ GitHub クラウドエージェントを呼び出す運用方針を標準搭載。

---

## リポジトリ構成

```text
agy-cloud-agents/
├── install.py                      # クロスプラットフォーム対応インストーラ (Linux / macOS / Windows)
├── README.md                       # セットアップ & 使い方ドキュメント
├── LICENSE                         # MIT License
├── rules/
│   └── GEMINI.md                   # ワークスペース用ルールテンプレート
├── skills/
│   └── github-cloud-agents/
│       ├── SKILL.md                # Antigravity スキル定義ファイル
│       └── scripts/
│           └── gh_cloud_agent.py   # GitHub Cloud Agent オーケストレーション CLI
└── tests/
    └── test_gh_cloud_agent.py      # CLI & インストーラのユニットテストスイート
```

---

## 別デバイスでのセットアップ手順（クイックスタート）

前提として `python3` と GitHub CLI (`gh auth login` 済み) が入っていればすぐに使えます。

```bash
# 1. リポジトリをクローンしてインストーラを実行
git clone https://github.com/stu2230085-maker/agy-cloud-agents.git
cd agy-cloud-agents
python3 install.py
```

### インストーラのオプション

```bash
# 特定のプロジェクトディレクトリにのみ .agents/skills と GEMINI.md を導入したい場合
python3 install.py --workspace /path/to/your/project

# グローバルスキル (~/.gemini/config/skills/) のみ導入し、GEMINI.md は上書きしない場合
python3 install.py --no-workspace
```

---

## ヘルパー CLI (`gh_cloud_agent.py`) の使い方

インストール完了後、Antigravity のチャット上で **「GitHub のクラウドエージェントに〇〇の実装 Issue を出して」「PR の様子を見てマージして」「main ブランチを保護して」** と伝えるだけでエージェントが自動的に以下のツールを実行します（手動でターミナルから直接実行することも可能です）。

```bash
# 1. リポジトリの GraphQL ID とアサイン可能な AI エージェント一覧を確認
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py actors \
  --repo stu2230085-maker/<REPO_NAME>

# 2. Issue を作成してクラウドエージェントにアサイン (copilot / claude / codex / --jules)
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py assign \
  --repo stu2230085-maker/<REPO_NAME> \
  --title "feat: Add health metrics endpoint" \
  --body-file /tmp/issue_body.md \
  --agents copilot,claude

# 3. オープン中の PR とエージェント作業完了状態 (agent_completed: true/false) を確認
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py status \
  --repo stu2230085-maker/<REPO_NAME>

# 4. 完了した PR を Ready 化 + レビューコメント + Squash マージ
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py merge \
  --repo stu2230085-maker/<REPO_NAME> \
  --pr <PR_NUMBER> \
  --admin

# 5. main ブランチの保護設定を有効化
python3 ~/.gemini/config/skills/github-cloud-agents/scripts/gh_cloud_agent.py protect-main \
  --repo stu2230085-maker/<REPO_NAME>
```

---

## テストの実行

```bash
python3 -m unittest discover -s tests -v
```

## ライセンス

MIT License
