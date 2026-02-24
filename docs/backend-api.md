# 后端 API 文档（V1 详细版）

## 1. 输入摘要（AGENTS 2.1）

- `user_goal`: 生成后端 API 文档（详细版）
- `stage`: `V1`
- `target_persona`: Creator（`docs/product-spec.md` 2.2）
- `constraints`:
  - 技术栈基线：FastAPI + SQLAlchemy + Alembic + SQLite（`AGENTS.md` 4.1）
  - 通信口径：`HTTP localhost`（`AGENTS.md` 4.2）
  - 业务语义与字段口径对齐 `docs/product-spec.md` 2.3 / 2.5 / 2.6 / 2.8 / 3
- `existing_assets`:
  - 路由：`app/api/v1/*`
  - Schema：`app/schemas/*`
  - Service 校验：`app/services/*`
  - 运行入口：`app/main.py`

## 2. 服务入口与运行前置

### 2.1 基础入口

- Base URL：`http://127.0.0.1:8000`
- Health：`GET /health`
- API Prefix：`/v1`
- OpenAPI JSON：`GET /openapi.json`
- Swagger UI：`GET /docs`

### 2.2 启动前置检查

服务启动时会 fail-fast 校验以下环境变量（`app/core/config.py` + `app/main.py`）：

| 变量名 | 必填 | 说明 |
| --- | --- | --- |
| `OPENAI_API_KEY` | 是 | LLM 调用凭证 |
| `OPENAI_BASE_URL` | 是 | OpenAI 兼容地址，启动时会做 URL 归一化与合法性校验 |
| `MODEL_NAME` | 是 | LLM 模型名 |

缺失时应用直接启动失败，不接受业务请求。

## 3. V1 范围对齐状态

### 3.1 当前已实现能力

- 诊断与能力画像（Onboarding）
- 身份模型生成与主备选择
- 人格宪法（版本化）
- 风险边界条目维护
- 7 天启动包生成与查询
- 草稿一致性检查
- 埋点事件记录与查询

### 3.2 与 `product-spec` V1 的差距

| V1 要求（`docs/product-spec.md` 2.5） | 当前后端状态 |
| --- | --- |
| Content Pillars & Matrix | 暂无独立资源 API |
| Monetization Map / 12 周路线图 | 暂无独立资源 API |
| 增长实验面板（假设-方案-结果-结论-迭代） | 仅有事件埋点 `experiment_created`，无独立 CRUD |

## 4. 通用协议与数据约定

### 4.1 协议

- Content-Type：`application/json`
- 大部分 POST/GET 成功状态码：`200`
- FastAPI/Pydantic 结构校验错误：`422`

### 4.2 标识与时间

- 业务主键 `id`：UUID 字符串
- 时间字段：ISO 8601 字符串（UTC）

### 4.3 JSON 字符串字段（重要）

以下字段在响应中是“JSON 字符串”，不是 JSON 对象/数组：

- `questionnaire_responses`
- `skill_stack_json`
- `interest_energy_curve_json`
- `value_boundaries_json`
- `content_pillars_json`
- `tone_keywords_json`
- `tone_examples_json`
- `long_term_views_json`
- `monetization_validation_order_json`
- `risk_boundary_json`
- `common_words_json`
- `forbidden_words_json`
- `sentence_preferences_json`
- `moat_positions_json`
- `sustainable_columns_json`
- `growth_experiment_suggestion_json`
- `deviation_items_json`
- `deviation_reasons_json`
- `suggestions_json`
- `payload_json`

客户端读取这些字段时需要二次反序列化。

### 4.4 当前无鉴权

当前接口没有 Token/Session 鉴权。仅适用于本地单用户开发阶段；进入共享环境前需补 ACL/鉴权。

## 5. 错误模型

### 5.1 HTTP 级错误语义

