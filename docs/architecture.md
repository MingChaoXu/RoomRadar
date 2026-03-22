# 酒店竞品价格爬虫工具技术架构

更新时间：2026-03-22

## 1. 架构目标

1. 支持高德地图定位和竞品发现。
2. 支持多 OTA 采集适配。
3. 支持高并发定时采集与失败重试。
4. 支持历史价格快照和可追溯调试。

## 2. 分层设计

### 2.1 接入层

1. Web 管理后台
2. OpenAPI
3. 导出与通知接口

### 2.2 应用层

1. 酒店管理服务
2. 竞品管理服务
3. 采集任务服务
4. 报表服务
5. 告警服务

### 2.3 采集层

1. Amap Adapter
2. Ctrip Adapter
3. Meituan Adapter
4. Proxy Manager
5. Session Manager

### 2.4 数据处理层

1. 酒店匹配引擎
2. 房型标准化引擎
3. 价格清洗引擎
4. 规则告警引擎

### 2.5 存储层

1. PostgreSQL
2. Redis
3. 对象存储

## 3. 推荐部署结构

```text
browser workers x N
    ├─ ctrip browser adapter
    ├─ meituan browser adapter
    └─ raw artifacts uploader

api service x 2
    ├─ admin api
    ├─ report api
    └─ task orchestration api

infra
    ├─ postgresql
    ├─ redis
    └─ object storage
```

## 4. 组件职责

### 4.1 API Service

职责：

1. 提供酒店、竞品、价格查询接口。
2. 触发手动采集任务。
3. 管理报表和导出。

### 4.2 Scheduler

职责：

1. 按天生成采集任务。
2. 按优先级下发任务。
3. 控制限流、重试和超时。

### 4.3 Browser Worker

职责：

1. 启动 Playwright 浏览器。
2. 执行酒店查询和价格抓取。
3. 输出结构化结果与原始调试材料。

### 4.4 Standardization Engine

职责：

1. 处理酒店同名、别名和连锁分店问题。
2. 处理房型名称差异。
3. 输出统一价格快照。

## 5. 接口边界

### 5.1 Amap Adapter 输出

```json
{
  "poi_id": "B0FFF...",
  "name": "某某酒店",
  "address": "上海市xx路xx号",
  "lng": 121.4737,
  "lat": 31.2304,
  "category": "住宿服务"
}
```

### 5.2 OTA Adapter 输出

```json
{
  "platform": "ctrip",
  "platform_hotel_id": "123456",
  "hotel_name": "某某酒店",
  "check_in": "2026-04-01",
  "check_out": "2026-04-02",
  "room_name": "高级大床房",
  "bed_type": "double",
  "breakfast": "2份早餐",
  "cancel_policy": "限时取消",
  "display_price": 468,
  "final_price": 458,
  "currency": "CNY",
  "captured_at": "2026-03-22T09:00:00+08:00"
}
```

## 6. 技术取舍

### 6.1 Python 优先

适用于：

1. 团队偏数据工程
2. 需要快速落地分析和导出
3. 后续要做规则引擎和轻量模型

### 6.2 Node + Crawlee 优先

适用于：

1. 团队偏前端或 TS
2. 采集能力是系统重心
3. 需要成熟的代理、会话、浏览器控制能力

## 7. 可观测性设计

1. 每个采集任务保留 trace_id
2. 存储原始 HTML、截图、JSON 响应
3. 记录重试次数、代理出口、UA 和错误码
4. 对平台和城市维度做成功率监控

## 8. 安全与权限

1. 管理后台使用账号体系
2. 凭证统一放在环境变量或密钥管理器
3. 原始采集数据按租户或酒店分区隔离

## 9. 后续演进方向

1. 引入官方 API 替换部分浏览器采集
2. 增加飞猪、同程、去哪儿适配器
3. 引入预测模型做价格建议
