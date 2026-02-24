# API 全接口测试手册（Apifox/Postman 执行版）

## 1. 文档目标与适用范围
本手册用于同伴在不写脚本的前提下，通过 Apifox 或 Postman 完成后端 29 接口黑盒测试、证据留存和缺陷提交流程。

适用范围：
1. 覆盖 29 接口（含 `POST /v1/users`）。
2. 覆盖主链路、查询链路、最小负向集、真实 LLM 联调。
3. 每个接口必须保留原始请求与原始响应证据。

不在范围：
1. 前端 UI 测试。
2. 数据库白盒校验。
3. 单元测试代码开发。

## 2. Apifox/Postman 前置配置
### 2.1 环境变量（必须）
在 Apifox 或 Postman 新建环境，配置：
1. `base_url = http://127.0.0.1:8000`
2. `user_id =`
3. `session_id =`
4. `profile_id =`
5. `primary_identity_id =`
6. `backup_identity_id =`
7. `constitution_id =`
8. `risk_boundary_id =`
9. `kit_id =`
10. `check_id =`
11. `event_id =`

### 2.2 Collection/项目结构（建议）
按以下文件夹组织请求，方便顺序执行：
1. `00-Health`
2. `01-Users`
3. `02-Onboarding`
4. `03-Identity`
5. `04-Persona-Risk`
6. `05-LaunchKit`
7. `06-Consistency`
8. `07-Events`
9. `08-Negative-Cases`
10. `09-Live-LLM`

### 2.3 证据导出设置（必须）
每次请求都要留存：
1. 请求证据：Method、URL、Headers、Body。
2. 响应证据：Status、Headers、Body。
3. 对于失败请求，额外保存运行时间与重试记录。

建议导出路径：
1. `tests/api/reports/<YYYYMMDD_HHMM>/E编号/request.*`
2. `tests/api/reports/<YYYYMMDD_HHMM>/E编号/response.*`
3. `tests/api/reports/<YYYYMMDD_HHMM>/summary.md`

## 3. 固定测试顺序（必须按序）
1. 基础可用性：E01 -> E02
2. 主链路建档：E03 -> E04 -> E08 -> E11 -> E13 -> E17 -> E19 -> E23 -> E26
3. 查询链路回查：E05 E06 E07 E09 E10 E12 E14 E15 E16 E18 E20 E21 E22 E24 E25 E27 E28 E29
4. 最小负向集：每模块至少 1 条
5. LLM 稳定性：E08/E13/E19/E23 多场景 + 重试

## 4. 全接口清单（29）
1. E01 `GET /health`
2. E02 `POST /v1/users`
3. E03 `POST /v1/onboarding/sessions`
4. E04 `POST /v1/onboarding/sessions/{session_id}/complete`
5. E05 `GET /v1/onboarding/sessions/{session_id}`
6. E06 `GET /v1/onboarding/sessions/{session_id}/profile`
7. E07 `GET /v1/onboarding/users/{user_id}/profiles`
8. E08 `POST /v1/identity-models/generate`
9. E09 `GET /v1/identity-models/users/{user_id}`
10. E10 `GET /v1/identity-models/{model_id}`
11. E11 `POST /v1/identity-selections`
12. E12 `GET /v1/identity-selections/users/{user_id}`
13. E13 `POST /v1/persona-constitutions/generate`
14. E14 `GET /v1/persona-constitutions/users/{user_id}`
15. E15 `GET /v1/persona-constitutions/users/{user_id}/latest`
16. E16 `GET /v1/persona-constitutions/{constitution_id}`
17. E17 `POST /v1/risk-boundaries`
18. E18 `GET /v1/risk-boundaries/users/{user_id}`
19. E19 `POST /v1/launch-kits/generate`
20. E20 `GET /v1/launch-kits/users/{user_id}`
21. E21 `GET /v1/launch-kits/users/{user_id}/latest`
22. E22 `GET /v1/launch-kits/{kit_id}`
23. E23 `POST /v1/consistency-checks`
24. E24 `GET /v1/consistency-checks/users/{user_id}`
25. E25 `GET /v1/consistency-checks/{check_id}`
26. E26 `POST /v1/events`
27. E27 `GET /v1/events/users/{user_id}`
28. E28 `GET /v1/events/name/{event_name}`
29. E29 `GET /v1/events/recent`

