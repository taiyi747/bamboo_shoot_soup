# API 测试 README（简版，给接口测试）

## 1. 文档用途与快速开始

这份文档给接口测试同学使用，目标是：
- 快速跑通主链路
- 快速定位每个接口怎么传参

快速开始（手工测试）：
1. 启动后端服务（默认 `http://127.0.0.1:8000`）。
2. 在 Apifox/Postman 配置环境变量（见第 2 节）。
3. 先按第 3 节跑主链路，再按第 4/5/6 节做全量接口验证。

## 2. 环境变量

| 变量名 | 必填 | 说明 |
| --- | --- | --- |
| `base_url` | 是 | 固定：`http://127.0.0.1:8000` |
| `user_id` | 是 | `POST /v1/users` 返回 |
| `session_id` | 是 | `POST /v1/onboarding/sessions` 返回 |
| `profile_id` | 否 | `POST /v1/onboarding/sessions/{session_id}/complete` 返回 |
| `primary_identity_id` | 是 | `POST /v1/identity-models/generate` 返回 |
| `backup_identity_id` | 否 | `POST /v1/identity-models/generate` 返回 |
| `constitution_id` | 是 | `POST /v1/persona-constitutions/generate` 返回 |
| `risk_boundary_id` | 否 | `POST /v1/risk-boundaries` 返回 |
| `kit_id` | 是 | `POST /v1/launch-kits/generate` 返回 |
| `check_id` | 是 | `POST /v1/consistency-checks` 返回 |
| `event_id` | 否 | `POST /v1/events` 返回 |

## 3. 主链路执行顺序（8 步）

1. `POST /v1/users`
2. `POST /v1/onboarding/sessions`
3. `POST /v1/onboarding/sessions/{session_id}/complete`
4. `POST /v1/identity-models/generate`
5. `POST /v1/identity-selections`
6. `POST /v1/persona-constitutions/generate`
7. `POST /v1/launch-kits/generate`
8. `POST /v1/consistency-checks`（最后可 `POST /v1/events` 记业务事件）

## 4. 全接口速查表（29）

| 编号 | Method | Path | 用途 |
| --- | --- | --- | --- |
| E01 | GET | `/health` | 健康检查 |
| E02 | POST | `/v1/users` | 创建测试用户 |
| E03 | POST | `/v1/onboarding/sessions` | 创建 onboarding 会话 |
| E04 | POST | `/v1/onboarding/sessions/{session_id}/complete` | 完成会话并生成画像 |
| E05 | GET | `/v1/onboarding/sessions/{session_id}` | 查询会话 |
| E06 | GET | `/v1/onboarding/sessions/{session_id}/profile` | 查询会话画像 |
| E07 | GET | `/v1/onboarding/users/{user_id}/profiles` | 查询用户画像列表 |
| E08 | POST | `/v1/identity-models/generate` | 生成身份模型 |
| E09 | GET | `/v1/identity-models/users/{user_id}` | 查询身份模型列表 |
| E10 | GET | `/v1/identity-models/{model_id}` | 查询身份模型详情 |
| E11 | POST | `/v1/identity-selections` | 选择主/备身份 |
| E12 | GET | `/v1/identity-selections/users/{user_id}` | 查询当前身份选择 |
| E13 | POST | `/v1/persona-constitutions/generate` | 生成人格宪法 |
| E14 | GET | `/v1/persona-constitutions/users/{user_id}` | 查询宪法列表 |
| E15 | GET | `/v1/persona-constitutions/users/{user_id}/latest` | 查询最新宪法 |
| E16 | GET | `/v1/persona-constitutions/{constitution_id}` | 查询宪法详情 |
| E17 | POST | `/v1/risk-boundaries` | 创建风险边界条目 |
| E18 | GET | `/v1/risk-boundaries/users/{user_id}` | 查询风险边界列表 |
| E19 | POST | `/v1/launch-kits/generate` | 生成 7 天启动包 |
| E20 | GET | `/v1/launch-kits/users/{user_id}` | 查询启动包列表 |
| E21 | GET | `/v1/launch-kits/users/{user_id}/latest` | 查询最新启动包 |
| E22 | GET | `/v1/launch-kits/{kit_id}` | 查询启动包详情 |
| E23 | POST | `/v1/consistency-checks` | 草稿一致性检查 |
| E24 | GET | `/v1/consistency-checks/users/{user_id}` | 查询一致性记录列表 |
| E25 | GET | `/v1/consistency-checks/{check_id}` | 查询一致性记录详情 |
| E26 | POST | `/v1/events` | 手动写事件 |
| E27 | GET | `/v1/events/users/{user_id}` | 按用户查事件 |
| E28 | GET | `/v1/events/name/{event_name}` | 按事件名查事件 |
| E29 | GET | `/v1/events/recent` | 查全局最近事件 |

