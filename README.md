# test-design-ai-tools

テスト設計を支援するAIエージェントスキル集です。

## スキル一覧

### 状態遷移テストケース生成 (`skills/state_transition_test`)

与えられた状態機械（ステートマシン）の定義から、状態遷移テストのテストケースを自動生成します。

**対応カバレッジ基準**

| カバレッジ基準 | 説明 |
|---|---|
| `all_states` | 全状態網羅 — すべての状態を少なくとも 1 回訪れる |
| `all_transitions` | 全遷移網羅（デフォルト） — すべての遷移を少なくとも 1 回通過する |
| `all_with_invalid` | 全遷移 + 無効遷移 — 正常テストに加え、各状態での未定義イベントに対する否定テストも生成する |

詳細は [`skills/state_transition_test/README.md`](skills/state_transition_test/README.md) を参照してください。

**クイックスタート**

```bash
# サンプルの決済ステートマシンでテストケースを生成する
python -m skills.state_transition_test examples/payment_state_machine.json all_transitions
```

```python
from skills.state_transition_test import run

result = run({
    "state_machine": {
        "states": ["Idle", "Running", "Stopped"],
        "initial_state": "Idle",
        "transitions": [
            {"from": "Idle",    "event": "start", "to": "Running"},
            {"from": "Running", "event": "stop",  "to": "Stopped"},
            {"from": "Stopped", "event": "reset", "to": "Idle"},
        ],
    },
    "coverage": "all_with_invalid",
})
```

## ディレクトリ構成

```
skills/
  state_transition_test/
    __init__.py          # パッケージ公開 API
    generator.py         # テストケース生成ロジック
    skill.py             # エージェントスキルのエントリポイント + CLI
    skill_definition.json  # OpenAI 関数呼び出し互換スキル定義
    README.md            # スキルのドキュメント
examples/
  payment_state_machine.json  # 決済フロー（英語）
  ec_site_login.json          # EC サイトのログインフロー（日本語）
tests/
  test_state_transition_generator.py  # ユニットテスト
```

## テストの実行

```bash
python -m pytest tests/ -v
```