## 5. 接口逐条测试步骤（E01-E29，固定 10 字段）
字段定义（每条都必须写入执行记录）：
1. 接口编号与名称
2. Method + Path
3. 目标（验证点）
4. 前置依赖
5. 请求示例（Body/Query）
6. 成功判定
7. 常见失败码与解释
8. 最小负向用例
9. 证据要求
10. 关联后续接口

### E01 健康检查
1. 编号与名称：E01 健康检查
2. Method + Path：`GET /health`
3. 目标：服务可达、数据库可用
4. 前置依赖：无
5. 请求示例：无 Body
6. 成功判定：`200`，响应含 `status=ok`、`db_ok=true`
7. 常见失败：`503`（数据库不可用）、`404`（误用 `/healthz`）
8. 最小负向：`GET /healthz` 预期 `404`
9. 证据要求：保存完整请求/响应
10. 后续：E02

### E02 创建测试用户
1. 编号与名称：E02 创建用户
2. Method + Path：`POST /v1/users`
3. 目标：创建用户并获得 `user_id`
4. 前置依赖：E01 通过
5. 请求示例：无 Body
6. 成功判定：`200`，响应含 `id`、`created_at`
7. 常见失败：`500`（数据库写入异常）
8. 最小负向：`GET /v1/users` 预期 `405`
9. 证据要求：记录并回填环境变量 `user_id`
10. 后续：E03

### E03 创建 Onboarding 会话
1. 编号与名称：E03 创建会话
2. Method + Path：`POST /v1/onboarding/sessions`
3. 目标：为用户创建会话并获得 `session_id`
4. 前置依赖：`user_id`
5. 请求示例：
```json
{"user_id":"{{user_id}}"}
```
6. 成功判定：`200`，响应含 `id/user_id/status`，`status=in_progress`
7. 常见失败：`422`（缺少 user_id）
8. 最小负向：Body `{}` 预期 `422`
9. 证据要求：记录 `session_id`
10. 后续：E04、E05

### E04 完成 Onboarding 会话
1. 编号与名称：E04 完成会话
2. Method + Path：`POST /v1/onboarding/sessions/{{session_id}}/complete`
3. 目标：完成问卷并生成画像，获得 `profile_id`
4. 前置依赖：`session_id`
5. 请求示例：
```json
{
  "session_id":"{{session_id}}",
  "questionnaire_responses":{"goal":"Build creator identity"},
  "skill_stack":["python","writing"],
  "interest_energy_curve":[{"topic":"growth","score":4}],
  "cognitive_style":"structured",
  "value_boundaries":["no fake claims"],
  "risk_tolerance":3,
  "time_investment_hours":8
}
```
6. 成功判定：`200`，响应含 `session_id/status/profile_id` 且 `status=completed`
7. 常见失败：`404`（session 不存在）、`422`（字段越界）
8. 最小负向：`risk_tolerance=7` 预期 `422`
9. 证据要求：记录 `profile_id`
10. 后续：E06、E07、E08

### E05 查询会话详情
1. 编号与名称：E05 查询会话
2. Method + Path：`GET /v1/onboarding/sessions/{{session_id}}`
3. 目标：会话状态回查
4. 前置依赖：`session_id`
5. 请求示例：无 Body
6. 成功判定：`200` 且 `id={{session_id}}`
7. 常见失败：`404`
8. 最小负向：`missing-session` 预期 `404`
9. 证据要求：保存完整响应
10. 后续：E06

### E06 查询会话画像
1. 编号与名称：E06 查询画像
2. Method + Path：`GET /v1/onboarding/sessions/{{session_id}}/profile`
3. 目标：画像可回查
4. 前置依赖：E04 成功
5. 请求示例：无 Body
6. 成功判定：`200` 且 `session_id={{session_id}}`
7. 常见失败：`404`
8. 最小负向：`missing-session/profile` 预期 `404`
9. 证据要求：保存完整响应
10. 后续：E07、E08

### E07 查询用户画像列表
1. 编号与名称：E07 查询画像列表
2. Method + Path：`GET /v1/onboarding/users/{{user_id}}/profiles`
3. 目标：用户维度画像列表可读
4. 前置依赖：`user_id`
5. 请求示例：无 Body
6. 成功判定：`200` 且数组长度 >= 1
7. 常见失败：`422`
8. 最小负向：路径缺 user_id 预期 `404`
9. 证据要求：保存完整响应
10. 后续：E08