| HTTP | 场景 | 备注 |
| --- | --- | --- |
| 400 | 业务校验失败 | 如非法事件名、主备身份冲突 |
| 404 | 资源不存在 | 如 session/model/kit/check 查无记录 |
| 422 | 请求结构校验失败 | FastAPI/Pydantic 自动返回 |
| 502 | LLM 失败或 LLM 输出结构不合规 | 由路由统一映射 `LLMServiceError` |
| 503 | 数据库不可用 | 仅 `GET /health` |
| 500 | 未捕获异常 | 未显式封装时由框架返回 |

### 5.2 `502` 结构化错误体

```json
{
  "detail": {
    "code": "LLM_UPSTREAM_HTTP_ERROR",
    "message": "LLM upstream returned an HTTP error.",
    "operation": "generate_identity_models",
    "provider_status": 429,
    "provider_request_id": "req_xxx",
    "retryable": true,
    "attempts": 2
  }
}
```

### 5.3 LLM 错误代码目录（`app/services/llm_client.py`）

- `LLM_SCHEMA_VALIDATION_FAILED`
- `LLM_UPSTREAM_TIMEOUT`
- `LLM_UPSTREAM_UNAVAILABLE`
- `LLM_UPSTREAM_HTTP_ERROR`
- `LLM_CLIENT_ERROR`
- `LLM_INVALID_RESPONSE`

## 6. Schema 合同（OpenAPI 组件）

以下为最关键请求/响应模型及约束。

### 6.1 Onboarding

`OnboardingSessionCreate`

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | - |

`OnboardingSessionComplete`

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `session_id` | string | 是 | 与路径参数并存；当前服务实际以路径参数定位 |
| `questionnaire_responses` | object | 否 | 默认 `{}` |
| `skill_stack` | string[] | 否 | 默认 `[]` |
| `interest_energy_curve` | object[] | 否 | 默认 `[]` |
| `cognitive_style` | string | 否 | 默认 `""` |
| `value_boundaries` | string[] | 否 | 默认 `[]` |
| `risk_tolerance` | int | 否 | `1..5`，默认 `3` |
| `time_investment_hours` | int | 否 | `>=0`，默认 `0` |

### 6.2 Identity

`IdentityModelGenerate`

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | - |
| `session_id` | string \| null | 否 | 提供后可从画像表覆盖部分能力输入 |
| `capability_profile` | object | 否 | 默认 `{}` |
| `count` | int | 否 | `3..5`，默认 `3` |

`IdentitySelectionCreate`

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | - |
| `primary_identity_id` | string | 是 | - |
| `backup_identity_id` | string \| null | 否 | 不能与 `primary_identity_id` 相同 |

### 6.3 Persona 与 Risk

`PersonaConstitutionGenerate`

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | - |
| `identity_model_id` | string \| null | 否 | - |
| `common_words` | string[] | 否 | 默认 `[]` |
| `forbidden_words` | string[] | 否 | 默认 `[]` |

`RiskBoundaryItemCreate`

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | - |
| `identity_model_id` | string \| null | 否 | - |
| `constitution_id` | string \| null | 否 | - |
| `risk_level` | int | 否 | `1..5`，默认 `3` |
| `boundary_type` | string | 否 | 默认 `""` |
| `statement` | string | 否 | 默认 `""` |
| `source` | string | 否 | 默认 `user_input` |

### 6.4 Launch Kit

`LaunchKitGenerate`

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | - |
| `identity_model_id` | string \| null | 否 | - |
| `constitution_id` | string \| null | 否 | - |
| `sustainable_columns` | string[] | 否 | 服务层强校验输出 `>=3` |
| `growth_experiment_suggestion` | object[] | 否 | 服务层强校验输出 `>=1` |

### 6.5 Consistency

`ConsistencyCheckCreate`

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | - |
| `identity_model_id` | string \| null | 否 | - |
| `constitution_id` | string \| null | 否 | - |
| `draft_text` | string | 否 | 默认 `""` |
| `deviation_items` | string[] | 否 | 请求可传但实际由服务生成 |
| `deviation_reasons` | string[] | 否 | 请求可传但实际由服务生成 |
| `suggestions` | string[] | 否 | 请求可传但实际由服务生成 |
| `risk_triggered` | bool | 否 | 默认 `false` |
| `risk_warning` | string | 否 | 当请求里 `risk_triggered=true` 时必填 |