## 5. POST 接口详细参数（10）

### 5.1 POST `/v1/users`

请求参数：无 Body。

| 字段名 | 是否必填 | 类型 | 约束 | 示例 |
| --- | --- | --- | --- | --- |
| - | - | - | 无提交参数 | - |

成功判定：`200`，返回 `id`、`created_at`。  
常见失败：`500`（数据库写入异常）。

### 5.2 POST `/v1/onboarding/sessions`

| 字段名 | 是否必填 | 类型 | 约束 | 示例 |
| --- | --- | --- | --- | --- |
| `user_id` | 是 | string | 用户 ID | `"{{user_id}}"` |

成功判定：`200`，返回 `id/user_id/status`。  
常见失败：`422`（缺少 `user_id`）。

### 5.3 POST `/v1/onboarding/sessions/{session_id}/complete`

Path 参数：

| 字段名 | 是否必填 | 类型 | 约束 | 示例 |
| --- | --- | --- | --- | --- |
| `session_id` | 是 | string | 会话 ID | `"{{session_id}}"` |

Body 参数：

| 字段名 | 是否必填 | 类型 | 约束 | 示例 |
| --- | --- | --- | --- | --- |
| `session_id` | 是 | string | 建议与 Path 一致 | `"{{session_id}}"` |
| `questionnaire_responses` | 否 | object | 默认 `{}` | `{"goal":"build identity"}` |
| `skill_stack` | 否 | string[] | 默认 `[]` | `["python","writing"]` |
| `interest_energy_curve` | 否 | object[] | 默认 `[]` | `[{"topic":"growth","score":4}]` |
| `cognitive_style` | 否 | string | 默认空字符串 | `"structured"` |
| `value_boundaries` | 否 | string[] | 默认 `[]` | `["no fake claims"]` |
| `risk_tolerance` | 否 | integer | `1..5`，默认 `3` | `3` |
| `time_investment_hours` | 否 | integer | `>=0`，默认 `0` | `8` |

成功判定：`200`，返回 `session_id/status/profile_id`。  
常见失败：`404`（会话不存在）、`422`（参数越界）。

### 5.4 POST `/v1/identity-models/generate`

| 字段名 | 是否必填 | 类型 | 约束 | 示例 |
| --- | --- | --- | --- | --- |
| `user_id` | 是 | string | 用户 ID | `"{{user_id}}"` |
| `session_id` | 否 | string \| null | 有值时可复用画像 | `"{{session_id}}"` |
| `capability_profile` | 否 | object | 默认 `{}` | `{}` |
| `count` | 否 | integer | `3..5`，默认 `3` | `3` |

业务补充约束（服务层）：
- 输出模型数必须等于 `count`
- `differentiation` 必须非空
- `tone_examples` 至少 5 条
- `long_term_views` 必须 5-10 条

成功判定：`200`，返回长度=`count` 的数组。  
常见失败：`422`（如 `count=2`）、`502`（LLM 上游或结构化失败）。

### 5.5 POST `/v1/identity-selections`

| 字段名 | 是否必填 | 类型 | 约束 | 示例 |
| --- | --- | --- | --- | --- |
| `user_id` | 是 | string | 用户 ID | `"{{user_id}}"` |
| `primary_identity_id` | 是 | string | 主身份 ID | `"{{primary_identity_id}}"` |
| `backup_identity_id` | 否 | string \| null | 不能与主身份相同 | `"{{backup_identity_id}}"` |

成功判定：`200`，返回 `primary_identity_id/backup_identity_id/selected_at`。  
常见失败：`400`（ID 不存在）、`422`（主备相同）。

### 5.6 POST `/v1/persona-constitutions/generate`

| 字段名 | 是否必填 | 类型 | 约束 | 示例 |
| --- | --- | --- | --- | --- |
| `user_id` | 是 | string | 用户 ID | `"{{user_id}}"` |
| `identity_model_id` | 否 | string \| null | 可选关联身份 | `"{{primary_identity_id}}"` |
| `common_words` | 否 | string[] | 默认 `[]` | `["clarity","evidence"]` |
| `forbidden_words` | 否 | string[] | 默认 `[]` | `["guarantee","fake"]` |

业务补充约束（服务层输出）：
- `common_words` / `forbidden_words` / `sentence_preferences` / `moat_positions` 各至少 3 条
- `narrative_mainline`、`growth_arc_template` 非空