### E08 生成身份模型（LLM）
1. 编号与名称：E08 生成身份模型
2. Method + Path：`POST /v1/identity-models/generate`
3. 目标：生成 3-5 条身份候选，记录 `primary_identity_id`、`backup_identity_id`
4. 前置依赖：`user_id`，建议有 `session_id`
5. 请求示例：
```json
{"user_id":"{{user_id}}","session_id":"{{session_id}}","count":3}
```
6. 成功判定：`200`，数组长度=3，每项含 `id/title/differentiation`
7. 常见失败：`422`（count 非法）、`502`（LLM 上游/结构失败）
8. 最小负向：`count=2` 预期 `422`
9. 证据要求：记录两个 identity id
10. 后续：E09、E10、E11

### E09 查询身份列表
1. 编号与名称：E09 查询身份列表
2. Method + Path：`GET /v1/identity-models/users/{{user_id}}`
3. 目标：回查 E08 生成结果
4. 前置依赖：`user_id`
5. 请求示例：无 Body
6. 成功判定：`200` 且包含 E08 返回的 id
7. 常见失败：`422`
8. 最小负向：不存在用户通常返回 `200 + []`
9. 证据要求：保存完整响应
10. 后续：E10、E11

### E10 查询单个身份
1. 编号与名称：E10 查询身份详情
2. Method + Path：`GET /v1/identity-models/{{primary_identity_id}}`
3. 目标：单条身份详情可读
4. 前置依赖：`primary_identity_id`
5. 请求示例：无 Body
6. 成功判定：`200` 且 `id` 匹配
7. 常见失败：`404`
8. 最小负向：`missing-model-id` 预期 `404`
9. 证据要求：保存完整响应
10. 后续：E11

### E11 选择主备身份
1. 编号与名称：E11 主备选择
2. Method + Path：`POST /v1/identity-selections`
3. 目标：写入主备身份并触发 `identity_selected`
4. 前置依赖：`user_id`、两个 identity id
5. 请求示例：
```json
{
  "user_id":"{{user_id}}",
  "primary_identity_id":"{{primary_identity_id}}",
  "backup_identity_id":"{{backup_identity_id}}"
}
```
6. 成功判定：`200`，响应含 `primary_identity_id/backup_identity_id/selected_at`
7. 常见失败：`422`（主备相同/缺字段）、`400`（id 不存在）
8. 最小负向：主备相同，预期 `422`
9. 证据要求：保存完整请求响应
10. 后续：E12、E13

### E12 查询当前身份选择
1. 编号与名称：E12 查询身份选择
2. Method + Path：`GET /v1/identity-selections/users/{{user_id}}`
3. 目标：回查 E11
4. 前置依赖：E11
5. 请求示例：无 Body
6. 成功判定：`200` 且主备 id 与 E11 一致
7. 常见失败：`404`（尚未选择）
8. 最小负向：不存在用户，预期 `404`
9. 证据要求：保存完整响应
10. 后续：E13

### E13 生成 Persona Constitution（LLM）
1. 编号与名称：E13 生成宪法
2. Method + Path：`POST /v1/persona-constitutions/generate`
3. 目标：获取 `constitution_id`
4. 前置依赖：`user_id`，建议带 `primary_identity_id`
5. 请求示例：
```json
{
  "user_id":"{{user_id}}",
  "identity_model_id":"{{primary_identity_id}}",
  "common_words":["evidence","system","clarity"],
  "forbidden_words":["guarantee","overnight","fake"]
}
```
6. 成功判定：`200`，含 `id/user_id/version/narrative_mainline`
7. 常见失败：`422`、`502`
8. 最小负向：Body `{}` 预期 `422`
9. 证据要求：记录 `constitution_id`
10. 后续：E14、E15、E16、E17、E19、E23

### E14 查询宪法列表
1. 编号与名称：E14 查询宪法列表
2. Method + Path：`GET /v1/persona-constitutions/users/{{user_id}}`
3. 目标：宪法列表可读
4. 前置依赖：`user_id`
5. 请求示例：无 Body
6. 成功判定：`200` 且包含 `constitution_id`
7. 常见失败：`422`
8. 最小负向：不存在用户，通常 `200 + []`
9. 证据要求：保存完整响应
10. 后续：E15、E16