### 6.6 Events

`EventLogCreate`

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | - |
| `event_name` | string | 是 | 必须属于白名单 |
| `stage` | string | 是 | 正则 `^(MVP|V1|V2)$` |
| `identity_model_id` | string \| null | 否 | - |
| `payload` | object | 否 | 默认 `{}` |

## 7. 接口详细规格

以下按模块列出 29 个端点（含测试用用户创建接口）。

### 7.1 Health

#### GET `/health`

- 说明：服务存活与数据库探针
- 成功响应：

```json
{
  "status": "ok",
  "db_ok": true
}
```

- 错误：数据库异常时返回 `503` + `{"detail":"database unavailable"}`

### 7.2 Users（测试辅助）

#### POST `/v1/users`

- 说明：创建一个最小用户实体，仅用于本地黑盒/API 联调拿 `user_id`
- 请求体：无
- 成功响应字段：`id`, `created_at`

### 7.2 Onboarding

#### POST `/v1/onboarding/sessions`

- 请求体：`OnboardingSessionCreate`
- 成功响应字段：`id`, `user_id`, `status`
- Side effect：写入事件 `onboarding_started`（`stage=MVP`）
- 典型错误：`422`

请求示例：

```json
{
  "user_id": "u_001"
}
```

成功示例：

```json
{
  "id": "session_uuid",
  "user_id": "u_001",
  "status": "in_progress"
}
```

#### POST `/v1/onboarding/sessions/{session_id}/complete`

- Path 参数：`session_id`（必填）
- 请求体：`OnboardingSessionComplete`
- 成功响应字段：`session_id`, `status`, `profile_id`
- Side effect：写入事件 `onboarding_completed`（`stage=MVP`）
- 典型错误：
  - `404`：会话不存在
  - `422`：结构校验失败

#### GET `/v1/onboarding/sessions/{session_id}`

- 响应模型：`OnboardingSessionResponse`
- 典型错误：`404`（Session not found）、`422`

#### GET `/v1/onboarding/sessions/{session_id}/profile`

- 响应模型：`CapabilityProfileResponse`
- 典型错误：`404`（Profile not found）、`422`

#### GET `/v1/onboarding/users/{user_id}/profiles`

- 响应模型：`CapabilityProfileResponse[]`
- 典型错误：`422`

### 7.3 Identity

#### POST `/v1/identity-models/generate`

- 请求体：`IdentityModelGenerate`
- 服务端强约束（对齐 `product-spec` 2.6）：
  - 模型数量必须等于 `count`（3-5）
  - `differentiation` 非空
  - `tone_examples` 至少 5 条
  - `long_term_views` 5-10 条
  - `monetization_validation_order` 至少 1 条
- 成功响应：`list[dict]`（精简字段）
  - `id`, `title`, `target_audience_pain`, `differentiation`, `is_primary`, `is_backup`
- Side effect：写入 `identity_models_generated`
- 典型错误：`502`, `422`

成功示例：

```json
[
  {
    "id": "model_1",
    "title": "匿名增长顾问",
    "target_audience_pain": "不会持续输出",
    "differentiation": "数据化迭代打法",
    "is_primary": false,
    "is_backup": false
  }
]
```

#### GET `/v1/identity-models/users/{user_id}`

- 响应模型：`IdentityModelResponse[]`
- 典型错误：`422`

#### GET `/v1/identity-models/{model_id}`

- 响应模型：`IdentityModelResponse`
- 典型错误：`404`（Identity model not found）、`422`

#### POST `/v1/identity-selections`

- 请求体：`IdentitySelectionCreate`
- 成功响应字段：`id`, `primary_identity_id`, `backup_identity_id`, `selected_at`
- Side effect：
  - 更新身份模型主/备标记
  - 写入选择历史 `identity_selections`
  - 写入事件 `identity_selected`（附 `identity_model_id=primary_identity_id`）
