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
| 识别能力 | Claude Vision / OCR | 从发票、铭牌、截图提取字段 |
| 存储 | SQLite（优先）/ JSON（兜底） | 本地轻量存储 |
| 语言 | Python 3.10+ | 类型标注、异步优先 |

系统分层:

1. `api` 层: FastAPI 路由、请求参数校验、响应模型。
2. `service` 层: 业务逻辑（保修计算、状态判断、排序筛选）。
3. `mcp` 层: MCP tool 定义与模型调用编排。
4. `repository` 层: SQLite/JSON 读写与查询。

## 3. MVP 范围

必须实现:

1. 手动新增/更新/删除保修记录。
2. 图片识别提取后可入库（允许人工确认后入库）。
3. 关键词查询（品牌/型号/SN 模糊匹配）。
4. 倒计时与状态计算（在保/临期/过保）。
5. 临期筛选（默认阈值 30 天，可配置）。
6. 日均价值计算与排序。

暂不纳入 MVP:

1. 多用户与权限系统。
2. 云端同步。
3. 消息推送（短信/邮件/IM）。

## 4. 统一数据模型

保修记录 `warranty_record` 推荐字段:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | `str` | 是 | UUID |
| `brand` | `str` | 是 | 品牌 |
| `model` | `str` | 否 | 型号 |
| `category` | `str` | 否 | 品类，如 laptop/phone |
| `serial_number` | `str` | 否 | SN 码 |
| `purchase_date` | `date` | 是 | 购买日期，`YYYY-MM-DD` |
| `warranty_months` | `int` | 是 | 保修月数，> 0 |
| `price` | `float` | 否 | 购入价格，>= 0 |
| `currency` | `str` | 否 | 默认 `CNY` |
| `source` | `str` | 否 | manual/image_extract |
| `notes` | `str` | 否 | 备注 |
| `created_at` | `datetime` | 是 | 创建时间 |
| `updated_at` | `datetime` | 是 | 更新时间 |

派生字段（不建议直接持久化）:

1. `expiry_date` = `purchase_date + warranty_months`
2. `days_left` = `expiry_date - today`
3. `status`:
   - `active`: `days_left > soon_threshold`
   - `expiring_soon`: `0 <= days_left <= soon_threshold`
   - `expired`: `days_left < 0`
4. `daily_value` = `price / max(days_used, 1)`

## 5. 关键业务规则

1. 日期统一使用本地时区日期，不使用时间戳参与保修天数计算。
2. `purchase_date` 不得晚于当天。
3. `warranty_months` 必须为正整数。
4. `price` 缺失时，`daily_value` 返回 `null`，不抛错。
5. 图片识别字段允许缺失，但入库前必须补齐 `brand/purchase_date/warranty_months`。
6. 查询与排序要支持组合条件（例如: `brand=Apple + status=expiring_soon`）。

## 6. API 与 MCP Tool 对齐

MCP tool 与 API 语义保持一致:

| MCP Tool | 建议 REST API | 功能 |
|---|---|---|
| `extract_warranty_from_image` | `POST /warranty/extract` | 识别并返回结构化字段 |
| `add_warranty_record` | `POST /warranty` | 新增记录 |
| `query_warranty` | `GET /warranty` | 搜索/筛选/排序 |
| `get_warranty_countdown` | `GET /warranty/{id}/countdown` | 返回到期日、剩余天数、状态 |
| `list_expiring_soon` | `GET /warranty/expiring-soon` | 临期列表 |
| `calculate_daily_value` | `GET /warranty/daily-value` | 日均价值列表 |
| `update_warranty_record` | `PUT /warranty/{id}` | 更新记录 |
| `delete_warranty_record` | `DELETE /warranty/{id}` | 删除记录 |

响应格式建议:

```json
{
  "success": true,
  "message": "ok",
  "data": {}
}
```