### E15 查询最新宪法
1. 编号与名称：E15 查询最新宪法
2. Method + Path：`GET /v1/persona-constitutions/users/{{user_id}}/latest`
3. 目标：返回最新版本
4. 前置依赖：E13
5. 请求示例：无 Body
6. 成功判定：`200`，`id` 非空
7. 常见失败：`404`（无数据）
8. 最小负向：不存在用户，预期 `404`
9. 证据要求：保存完整响应
10. 后续：E16

### E16 查询宪法详情
1. 编号与名称：E16 查询宪法详情
2. Method + Path：`GET /v1/persona-constitutions/{{constitution_id}}`
3. 目标：单条可读
4. 前置依赖：`constitution_id`
5. 请求示例：无 Body
6. 成功判定：`200` 且 `id` 匹配
7. 常见失败：`404`
8. 最小负向：`missing-constitution-id` 预期 `404`
9. 证据要求：保存完整响应
10. 后续：E17

### E17 创建风险边界
1. 编号与名称：E17 创建风险边界
2. Method + Path：`POST /v1/risk-boundaries`
3. 目标：写入风险边界并拿到 `risk_boundary_id`
4. 前置依赖：`user_id`，可选 `constitution_id`
5. 请求示例：
```json
{
  "user_id":"{{user_id}}",
  "constitution_id":"{{constitution_id}}",
  "risk_level":3,
  "boundary_type":"legal",
  "statement":"Do not impersonate people.",
  "source":"user_input"
}
```
6. 成功判定：`200`，含 `id/risk_level/boundary_type/statement`
7. 常见失败：`422`（risk_level 越界）
8. 最小负向：`risk_level=7` 预期 `422`
9. 证据要求：记录 `risk_boundary_id`
10. 后续：E18、E19

### E18 查询风险边界列表
1. 编号与名称：E18 查询风险边界列表
2. Method + Path：`GET /v1/risk-boundaries/users/{{user_id}}`
3. 目标：回查 E17
4. 前置依赖：`user_id`
5. 请求示例：无 Body
6. 成功判定：`200` 且数组 >= 1
7. 常见失败：`422`
8. 最小负向：不存在用户，通常 `200 + []`
9. 证据要求：保存完整响应
10. 后续：E19

### E19 生成 Launch Kit（LLM）
1. 编号与名称：E19 生成启动包
2. Method + Path：`POST /v1/launch-kits/generate`
3. 目标：获得 `kit_id`，验证 7 天结构
4. 前置依赖：`user_id`，建议带 identity/constitution
5. 请求示例：
```json
{
  "user_id":"{{user_id}}",
  "identity_model_id":"{{primary_identity_id}}",
  "constitution_id":"{{constitution_id}}",
  "sustainable_columns":["case breakdown","system teardown","weekly reflection"],
  "growth_experiment_suggestion":[{"name":"title A/B test"}]
}
```
6. 成功判定：`200`，含 `id/user_id/days`，`days` 长度 7，覆盖 1..7
7. 常见失败：`422`、`502`
8. 最小负向：Body `{}` 预期 `422`
9. 证据要求：记录 `kit_id`
10. 后续：E20、E21、E22、E23

### E20 查询启动包列表
1. 编号与名称：E20 查询启动包列表
2. Method + Path：`GET /v1/launch-kits/users/{{user_id}}`
3. 目标：回查 E19
4. 前置依赖：`user_id`
5. 请求示例：无 Body
6. 成功判定：`200`，包含 `kit_id`
7. 常见失败：`422`
8. 最小负向：不存在用户通常 `200 + []`
9. 证据要求：保存完整响应
10. 后续：E21、E22

### E21 查询最新启动包
1. 编号与名称：E21 查询最新启动包
2. Method + Path：`GET /v1/launch-kits/users/{{user_id}}/latest`
3. 目标：返回最新一条
4. 前置依赖：E19
5. 请求示例：无 Body
6. 成功判定：`200`，`id` 非空，`days` 长度 7
7. 常见失败：`404`
8. 最小负向：不存在用户，预期 `404`
9. 证据要求：保存完整响应
10. 后续：E22