成功判定：`200`，返回 `id/user_id/version/narrative_mainline`。  
常见失败：`422`、`502`。

### 5.7 POST `/v1/risk-boundaries`

| 字段名 | 是否必填 | 类型 | 约束 | 示例 |
| --- | --- | --- | --- | --- |
| `user_id` | 是 | string | 用户 ID | `"{{user_id}}"` |
| `identity_model_id` | 否 | string \| null | 可选 | `"{{primary_identity_id}}"` |
| `constitution_id` | 否 | string \| null | 可选 | `"{{constitution_id}}"` |
| `risk_level` | 否 | integer | `1..5`，默认 `3` | `3` |
| `boundary_type` | 否 | string | 默认空字符串 | `"legal"` |
| `statement` | 否 | string | 默认空字符串 | `"Do not impersonate others."` |
| `source` | 否 | string | 默认 `user_input` | `"user_input"` |

成功判定：`200`，返回 `id/risk_level/boundary_type/statement`。  
常见失败：`422`（如 `risk_level=7`）。

### 5.8 POST `/v1/launch-kits/generate`

| 字段名 | 是否必填 | 类型 | 约束 | 示例 |
| --- | --- | --- | --- | --- |
| `user_id` | 是 | string | 用户 ID | `"{{user_id}}"` |
| `identity_model_id` | 否 | string \| null | 可选 | `"{{primary_identity_id}}"` |
| `constitution_id` | 否 | string \| null | 可选 | `"{{constitution_id}}"` |
| `sustainable_columns` | 否 | string[] | 默认 `[]` | `["case","teardown","weekly note"]` |
| `growth_experiment_suggestion` | 否 | object[] | 默认 `[]` | `[{"name":"title A/B"}]` |

业务补充约束（服务层输出）：
- 必须返回 7 天，且 `day_no` 覆盖 `1..7`
- `sustainable_columns` 至少 3 条
- `growth_experiment_suggestion` 至少 1 条

成功判定：`200`，返回 `id/user_id/days(7条)`。  
常见失败：`422`、`502`。

### 5.9 POST `/v1/consistency-checks`

| 字段名 | 是否必填 | 类型 | 约束 | 示例 |
| --- | --- | --- | --- | --- |
| `user_id` | 是 | string | 用户 ID | `"{{user_id}}"` |
| `identity_model_id` | 否 | string \| null | 可选 | `"{{primary_identity_id}}"` |
| `constitution_id` | 否 | string \| null | 可选 | `"{{constitution_id}}"` |
| `draft_text` | 否 | string | 默认空字符串 | `"draft text"` |
| `deviation_items` | 否 | string[] | 默认 `[]`，可不传 | `[]` |
| `deviation_reasons` | 否 | string[] | 默认 `[]`，可不传 | `[]` |
| `suggestions` | 否 | string[] | 默认 `[]`，可不传 | `[]` |
| `risk_triggered` | 否 | boolean | 默认 `false` | `false` |
| `risk_warning` | 否 | string | 当 `risk_triggered=true` 时必填 | `"potential risk"` |

业务补充约束（服务层输出）：
- 返回必须含 `deviation_items/deviation_reasons/suggestions`
- 有 schema repair 机制，响应附带 `degraded/degrade_reason/schema_repair_attempts`

成功判定：`200`，返回 `id`、偏离项、风险字段、降级字段。  
常见失败：`400`、`422`、`502`。

### 5.10 POST `/v1/events`

| 字段名 | 是否必填 | 类型 | 约束 | 示例 |
| --- | --- | --- | --- | --- |
| `user_id` | 是 | string | 用户 ID | `"{{user_id}}"` |
| `event_name` | 是 | string | 必须在白名单内 | `"experiment_created"` |
| `stage` | 是 | string | 只能是 `MVP` / `V1` / `V2` | `"V1"` |
| `identity_model_id` | 否 | string \| null | 可选 | `"{{primary_identity_id}}"` |
| `payload` | 否 | object | 默认 `{}` | `{"hypothesis":"new CTA"}` |

`event_name` 白名单：
- `onboarding_started`
- `onboarding_completed`
- `identity_models_generated`
- `identity_selected`
- `launch_kit_generated`
- `content_published`
- `consistency_check_triggered`
- `experiment_created`
- `monetization_plan_started`
- `first_revenue_or_lead_confirmed`

成功判定：`200`，返回 `id/event_name/occurred_at`。  
常见失败：`400`（事件名不合法）、`422`（`stage` 格式不合法）。

