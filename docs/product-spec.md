# MCP 保修姬 - Product Spec

本文件定义产品目标、范围和核心业务规则，用于产品实现与接口设计对齐。

## 1. 项目定位

项目名: `MCP 保修姬`  
一句话: 基于 `FastMCP + FastAPI` 的电子保修卡管家，支持图片识别录入、保修倒计时、临期筛选和日均价值分析。

## 2. 技术栈与边界

| 层级 | 选型 | 说明 |
|---|---|---|
| 服务框架 | FastAPI | 提供 REST API |
| MCP | FastMCP | 提供 MCP Tools 能力 |
| 识别能力 | 通用多模态大模型 API | 通过统一适配层对接不同厂商模型，提取发票、订单截图、保修卡、设备铭牌字段 |
| 存储 | PostgreSQL | 关系型持久化存储，支持索引与复杂查询 |
| 语言 | Python 3.10+ | 类型标注、异步优先 |

系统分层:

1. `api` 层: FastAPI 路由、请求参数校验、响应模型。
2. `service` 层: 业务逻辑（保修计算、状态判断、排序筛选）。
3. `mcp` 层: MCP tool 定义与模型调用编排。
4. `repository` 层: PostgreSQL 读写与查询。

## 3. MVP 范围

必须实现:

1. 手动新增/更新/删除保修记录。
2. 图片识别提取后可入库（允许人工确认后入库）。
3. 关键词查询（设备昵称/品牌/型号/SN 模糊匹配）。
4. 倒计时与状态计算（在保/已过期，支持在保临期子状态）。
5. 筛选已过期与即将到期在保产品（默认阈值 30 天，可配置如 7/30 天）。
6. 日均价值计算，列表与详情展示，支持按日均价值排序（筛选可选）。

暂不纳入 MVP:

1. 多用户与权限系统。
2. 云端同步。
3. 消息推送（短信/邮件/IM）。

## 4. 统一数据模型

保修记录 `warranty_record` 推荐字段:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | `str` | 是 | UUID |
| `device_nickname` | `str` | 否 | 设备昵称，如“客厅电视” |
| `brand` | `str` | 是 | 品牌 |
| `model` | `str` | 否 | 型号 |
| `category` | `str` | 否 | 品类，如 laptop/phone |
| `serial_number` | `str` | 否 | SN 码 |
| `purchase_date` | `date` | 是 | 购买日期，`YYYY-MM-DD` |
| `warranty_term` | `int` | 是 | 保修期数值，> 0 |
| `warranty_unit` | `str` | 是 | 保修期单位，`month` 或 `year` |
| `purchase_price` | `float` | 否 | 购入价格，>= 0 |
| `asset_value` | `float` | 否 | 资产价值（购入价或登记价值），>= 0 |
| `asset_value_type` | `str` | 否 | `purchase` / `registered` |
| `currency` | `str` | 否 | 默认 `CNY` |
| `proof_image_urls` | `list[str]` | 否 | 凭证图片地址（发票/订单/保修卡/铭牌） |
| `source` | `str` | 否 | manual/image_extract |
| `notes` | `str` | 否 | 备注 |
| `created_at` | `datetime` | 是 | 创建时间 |
| `updated_at` | `datetime` | 是 | 更新时间 |

派生字段（不建议直接持久化）:

1. `warranty_months` = `warranty_term * 12`（当 `warranty_unit=year`）否则 `warranty_term`
2. `expiry_date` = `purchase_date + warranty_months`
3. `days_left` = `expiry_date - today`
4. `expired_days` = `abs(days_left)`（仅当 `days_left < 0`）
5. `status`:
   - `in_warranty`: `days_left >= 0`
   - `expired`: `days_left < 0`
6. `is_expiring_soon`:
   - `true`: `status=in_warranty` 且 `days_left <= soon_threshold`
   - `false`: 其他情况
7. `daily_value` = `base_value / max(days_used, 1)`
8. `base_value` 取值优先级: `asset_value` > `purchase_price`

## 5. 关键业务规则

1. 日期统一使用本地时区日期，不使用时间戳参与保修天数计算。
2. `purchase_date` 不得晚于当天。
3. `warranty_term` 必须为正整数，`warranty_unit` 只能是 `month/year`。
4. `purchase_price` 与 `asset_value` 至少填写一项；都缺失时 `daily_value` 返回 `null`。
5. 图片识别字段允许缺失，但入库前必须补齐 `brand/purchase_date/warranty_term/warranty_unit`。
6. 凭证图片支持多张，建议限制单条记录最多 9 张。
7. 查询与排序要支持组合条件（例如: `brand=Apple + is_expiring_soon=true`）。

## 6. API 与 MCP Tool 对齐

MCP tool 与 API 语义保持一致:

| MCP Tool | 建议 REST API | 功能 |
|---|---|---|
| `extract_warranty_from_image` | `POST /warranty/extract` | 识别并返回结构化字段 |
| `add_warranty_record` | `POST /warranty` | 新增记录 |
| `query_warranty` | `GET /warranty` | 按昵称/品牌/型号/SN 搜索并筛选排序 |
| `get_warranty_countdown` | `GET /warranty/{id}/countdown` | 返回到期日、剩余天数、已过期天数、状态 |
| `list_expiring_soon` | `GET /warranty/expiring-soon` | 临期列表 |
| `calculate_daily_value` | `GET /warranty/daily-value` | 日均价值列表 |
| `update_warranty_record` | `PUT /warranty/{id}` | 更新记录 |
| `delete_warranty_record` | `DELETE /warranty/{id}` | 删除记录 |

`GET /warranty` 推荐查询参数:

1. `q`: 关键词（匹配设备昵称/品牌/型号/SN）
2. `status`: `in_warranty` 或 `expired`
3. `expiring_within_days`: 如 `7`/`30`，仅返回在保且 N 天内到期
4. `sort_by`: `purchase_date` / `expiry_date` / `daily_value`
5. `order`: `asc` / `desc`

## 7. 展示要求

1. 详情页必须展示: 品牌、品类、型号、SN、购买日期、保修期、到期日、`days_left/expired_days`、状态、日均价值、凭证图片。
2. 列表页必须展示: 设备昵称（若有）、品牌、型号、状态、到期日、剩余天数、日均价值。
3. 列表页支持按 `daily_value` 排序；按 `daily_value` 筛选为可选能力。

响应格式建议:

```json
{
  "success": true,
  "message": "ok",
  "data": {}
}
```