### E22 查询启动包详情
1. 编号与名称：E22 查询启动包详情
2. Method + Path：`GET /v1/launch-kits/{{kit_id}}`
3. 目标：详情可读（含 `draft_or_outline`）
4. 前置依赖：`kit_id`
5. 请求示例：无 Body
6. 成功判定：`200` 且 `id` 匹配
7. 常见失败：`404`
8. 最小负向：`missing-kit-id` 预期 `404`
9. 证据要求：保存完整响应
10. 后续：E23

### E23 一致性检查（LLM）
1. 编号与名称：E23 一致性检查
2. Method + Path：`POST /v1/consistency-checks`
3. 目标：获得 `check_id`，验证降级字段
4. 前置依赖：`user_id`，建议带 identity/constitution
5. 请求示例：
```json
{
  "user_id":"{{user_id}}",
  "identity_model_id":"{{primary_identity_id}}",
  "constitution_id":"{{constitution_id}}",
  "draft_text":"This draft promises guaranteed results in 7 days. Please check risks."
}
```
6. 成功判定：`200`，含 `id/deviation_items/deviation_reasons/suggestions/degraded/degrade_reason/schema_repair_attempts`
7. 常见失败：`422`、`400`、`502`
8. 最小负向：`risk_triggered=true` 且 `risk_warning=""` 预期 `422`
9. 证据要求：记录 `check_id` 与 `degraded` 值
10. 后续：E24、E25、E26

### E24 查询一致性列表
1. 编号与名称：E24 查询一致性列表
2. Method + Path：`GET /v1/consistency-checks/users/{{user_id}}`
3. 目标：回查 E23
4. 前置依赖：`user_id`
5. 请求示例：无 Body
6. 成功判定：`200` 且包含 `check_id`
7. 常见失败：`422`
8. 最小负向：不存在用户通常 `200 + []`
9. 证据要求：保存完整响应
10. 后续：E25

### E25 查询一致性详情
1. 编号与名称：E25 查询一致性详情
2. Method + Path：`GET /v1/consistency-checks/{{check_id}}`
3. 目标：单条可读
4. 前置依赖：`check_id`
5. 请求示例：无 Body
6. 成功判定：`200` 且 `id` 匹配
7. 常见失败：`404`
8. 最小负向：`missing-check-id` 预期 `404`
9. 证据要求：保存完整响应
10. 后续：E26

### E26 创建事件
1. 编号与名称：E26 创建事件
2. Method + Path：`POST /v1/events`
3. 目标：写入事件并获得 `event_id`
4. 前置依赖：`user_id`
5. 请求示例：
```json
{
  "user_id":"{{user_id}}",
  "event_name":"experiment_created",
  "stage":"V1",
  "payload":{"hypothesis":"new CTA works"}
}
```
6. 成功判定：`200`，含 `id/event_name/occurred_at`
7. 常见失败：`400`（非法 event_name）、`422`（stage 不合法）
8. 最小负向：`event_name=invalid_event` 预期 `400`
9. 证据要求：记录 `event_id`
10. 后续：E27、E28、E29

### E27 查询用户事件
1. 编号与名称：E27 查询用户事件
2. Method + Path：`GET /v1/events/users/{{user_id}}`
3. 目标：按用户查询事件
4. 前置依赖：`user_id`
5. 请求示例：Query `limit=20`
6. 成功判定：`200` 且包含 `experiment_created`
7. 常见失败：`422`（limit 非整数）
8. 最小负向：`limit=oops` 预期 `422`
9. 证据要求：保存完整响应
10. 后续：E28、E29

### E28 按事件名查询
1. 编号与名称：E28 按事件名查询
2. Method + Path：`GET /v1/events/name/experiment_created`
3. 目标：事件名筛选正确
4. 前置依赖：E26
5. 请求示例：Query `limit=20`
6. 成功判定：`200` 且每条 `event_name=experiment_created`
7. 常见失败：`422`
8. 最小负向：`limit=bad` 预期 `422`
9. 证据要求：保存完整响应
10. 后续：E29

### E29 查询最近事件
1. 编号与名称：E29 查询最近事件
2. Method + Path：`GET /v1/events/recent`
3. 目标：全局最近事件可读
4. 前置依赖：建议 E26 后
5. 请求示例：Query `limit=20`
6. 成功判定：`200` 且响应数组非空
7. 常见失败：`422`
8. 最小负向：`limit=oops` 预期 `422`
9. 证据要求：保存完整响应
10. 后续：汇总与提单

