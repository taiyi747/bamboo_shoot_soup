# MVP 端到端实施计划（按 AGENTS / product-spec）

## 1. 输入摘要（AGENTS 2.1）

- `user_goal`: 完成 MVP 需求的实施计划（不限于 SQLAlchemy/Alembic）。
- `stage`: `MVP`
- `target_persona`: Creator（普通用户，见 `docs/product-spec.md` 2.2）
- `constraints`:
  - 架构基线：FastAPI + Tauri v2 + Nuxt 4 + SQLite + localhost HTTP（AGENTS 4.1/4.2）
  - 周期：2-4 周（`docs/product-spec.md` 2.5）
  - 强规则：2.6 业务规则必须可验证
- `existing_assets`: 当前仓库仅有文档，无工程脚手架与实现代码。

## 2. MVP 范围与非范围

范围（`docs/product-spec.md` 2.5 MVP）：

1. 身份诊断（问卷 + 对话追问）与能力画像
2. 身份模型生成（3-5 个）与主/备身份选择
3. 人格宪法生成
4. 草稿一致性检查（偏离项/原因/建议 + 风险提醒）
5. 7-Day Launch Kit 生成
6. MVP 关键事件埋点（2.8）

非范围：

1. V1：内容矩阵、增长实验面板、变现路线图
2. V2：人格模拟器、观点资产库自动生长

## 3. MVP 强制交付物（`docs/product-spec.md` 3）

1. `Identity Model Card`
2. `Persona Constitution`
3. `7-Day Launch Kit`
4. `Risk & Boundary List`

完成标准（DoD）：

1. 交付物字段口径对齐 2.3，不新增冲突字段
2. 每个交付物可被保存、查询、版本化（至少宪法支持版本）
3. 交付物可串联端到端流程（2.4：诊断 -> 身份生成 -> 选择 -> 启动包 -> 一致性检查）

## 4. 架构与模块拆分

### 4.1 Backend（FastAPI）

模块：

1. `onboarding`：问卷会话、追问、能力画像生成
2. `identity`：身份模型生成与主/备选择
3. `persona`：人格宪法生成与版本管理
4. `launch_kit`：7 日主题与草稿/大纲生成
5. `consistency`：草稿一致性检查
6. `analytics`：埋点事件落库与查询

建议 API（MVP）：

1. `POST /api/v1/onboarding/sessions`
2. `POST /api/v1/onboarding/sessions/{session_id}/complete`
3. `POST /api/v1/identity-models/generate`
4. `POST /api/v1/identity-selections`
5. `POST /api/v1/persona-constitutions/generate`
6. `POST /api/v1/launch-kits/generate`
7. `POST /api/v1/consistency-checks`
8. `POST /api/v1/events`

### 4.2 Frontend（Tauri v2 + Nuxt 4）

页面流：

1. Onboarding 诊断页
2. 身份候选对比与主/备选择页
3. 人格宪法查看/编辑页
4. 7-Day Launch Kit 看板页
5. 草稿一致性检查页

MVP UI 重点：

1. 保证完整主流程可走通
2. 先实现单用户本地模式
3. 每一步有明确“下一步入口”和错误重试

### 4.3 数据层（SQLite + SQLAlchemy + Alembic）

数据模型与迁移拆分采用：`docs/mvp-sqlalchemy-alembic-plan.md`。  
此文档作为 MVP 数据子计划，属于本计划的 Workstream-C。

## 5. 规则落地（`docs/product-spec.md` 2.6）

实现要求：

1. 身份模型生成必须强制：
  - 差异化定位非空
  - 变现验证顺序存在
  - 语气示例不少于 5 句
  - 风险与禁区与用户风险承受度关联
2. 一致性检查输出必须包含：
  - 偏离项
  - 偏离原因
  - 修改建议
3. 触发风险边界时必须输出明确提醒
4. 不允许输出违法/冒充/侵权/虚假陈述建议

## 6. 埋点方案（`docs/product-spec.md` 2.8）

MVP 必打事件：

1. `onboarding_started`
2. `onboarding_completed`
3. `identity_models_generated`
4. `identity_selected`
5. `launch_kit_generated`
6. `consistency_check_triggered`

预留事件（可落库但不强制在首轮 UI 触发）：

1. `content_published`
2. `experiment_created`
3. `monetization_plan_started`
4. `first_revenue_or_lead_confirmed`

每个事件统一字段：

1. `user_id`
2. `occurred_at`
3. `stage`（MVP/V1/V2）
4. `identity_model_id`（如适用）

## 7. 里程碑拆解（`docs/product-spec.md` 2.9）

1. `M0`（诊断能力）
  - 问卷字段覆盖六类维度
  - 生成可保存的能力画像
2. `M1`（身份生成）
  - 3-5 候选身份完整生成
  - 主/备身份选择可保存
3. `M2`（人格宪法 + 检查）
  - 宪法可编辑并版本化
  - 检查结果含偏离/原因/建议
4. `M3`（7-Day Launch Kit）
  - 7 日主题 + 草稿/大纲
  - 至少 1 个增长实验建议
5. `M4`（内测数据）
  - 埋点可支撑 7 日发布率与 W4 留存统计

## 8. 测试计划（按 AGENTS 5）

自动化测试（必须）：

1. 新功能正向测试（每模块至少 1 个）：
  - Onboarding 完成
  - 身份模型生成 3-5 个
  - 主/备身份选择成功
  - 人格宪法生成成功
  - 7-Day Launch Kit 生成成功
  - 一致性检查成功
2. 规则约束测试：
  - 语气示例 < 5 句时报错
  - 差异化定位为空时报错
  - 风险触发但无提醒时报错
3. 回归测试（缺陷修复必须新增）
4. 迁移测试：Alembic 升降级链路

手工验收脚本（若某环节暂未自动化）：

1. 从空库启动，按 UI 流程走完整个 MVP
2. 检查四类交付物均可查询
3. 检查埋点事件是否按口径落库

## 9. 执行顺序（建议）

1. 建后端骨架 + 迁移骨架（Day 1-2）
2. 打通 M0/M1（Day 3-6）
3. 打通 M2/M3（Day 7-10）
4. 补 M4 埋点与统计查询（Day 11-12）
5. 测试补齐与联调修复（Day 13-14）

## 10. 风险与应对

1. 风险：LLM 输出字段漂移导致交付物不完整  
应对：统一 response schema + 服务层强校验 + 失败重试

2. 风险：规则命中但无显式报错  
应对：2.6 规则编程化，加入 API 级测试

3. 风险：只做功能不做埋点，M4 无法验收  
应对：事件落库作为主流程内步骤，不作为可选项