- 典型错误：
  - `400`：主备相同/身份不存在
  - `422`：结构校验失败

#### GET `/v1/identity-selections/users/{user_id}`

- 响应模型：`IdentitySelectionResponse`
- 典型错误：`404`（No selection found）、`422`

### 7.4 Persona Constitution

#### POST `/v1/persona-constitutions/generate`

- 请求体：`PersonaConstitutionGenerate`
- 服务端强约束：
  - `common_words`, `forbidden_words`, `sentence_preferences`, `moat_positions` 均至少 3 条
  - `narrative_mainline`, `growth_arc_template` 非空
- 成功响应字段：`id`, `user_id`, `version`, `narrative_mainline`
- Side effect：版本号递增并保存 `previous_version_id`
- 典型错误：`502`, `422`

#### GET `/v1/persona-constitutions/users/{user_id}`

- 响应模型：`PersonaConstitutionResponse[]`（按版本倒序）
- 典型错误：`422`

#### GET `/v1/persona-constitutions/users/{user_id}/latest`

- 响应模型：`PersonaConstitutionResponse`
- 典型错误：`404`（No constitution found）、`422`

#### GET `/v1/persona-constitutions/{constitution_id}`

- 响应模型：`PersonaConstitutionResponse`
- 典型错误：`404`（Constitution not found）、`422`

### 7.5 Risk Boundaries

#### POST `/v1/risk-boundaries`

- 请求体：`RiskBoundaryItemCreate`
- 成功响应字段：`id`, `risk_level`, `boundary_type`, `statement`
- 典型错误：`422`

#### GET `/v1/risk-boundaries/users/{user_id}`

- 响应模型：`RiskBoundaryItemResponse[]`
- 典型错误：`422`

### 7.6 Launch Kits

#### POST `/v1/launch-kits/generate`

- 请求体：`LaunchKitGenerate`
- 服务端强约束：
  - `days` 必须恰好 7 条
  - `day_no` 必须唯一且覆盖 1..7
  - `sustainable_columns` 至少 3 条
  - `growth_experiment_suggestion` 至少 1 条
- 成功响应：
  - 顶层：`id`, `user_id`
  - `days[]` 仅返回 `day_no`, `theme`, `opening_text`
- Side effect：写入事件 `launch_kit_generated`
- 可靠性策略：
  - 当 LLM 输出结构不合规时，服务端会执行最多 2 次 schema 修复重试
  - 若 2 次重试仍不合规，返回 `502`（错误体 message 会包含重试耗尽信息）
- 典型错误：`502`, `422`

注意：若需要 `draft_or_outline`，请调用 `GET /v1/launch-kits/{kit_id}`。

#### GET `/v1/launch-kits/users/{user_id}`

- 响应模型：`LaunchKitResponse[]`
- 典型错误：`422`

#### GET `/v1/launch-kits/users/{user_id}/latest`

- 响应模型：`LaunchKitResponse`
- 典型错误：`404`（No launch kit found）、`422`

#### GET `/v1/launch-kits/{kit_id}`

- 响应模型：`LaunchKitResponse`
- 典型错误：`404`（Launch kit not found）、`422`

### 7.7 Consistency Checks

#### POST `/v1/consistency-checks`

- 请求体：`ConsistencyCheckCreate`
- 服务端强约束（对齐 `product-spec` 2.6）：
  - 输出至少包含：偏离项、偏离原因、修改建议
  - 若 `risk_triggered=true`，`risk_warning` 必填
- 成功响应字段：
  - `id`
  - `deviation_items`
  - `deviation_reasons`
  - `suggestions`
  - `risk_triggered`
  - `risk_warning`
  - `degraded`（bool）
  - `degrade_reason`（string \| null）
  - `schema_repair_attempts`（int，0..2）