## 6. 最小负向测试矩阵（每模块至少 1 条）
1. Health：`GET /healthz` -> `404`
2. Users：`GET /v1/users` -> `405`
3. Onboarding：`POST /v1/onboarding/sessions` Body `{}` -> `422`
4. Identity Generate：`count=2` -> `422`
5. Identity Selection：主备相同 -> `422`
6. Persona Generate：Body `{}` -> `422`
7. Risk Boundary：`risk_level=7` -> `422`
8. Launch Kit Generate：Body `{}` -> `422`
9. Consistency：`risk_triggered=true` 且空 `risk_warning` -> `422`
10. Events Create：`invalid_event` -> `400`
11. Events Query：`limit=oops` -> `422`

## 7. 真实 LLM 联调规则（E08/E13/E19/E23）
1. 前置变量必须存在：`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`MODEL_NAME`
2. 若返回 `502` 或超时，同参最多重试 2 次
3. 第一次失败响应必须保留，不可覆盖
4. 重试成功要标记“瞬时失败后恢复”
5. 重试后仍失败必须提缺陷
6. E23 若 `200` 且 `degraded=true`，视为降级成功，不判接口失败
7. E23 的降级次数要单独统计

## 8. 严格证据采集规范
每个接口都要有以下证据：
1. 原始请求（Method、URL、Headers、Body）
2. 原始响应（Status、Headers、Body）
3. 判定（PASS/FAIL）与断言说明
4. 失败时附重试记录与影响说明

建议目录：
1. `tests/api/reports/<run_id>/E01/...`
2. `tests/api/reports/<run_id>/E01N/...`
3. `tests/api/reports/<run_id>/...`
4. `tests/api/reports/<run_id>/summary.md`

## 9. 缺陷提交规则（固定模板）
每个 FAIL 必须提一条缺陷，模板如下：

```markdown
# [API][E编号][状态码] 简述

## 1) 环境
- commit:
- 时间:
- base_url:
- live_llm: YES/NO

## 2) 复现步骤
- 步骤1:
- 步骤2:
- 步骤3:

## 3) 复现请求
- Method:
- URL:
- Headers:
- Body:

## 4) 预期结果
- 

## 5) 实际结果
- 状态码:
- 响应体:

## 6) 影响评估
- 严重级别: 阻断/高/中/低
- 影响链路:

## 7) 重试结果
- 是否可恢复:
- 重试次数:
```

## 10. 通过判定与汇总模板
通过条件：
1. 29 接口正向全部执行完成且有证据
2. 每模块至少 1 条负向用例已执行
3. LLM 4 接口已执行稳定性规则
4. 所有失败均完成缺陷提报

汇总模板：

```markdown
# API 全接口测试汇总

## 执行信息
- 执行人:
- 时间:
- base_url: http://127.0.0.1:8000
- live LLM: YES/NO

## 总览
- 总接口数: 29
- 正向通过:
- 正向失败:
- 负向通过:
- 负向失败:
- 阻断:

## LLM 稳定性
- E08 成功/重试成功/失败:
- E13 成功/重试成功/失败:
- E19 成功/重试成功/失败:
- E23 成功/重试成功/失败:
- E23 degraded 次数:

## 失败明细
| Case | 接口 | 实际状态码 | 预期状态码 | Bug编号 | 备注 |
| --- | --- | --- | --- | --- | --- |

## 结论
- PASS / FAIL
- 下一步建议:
```

## 11. 常见失败与排障
1. `404 /healthz`：应使用 `/health`
2. `422 json_invalid`：请求体不是合法 JSON
3. `422`：字段越界或必填缺失（如 `risk_level`、`count`、`stage`）
4. `400`：业务校验失败（如非法 event_name）
5. `502`：LLM 上游不稳定，按规则重试并留证据
6. `503 /health`：数据库不可用，先修复环境

## 12. 附录
### 12.1 事件白名单
1. onboarding_started
2. onboarding_completed
3. identity_models_generated
4. identity_selected
5. launch_kit_generated
6. content_published
7. consistency_check_triggered
8. experiment_created
9. monetization_plan_started
10. first_revenue_or_lead_confirmed

### 12.2 说明
本手册默认使用 Apifox/Postman 执行，不依赖 PowerShell/curl 脚本。