## 6. GET 接口参数简表

| Method | Path | Path 参数 | Query 参数 | 成功判定 | 常见失败 |
| --- | --- | --- | --- | --- | --- |
| GET | `/health` | - | - | `200` 且 `status=ok` | `503` |
| GET | `/v1/onboarding/sessions/{session_id}` | `session_id` | - | `200` 且返回会话 | `404/422` |
| GET | `/v1/onboarding/sessions/{session_id}/profile` | `session_id` | - | `200` 且返回画像 | `404/422` |
| GET | `/v1/onboarding/users/{user_id}/profiles` | `user_id` | - | `200` 返回数组 | `422` |
| GET | `/v1/identity-models/users/{user_id}` | `user_id` | - | `200` 返回数组 | `422` |
| GET | `/v1/identity-models/{model_id}` | `model_id` | - | `200` 返回详情 | `404/422` |
| GET | `/v1/identity-selections/users/{user_id}` | `user_id` | - | `200` 返回主备选择 | `404/422` |
| GET | `/v1/persona-constitutions/users/{user_id}` | `user_id` | - | `200` 返回数组 | `422` |
| GET | `/v1/persona-constitutions/users/{user_id}/latest` | `user_id` | - | `200` 返回最新宪法 | `404/422` |
| GET | `/v1/persona-constitutions/{constitution_id}` | `constitution_id` | - | `200` 返回详情 | `404/422` |
| GET | `/v1/risk-boundaries/users/{user_id}` | `user_id` | - | `200` 返回数组 | `422` |
| GET | `/v1/launch-kits/users/{user_id}` | `user_id` | - | `200` 返回数组 | `422` |
| GET | `/v1/launch-kits/users/{user_id}/latest` | `user_id` | - | `200` 返回最新启动包 | `404/422` |
| GET | `/v1/launch-kits/{kit_id}` | `kit_id` | - | `200` 返回详情 | `404/422` |
| GET | `/v1/consistency-checks/users/{user_id}` | `user_id` | - | `200` 返回数组 | `422` |
| GET | `/v1/consistency-checks/{check_id}` | `check_id` | - | `200` 返回详情 | `404/422` |
| GET | `/v1/events/users/{user_id}` | `user_id` | `limit`（默认100） | `200` 返回数组 | `422` |
| GET | `/v1/events/name/{event_name}` | `event_name` | `limit`（默认100） | `200` 返回数组 | `422` |
| GET | `/v1/events/recent` | - | `limit`（默认100） | `200` 返回数组 | `422` |

## 7. 统一成功与常见错误码

| 状态码 | 含义 | 常见场景 |
| --- | --- | --- |
| `200` | 成功 | 查询成功、创建成功 |
| `400` | 业务校验失败 | 非法 `event_name`、ID 业务关系错误 |
| `404` | 资源不存在 | `session_id/model_id/kit_id/check_id` 不存在 |
| `422` | 请求参数不合法 | 必填缺失、范围越界、类型错误 |
| `502` | LLM 上游/结构化失败 | 身份生成、宪法生成、启动包生成、一致性检查 |
| `503` | 依赖不可用 | 健康检查时数据库不可用 |

## 8. 最小可执行示例（4 个）

### 示例 1：完成 onboarding

`POST /v1/onboarding/sessions/{session_id}/complete`

```json
{
  "session_id": "{{session_id}}",
  "questionnaire_responses": {"goal": "build second identity"},
  "skill_stack": ["python", "strategy"],
  "interest_energy_curve": [{"topic": "growth", "score": 4}],
  "cognitive_style": "structured",
  "value_boundaries": ["no fake claims"],
  "risk_tolerance": 3,
  "time_investment_hours": 8
}
```

### 示例 2：生成身份模型

`POST /v1/identity-models/generate`

```json
{
  "user_id": "{{user_id}}",
  "session_id": "{{session_id}}",
  "count": 3
}
```

### 示例 3：生成启动包

`POST /v1/launch-kits/generate`

```json
{
  "user_id": "{{user_id}}",
  "identity_model_id": "{{primary_identity_id}}",
  "constitution_id": "{{constitution_id}}",
  "sustainable_columns": ["case", "teardown", "weekly note"],
  "growth_experiment_suggestion": [{"name": "title A/B"}]
}
```

### 示例 4：手动写事件

`POST /v1/events`

```json
{
  "user_id": "{{user_id}}",
  "event_name": "experiment_created",
  "stage": "V1",
  "identity_model_id": "{{primary_identity_id}}",
  "payload": {"hypothesis": "new CTA has better CTR"}
}
```
