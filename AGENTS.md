# AGENTS.md

## 0. 文档定位与优先级

本文件只定义 AI 协作执行规则，不再重复产品与业务规格细节。

优先级如下：

1. `docs/product-spec.md`（产品与业务事实单一来源）
2. `AGENTS.md`（AI 执行方式与门禁）
3. `docs/PRD.md`（背景与方向说明）

若存在冲突：业务语义以 `docs/product-spec.md` 为准；执行流程与交付格式以 `AGENTS.md` 为准。

## 1. 去重原则（引用 product-spec，不重复维护）

以下内容统一引用 `docs/product-spec.md`，本文件不再重复展开：

- 产品定义、目标用户、核心价值、产品边界：见 `docs/product-spec.md` 第 1 节。
- 业务目标、核心漏斗指标、质量指标：见 `docs/product-spec.md` 第 2.1 节。
- 业务角色与核心业务对象（字段定义）：见 `docs/product-spec.md` 第 2.2-2.3 节。
- 端到端流程：见 `docs/product-spec.md` 第 2.4 节。
- 分阶段功能规格（MVP/V1/V2）：见 `docs/product-spec.md` 第 2.5 节。
- 强制业务规则：见 `docs/product-spec.md` 第 2.6 节。
- 数据埋点与事件字段：见 `docs/product-spec.md` 第 2.8 节。
- 里程碑验收标准（M0-M4）：见 `docs/product-spec.md` 第 2.9 节。
- 标准化交付清单：见 `docs/product-spec.md` 第 3 节。

## 2. AI 执行基线（本文件负责）

### 2.1 最小输入门禁

每次任务至少包含：

- `user_goal`
- `stage`（`MVP` / `V1` / `V2`）
- `target_persona`
- `constraints`（时间/风险/平台）
- `existing_assets`

任一缺失时，必须先补全输入，再进入生成。

### 2.2 交付一致性门禁

- 交付物名称与结构必须对齐 `docs/product-spec.md` 第 3 节。
- 不允许发明与规格冲突的字段名或阶段口径。
- 对产物内容的业务判断，必须引用 `docs/product-spec.md` 对应章节。

## 3. Run Report Interface（每次执行必须）

```markdown
## Run Report
### 1) 输入摘要
- user_goal:
- stage:
- target_persona:
- constraints:
- existing_assets:

### 2) 生成结果
- artifacts_generated:
- artifact_completeness:
- spec_refs_used:  # 例如 2.3 / 2.6 / 3

### 3) 校验结果
- spec_alignment: PASS/FAIL
- failed_spec_refs:
- failure_reasons:
- tech_stack_alignment: PASS/FAIL
- test_alignment: PASS/FAIL

### 4) 风险提示
- compliance_risks:
- delivery_risks:

### 5) 下一步动作
- next_actions:
- owner:

### 6) 埋点建议
- events_to_log:  # 事件名与字段口径对齐 product-spec 2.8

### 7) 测试执行
- test_required: YES/NO + reason
- test_plan:
- test_results: PASS/FAIL/NOT_RUN
- test_evidence:
- uncovered_risks:
```

## 4. 技术栈与架构基线

### 4.1 技术栈声明（MVP 基线）

| 维度 | 基线选型 | 说明 |
| --- | --- | --- |
| Backend API | `FastAPI`（Python） | FastAPI 0.x 主线，Pydantic v2 生态 |
| Backend Data | `SQLAlchemy + Alembic` | ORM + 迁移管理（MVP 默认） |
| Frontend | `Tauri v2 + Nuxt 4` | 桌面端 UI |
| Frontend Toolchain | `bun` | 前端依赖安装与脚本执行默认工具 |
| Persistence | `SQLite`（MVP） | 默认本地持久化 |
| Communication | `HTTP localhost` | 前端通过本地 HTTP API 调后端 |
| Runtime Mode | `Desktop-first (Local-first)` | 本地桌面优先 |

### 4.2 Runtime Topology Contract

- `FastAPI` 作为本地服务进程启动。
- 后端数据访问层默认使用 `SQLAlchemy`，数据库版本演进默认使用 `Alembic`。
- `Tauri + Nuxt` 作为本地桌面前端，调用 `http://127.0.0.1:<port>`。
- 前端默认使用 `bun` 执行依赖安装与脚本命令。
- 端口允许配置化，但必须支持探测与重试。
- 当前不以云端部署为默认路径。

### 4.3 一致性规则（硬约束）

- 不接受 `Electron`、`Flask`、`Django` 作为默认替代。
- 不接受以 `npm` / `yarn` / `pnpm` 作为默认前端工具链口径（文档默认口径为 `bun`）。
- 不接受 `invoke-only` 作为默认前后端通信。
- 不接受 `JSON 文件` 作为默认持久化。

## 5. 测试硬约束（AI 必须执行）

- 任何影响行为的实现变更（代码、配置、Prompt 规则）必须包含测试。
- 新功能至少 1 个正向测试；缺陷修复至少 1 个回归测试。
- 若暂无法自动化，必须给可复现的手工验证步骤与风险说明。
- 未提供测试证据，或测试失败且无阻断原因，任务结论必须为 `FAIL`。

## 6. 维护机制

- 当前版本：`v1.2`
- 触发更新条件：
  - `docs/product-spec.md` 结构或口径变化
  - 技术栈默认基线变化
  - 测试/交付门禁变化

本文件为 AI 协作执行基线。业务细节请直接引用 `docs/product-spec.md`，不要在此重复维护。
