# MCP 保修姬 - AGENTS 指南

本文件用于约束本仓库中 AI/开发者协作方式，目标是让实现过程稳定、可复现、可测试。

产品说明与业务规格已迁移到 `product-spec.md`。

## 1. 代码规范

1. 强制类型标注，核心函数写 docstring。
2. Pydantic 模型用于请求/响应与持久化对象校验。
3. 业务逻辑不得直接写在路由层。
4. 所有对外错误返回统一错误码与消息结构。
5. 新增能力必须附带最小测试。

## 2. 测试要求

至少覆盖:

1. 保修状态边界: `days_left = -1/0/soon_threshold/soon_threshold+1`。
2. `daily_value` 计算: 价格缺失、使用天数 0、正常值。
3. 查询筛选: 关键词模糊匹配、状态筛选、组合筛选。
4. 图片提取后补全校验: 缺关键字段时拒绝入库。

推荐目录:

```
tests/
  test_service_countdown.py
  test_service_daily_value.py
  test_api_warranty.py
```

## 3. 里程碑建议

1. `Milestone 1`: 数据模型 + CRUD + SQLite 仓储。
2. `Milestone 2`: 倒计时/状态/临期筛选 + 单元测试。
3. `Milestone 3`: 图片识别接入 + 人工确认流。
4. `Milestone 4`: MCP tool 对外发布 + 文档完善。

## 4. 完成定义（DoD）

任务完成需同时满足:

1. 代码通过测试与基础 lint。
2. API 与 MCP tool 命名、语义一致。
3. 文档同步更新（README 或接口文档）。
4. 关键业务规则有测试覆盖。
5. 不引入未说明的破坏性变更。
