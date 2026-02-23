# MCP 保修姬

基于 `FastMCP + FastAPI` 的电子保修卡管理系统，支持图片识别录入、保修倒计时、到期筛选和日均价值分析。

## 项目目标

解决个人/家庭/小团队设备保修信息分散、过保遗忘、资产利用率不透明的问题。

核心能力:

1. 图片识别录入（发票、订单截图、保修卡、设备铭牌）
2. 保修倒计时（剩余天数/已过期天数、在保/过保状态）
3. 产品资产日均价值估算（按日均价值排序）
4. 快速查询与筛选（昵称/品牌/型号/SN、即将到期/已过期）

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端框架 | FastAPI |
| MCP 能力 | FastMCP |
| 识别能力 | 通用多模态大模型 API（可适配不同厂商） |
| 数据存储 | PostgreSQL |
| 语言 | Python 3.10+ |

## 数据模型（摘要）

核心对象: `warranty_record`

主要字段:

1. 设备信息: `device_nickname`, `brand`, `category`, `model`, `serial_number`
2. 购买与保修: `purchase_date`, `warranty_term`, `warranty_unit`
3. 资产价值: `purchase_price`, `asset_value`, `asset_value_type`, `currency`
4. 凭证与来源: `proof_image_urls`, `source`, `notes`

关键派生字段:

1. `expiry_date`
2. `days_left` / `expired_days`
3. `status` (`in_warranty` / `expired`)
4. `is_expiring_soon`
5. `daily_value`

详细定义见 `docs/product-spec.md`。

## API 规划（MVP）

| 能力 | 方法 | 路径 |
|---|---|---|
| 图片识别抽取 | `POST` | `/warranty/extract` |
| 新增记录 | `POST` | `/warranty` |
| 查询/筛选/排序 | `GET` | `/warranty` |
| 保修倒计时 | `GET` | `/warranty/{id}/countdown` |
| 即将到期列表 | `GET` | `/warranty/expiring-soon` |
| 日均价值列表 | `GET` | `/warranty/daily-value` |
| 更新记录 | `PUT` | `/warranty/{id}` |
| 删除记录 | `DELETE` | `/warranty/{id}` |

`GET /warranty` 推荐参数:

1. `q`（昵称/品牌/型号/SN 关键词）
2. `status`（`in_warranty` / `expired`）
3. `expiring_within_days`（如 `7` / `30`）
4. `sort_by`（`purchase_date` / `expiry_date` / `daily_value`）
5. `order`（`asc` / `desc`）

## 开发状态

当前仓库以文档和规范为主，代码实现按以下里程碑推进:

1. 数据模型 + CRUD + PostgreSQL 仓储
2. 倒计时/状态/临期筛选 + 单元测试
3. 图片识别接入 + 人工确认流
4. MCP Tool 发布 + 文档完善

## 文档索引

1. 产品规格: `docs/product-spec.md`
2. 协作规范: `AGENTS.md`
3. Claude 入口说明: `CLAUDE.md`

## License

本项目使用 `MIT` 许可证，详见 `LICENSE`。
