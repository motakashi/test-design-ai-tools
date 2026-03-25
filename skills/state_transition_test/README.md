# State Transition Test Case Generator

状態遷移テスト（State Transition Testing）のテストケースを自動生成するエージェントスキルです。

## 概要

与えられた状態機械（ステートマシン）の定義から、以下のカバレッジ基準に基づくテストケースを生成します。

| カバレッジ基準 | 説明 |
|---|---|
| `all_states` | 全状態網羅 (0スイッチカバレッジ) — すべての状態を少なくとも 1 回訪れる |
| `all_transitions` | 全遷移網羅 (1スイッチカバレッジ) — すべての遷移を少なくとも 1 回通過する（デフォルト） |
| `all_with_invalid` | 全遷移 + 無効遷移 — 全遷移網羅に加え、各状態で定義されていないイベントを投入する否定テストを生成する |

## 入力フォーマット

```json
{
  "state_machine": {
    "states": ["状態A", "状態B", "状態C"],
    "initial_state": "状態A",
    "final_states": ["状態C"],
    "transitions": [
      { "from": "状態A", "event": "イベント1", "to": "状態B" },
      { "from": "状態B", "event": "イベント2", "to": "状態C" },
      { "from": "状態B", "event": "イベント3", "to": "状態A" }
    ]
  },
  "coverage": "all_transitions"
}
```

### 各フィールドの説明

| フィールド | 必須 | 説明 |
|---|---|---|
| `states` | ✔ | 状態の一覧 |
| `initial_state` | ✔ | 初期状態 |
| `final_states` | — | 終了状態の一覧（省略可） |
| `transitions[].from` | ✔ | 遷移元の状態 |
| `transitions[].event` | ✔ | 遷移を引き起こすイベント |
| `transitions[].to` | ✔ | 遷移先の状態 |
| `transitions[].condition` | — | ガード条件（省略可） |
| `transitions[].action` | — | 遷移時に実行するアクション（省略可） |
| `coverage` | — | カバレッジ基準（省略時は `all_transitions`） |

## 出力フォーマット

```json
{
  "metadata": {
    "total_states": 3,
    "total_events": 3,
    "total_transitions": 3,
    "coverage_criterion": "all_transitions",
    "total_test_cases": 3
  },
  "test_cases": [
    {
      "id": "TC-001",
      "description": "Transition [状態A] --[イベント1]--> [状態B]",
      "precondition": "System is in initial state [状態A]",
      "coverage_criterion": "All Transitions Coverage",
      "steps": [
        {
          "current_state": "状態A",
          "event": "イベント1",
          "next_state": "状態B",
          "expected_result": "transition succeeds"
        }
      ],
      "expected_final_state": "状態B"
    }
  ]
}
```

## 使い方

### Python モジュールとして使う

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
print(result)
```

### コマンドラインから使う

```bash
python -m skills.state_transition_test examples/payment_state_machine.json all_transitions
```

### AI エージェントツールとして使う

`skill_definition.json` をエージェントのツール定義として登録し、エージェントが
`generate_state_transition_test_cases` を呼び出せるようにしてください。

```python
import json
from skills.state_transition_test import SKILL_DEFINITION, run

# ツール定義をエージェントに渡す
tools = [{"type": "function", "function": SKILL_DEFINITION}]

# エージェントがツールを呼び出した際の処理
def handle_tool_call(tool_name: str, arguments: dict) -> str:
    if tool_name == "generate_state_transition_test_cases":
        result = run(arguments)
        return json.dumps(result, ensure_ascii=False, indent=2)
```

## サンプル

`examples/` ディレクトリにサンプルの入力ファイルがあります。

```bash
# EC サイトのログインフロー（全遷移 + 無効遷移）
python -m skills.state_transition_test examples/ec_site_login.json all_with_invalid

# 決済ステートマシン（全遷移網羅）
python -m skills.state_transition_test examples/payment_state_machine.json all_transitions
```
