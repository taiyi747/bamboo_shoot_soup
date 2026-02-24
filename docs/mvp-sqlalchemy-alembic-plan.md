# MVP 数据层 Plan（SQLAlchemy / Alembic）

## 1. 输入门禁（按 AGENTS 2.1 补全）

- `user_goal`: 产出仅面向 MVP 的数据层实施计划，技术方案限定为 SQLAlchemy + Alembic。
- `stage`: `MVP`
- `target_persona`: Creator（普通用户，见 `docs/product-spec.md` 2.2）
- `constraints`:
  - 时间：MVP 周期 2-4 周（见 2.5）
  - 架构：FastAPI + SQLite + localhost HTTP + Desktop-first（见 AGENTS 4.1/4.2）
  - 风险：必须满足强制业务规则与埋点口径（见 2.6/2.8）
- `existing_assets`: 当前仓库仅有产品/规范文档，尚无后端代码与迁移脚手架。

## 2. MVP 范围（仅覆盖 product-spec 2.5 MVP）

覆盖模块：

1. 身份诊断（能力画像）
2. 3-5 身份模型生成与主/备选择
3. 人格宪法（基础一致性引擎数据基础）
4. 7 天启动包
5. 草稿一致性检查记录
6. MVP 埋点事件（2.8）

不纳入本轮：

1. V1 的内容矩阵、实验面板、变现路线图
2. V2 的人格模拟器与观点资产库

## 3. 业务对象到数据模型映射（product-spec 2.3 / 3）

| 交付物/对象 | SQLAlchemy 实体 | 关键字段（示例） |
| --- | --- | --- |
| 能力画像卡（M0） | `CapabilityProfile` | `skill_stack_json`, `interest_energy_curve_json`, `cognitive_style`, `value_boundaries_json`, `risk_tolerance`, `time_investment_hours` |
| Identity Model Card | `IdentityModel` | `title`, `target_audience_pain`, `content_pillars_json`, `tone_keywords_json`, `tone_examples_json`, `long_term_views_json`, `differentiation`, `growth_path_0_3m`, `growth_path_3_12m`, `monetization_validation_order_json` |
| 主/备身份选择 | `IdentitySelection` | `primary_identity_id`, `backup_identity_id`, `selected_at` |
| Persona Constitution | `PersonaConstitution` | `common_words_json`, `forbidden_words_json`, `sentence_preferences_json`, `moat_positions_json`, `narrative_mainline`, `growth_arc_template`, `version` |
| 7-Day Launch Kit | `LaunchKit`, `LaunchKitDay` | `sustainable_columns_json`, `growth_experiment_suggestion_json`, `day_no`, `theme`, `draft_or_outline`, `opening_text` |
| Risk & Boundary List | `RiskBoundaryItem` | `risk_level`, `boundary_type`, `statement`, `source` |
| 一致性检查结果 | `ConsistencyCheck` | `draft_text`, `deviation_items_json`, `deviation_reasons_json`, `suggestions_json`, `risk_triggered`, `risk_warning` |
| 埋点事件 | `EventLog` | `event_name`, `stage`, `user_id`, `identity_model_id`, `payload_json`, `occurred_at` |

补充基础实体：

- `User`
- `OnboardingSession`

## 4. 约束设计（落实 product-spec 2.6）

数据库层约束：

1. `IdentityModel.differentiation` 非空（`NOT NULL` + 空串校验）
2. `IdentitySelection` 强制主/备身份都存在，且两者不同（`CHECK (primary_identity_id <> backup_identity_id)`）
3. `ConsistencyCheck` 当 `risk_triggered = 1` 时 `risk_warning` 必填（条件约束）
4. `EventLog.stage` 限定 `MVP/V1/V2`

服务层校验（Pydantic/Domain Service）：

1. `tone_examples_json` 至少 5 句
2. `long_term_views_json` 在 5-10 条范围
3. `monetization_validation_order_json` 至少 1 步，且顺序明确
4. 一致性检查输出必须包含偏离项/偏离原因/修改建议三段

## 5. Alembic 迁移拆分（建议 5 个 revision）

1. `0001_init_user_onboarding_profile`
  - `users`
  - `onboarding_sessions`
  - `capability_profiles`

2. `0002_identity_model_and_selection`
  - `identity_models`
  - `identity_selections`

3. `0003_persona_and_risk_boundary`
  - `persona_constitutions`
  - `risk_boundary_items`

4. `0004_launch_kit`
  - `launch_kits`
  - `launch_kit_days`

5. `0005_consistency_and_events`
  - `consistency_checks`
  - `event_logs`
  - MVP 索引（`user_id`, `identity_model_id`, `occurred_at`, `event_name`）

说明：

- SQLite 作为 MVP 默认持久化（AGENTS 4.1），Alembic 迁移需兼容 SQLite DDL 限制。
- 每个 revision 都应提供 downgrade，保障本地迭代可回滚。

## 6. 建议目录骨架（实施时）

```text
backend/
  app/
    db/
      base.py
      session.py
    models/
      user.py
      onboarding.py
      capability_profile.py
      identity_model.py
      identity_selection.py
      persona_constitution.py
      risk_boundary_item.py
      launch_kit.py
      consistency_check.py
      event_log.py
  alembic.ini
  migrations/
    env.py
    script.py.mako
    versions/
```

## 7. 测试计划（实施阶段执行）

自动化测试（最小集）：

1. 迁移链路测试：`upgrade base -> head` 成功
2. 回滚测试：`downgrade -1` 可执行（至少验证最新 revision）
3. 约束测试：
  - 空 `differentiation` 写入失败
  - 主/备身份相同写入失败
  - `risk_triggered=1` 且无 `risk_warning` 写入失败
4. 服务层规则测试：
  - 语气示例不足 5 条应失败
  - 一致性检查结果缺少三段结构应失败
5. 事件口径测试：
  - `event_name` 与 `stage` 落库并可按 `user_id + occurred_at` 查询

## 8. 交付节奏（MVP 内）

1. Week 1：建库脚手架、`0001/0002`、模型基础测试
2. Week 2：`0003/0004`、主流程对象打通（M0-M3）
3. Week 3：`0005`、埋点与一致性检查记录打通（M2/M4 准备）
4. Week 4：补齐回归测试、迁移回滚验证、准备联调

## 9. 验收映射（product-spec 2.9）

- M0：`capability_profiles` 可完整承载六类维度
- M1：`identity_models + identity_selections` 支持 3-5 候选与主/备选择
- M2：`persona_constitutions + consistency_checks` 支持可编辑、可版本、可偏离提示
- M3：`launch_kits + launch_kit_days` 支持 7 日主题/草稿与增长实验建议
- M4：`event_logs` 支持 7 日发布率、W4 留存、可执行性评分的后续统计基础