- Side effect：写入事件 `consistency_check_triggered`，`payload` 包含 `risk_triggered`, `degraded`, `degrade_reason`, `schema_repair_attempts`
- 可靠性策略：
  - 当 LLM 输出结构不合规时，服务端会执行最多 2 次 schema 修复重试
  - 若 2 次重试仍不合规，接口返回 `200`，并使用降级结果（`degraded=true`）
- 典型错误：`400`, `502`, `422`（`502` 主要用于上游/网络类错误）

注意：`deviation_items` / `deviation_reasons` / `suggestions` 当前返回的是 JSON 字符串。

#### GET `/v1/consistency-checks/users/{user_id}`

- 响应模型：`ConsistencyCheckResponse[]`
- 典型错误：`422`

#### GET `/v1/consistency-checks/{check_id}`

- 响应模型：`ConsistencyCheckResponse`
- 典型错误：`404`（Consistency check not found）、`422`

### 7.8 Events

#### POST `/v1/events`

- 请求体：`EventLogCreate`
- `event_name` 白名单：
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
- `stage` 必须是 `MVP` / `V1` / `V2`
- 成功响应字段：`id`, `event_name`, `occurred_at`
- 典型错误：`400`, `422`

#### GET `/v1/events/users/{user_id}`

- Query 参数：`limit`（默认 `100`）
- 响应模型：`EventLogResponse[]`
- 典型错误：`422`

#### GET `/v1/events/name/{event_name}`

- Query 参数：`limit`（默认 `100`）
- 响应模型：`EventLogResponse[]`
- 典型错误：`422`

#### GET `/v1/events/recent`

- Query 参数：`limit`（默认 `100`）
- 响应模型：`EventLogResponse[]`
- 典型错误：`422`

## 8. 端到端调用示例（当前链路）

1. 创建 Onboarding 会话：`POST /v1/onboarding/sessions`
2. 完成问卷并产出画像：`POST /v1/onboarding/sessions/{session_id}/complete`
3. 生成身份模型：`POST /v1/identity-models/generate`
4. 选择主备身份：`POST /v1/identity-selections`
5. 生成人格宪法：`POST /v1/persona-constitutions/generate`
6. 生成 7 天启动包：`POST /v1/launch-kits/generate`
7. 发布前一致性检查：`POST /v1/consistency-checks`

## 9. 埋点映射（`product-spec` 2.8）

| 事件名 | 触发来源 |
| --- | --- |
| `onboarding_started` | `POST /v1/onboarding/sessions` 自动写入 |
| `onboarding_completed` | `POST /v1/onboarding/sessions/{session_id}/complete` 自动写入 |
| `identity_models_generated` | `POST /v1/identity-models/generate` 自动写入 |
| `identity_selected` | `POST /v1/identity-selections` 自动写入 |
| `launch_kit_generated` | `POST /v1/launch-kits/generate` 自动写入 |
| `consistency_check_triggered` | `POST /v1/consistency-checks` 自动写入 |
| 其余 4 个事件 | 可通过 `POST /v1/events` 手动写入 |

## 10. 标准交付物映射（`product-spec` 3）

| 交付物 | 对应后端接口 |
| --- | --- |
| Identity Model Card | `/v1/identity-models/*` + `/v1/identity-selections/*` |
| Persona Constitution | `/v1/persona-constitutions/*` |
| 7-Day Launch Kit | `/v1/launch-kits/*` |
| Risk & Boundary List | `/v1/risk-boundaries/*` |
| Content Pillars & Matrix（V1） | 暂无独立 API |
| Monetization Map（V1） | 暂无独立 API |

## 11. V1 后续接口建议（补齐差距）

- `GET/POST /v1/content-matrixes`：内容支柱 -> 选题池 -> 多平台改写
- `GET/POST /v1/monetization-maps`：12 周路线图与验证节点
- `GET/POST /v1/experiments`：假设、变量、周期、结果、结论、迭代

以上 3 组接口补齐后，V1 交付物可闭环覆盖。
