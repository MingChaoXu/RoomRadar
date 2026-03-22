# 酒店竞品价格爬虫工具数据库设计

更新时间：2026-03-22

## 1. 设计原则

1. 原始采集数据与标准化结果分层存储。
2. 保留可追溯字段，方便回放和排障。
3. 价格快照支持时间序列分析。

## 2. 核心表

### 2.1 `hotels`

目标酒店和标准酒店主数据。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint pk | 主键 |
| hotel_code | varchar(64) | 内部酒店编码 |
| name | varchar(255) | 标准酒店名 |
| alias_name | varchar(255) | 别名 |
| brand | varchar(128) | 品牌 |
| star_level | int | 星级 |
| province | varchar(64) | 省 |
| city | varchar(64) | 市 |
| district | varchar(64) | 区 |
| address | varchar(255) | 地址 |
| lng | numeric(10,6) | 经度 |
| lat | numeric(10,6) | 纬度 |
| business_area | varchar(128) | 商圈 |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

### 2.2 `hotel_platform_mapping`

标准酒店与平台酒店的映射关系。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint pk | 主键 |
| hotel_id | bigint | 标准酒店 ID |
| platform | varchar(32) | `amap` / `ctrip` / `meituan` |
| platform_hotel_id | varchar(128) | 平台酒店 ID |
| platform_hotel_name | varchar(255) | 平台酒店名称 |
| match_score | numeric(5,2) | 匹配分 |
| match_status | varchar(32) | matched/manual/pending |
| raw_payload | jsonb | 原始数据 |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

### 2.3 `competitor_groups`

目标酒店与竞品关系。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint pk | 主键 |
| target_hotel_id | bigint | 目标酒店 |
| competitor_hotel_id | bigint | 竞品酒店 |
| distance_meters | int | 距离 |
| radius_bucket | varchar(32) | 半径圈层 |
| source | varchar(32) | amap/manual |
| enabled | boolean | 是否启用 |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

### 2.4 `crawl_jobs`

任务主表。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint pk | 主键 |
| job_type | varchar(32) | discover/rate_collect |
| platform | varchar(32) | amap/ctrip/meituan |
| hotel_id | bigint | 酒店 ID |
| payload | jsonb | 请求参数 |
| status | varchar(32) | pending/running/success/failed |
| priority | int | 优先级 |
| retry_count | int | 重试次数 |
| scheduled_at | timestamptz | 调度时间 |
| started_at | timestamptz | 开始时间 |
| finished_at | timestamptz | 结束时间 |
| error_message | text | 错误信息 |
| created_at | timestamptz | 创建时间 |

### 2.5 `crawl_raw_results`

原始采集结果。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint pk | 主键 |
| job_id | bigint | 任务 ID |
| platform | varchar(32) | 平台 |
| hotel_id | bigint | 标准酒店 ID |
| platform_hotel_id | varchar(128) | 平台酒店 ID |
| check_in_date | date | 入住日 |
| check_out_date | date | 离店日 |
| request_payload | jsonb | 请求参数 |
| response_payload | jsonb | 结构化原始结果 |
| html_path | varchar(255) | HTML 存储路径 |
| screenshot_path | varchar(255) | 截图路径 |
| collected_at | timestamptz | 采集时间 |
| created_at | timestamptz | 创建时间 |

### 2.6 `room_type_dictionary`

标准房型字典。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint pk | 主键 |
| room_type_code | varchar(64) | 标准房型编码 |
| room_type_name | varchar(128) | 标准房型名称 |
| bed_type | varchar(32) | 床型 |
| breakfast_rule | varchar(64) | 早餐规则 |
| cancel_rule | varchar(64) | 取消规则 |
| occupancy | int | 可住人数 |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

### 2.7 `platform_room_mapping`

平台房型与标准房型映射。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint pk | 主键 |
| hotel_id | bigint | 酒店 ID |
| platform | varchar(32) | 平台 |
| platform_room_name | varchar(255) | 平台房型名称 |
| room_type_id | bigint | 标准房型 ID |
| match_score | numeric(5,2) | 匹配分 |
| match_status | varchar(32) | matched/manual/pending |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

### 2.8 `rate_snapshots`

标准化后的价格快照主表。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint pk | 主键 |
| hotel_id | bigint | 酒店 ID |
| platform | varchar(32) | 平台 |
| platform_hotel_id | varchar(128) | 平台酒店 ID |
| room_type_id | bigint | 标准房型 ID |
| check_in_date | date | 入住日 |
| check_out_date | date | 离店日 |
| adults | int | 成人数 |
| children | int | 儿童数 |
| nights | int | 间夜数 |
| currency | varchar(16) | 币种 |
| display_price | numeric(10,2) | 展示价 |
| final_price | numeric(10,2) | 最终价 |
| member_price | numeric(10,2) | 会员价 |
| coupon_discount | numeric(10,2) | 券优惠 |
| tax_included | boolean | 是否含税 |
| breakfast_included | boolean | 是否含早 |
| free_cancel | boolean | 是否可免费取消 |
| inventory_status | varchar(32) | available/sold_out |
| captured_at | timestamptz | 采集时间 |
| created_at | timestamptz | 创建时间 |

建议唯一索引：

`(hotel_id, platform, room_type_id, check_in_date, check_out_date, adults, children, captured_at)`

### 2.9 `price_alerts`

价格告警表。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint pk | 主键 |
| hotel_id | bigint | 目标酒店 |
| competitor_hotel_id | bigint | 竞品酒店 |
| platform | varchar(32) | 平台 |
| alert_type | varchar(32) | drop/rise/gap/anomaly |
| alert_value | numeric(10,2) | 变化值 |
| alert_payload | jsonb | 详细内容 |
| status | varchar(32) | open/closed/ignored |
| detected_at | timestamptz | 发现时间 |
| created_at | timestamptz | 创建时间 |

## 3. 关系说明

1. `hotels` 是标准酒店主表。
2. `hotel_platform_mapping` 维护标准酒店与平台酒店映射。
3. `competitor_groups` 维护目标酒店和竞品酒店的关系。
4. `crawl_jobs` 管理任务生命周期。
5. `crawl_raw_results` 保存原始采集结果。
6. `platform_room_mapping` 和 `room_type_dictionary` 负责房型归一。
7. `rate_snapshots` 是报表查询核心表。

## 4. 建议索引

### 4.1 `hotel_platform_mapping`

1. `(platform, platform_hotel_id)` 唯一索引
2. `(hotel_id, platform)` 普通索引

### 4.2 `competitor_groups`

1. `(target_hotel_id, enabled)`
2. `(competitor_hotel_id)`

### 4.3 `crawl_jobs`

1. `(status, scheduled_at)`
2. `(platform, status)`
3. `(hotel_id, created_at desc)`

### 4.4 `rate_snapshots`

1. `(hotel_id, check_in_date, platform)`
2. `(hotel_id, captured_at desc)`
3. `(platform, platform_hotel_id, check_in_date)`

## 5. 分区建议

如果采集规模上来，建议 `rate_snapshots` 和 `crawl_raw_results` 按月分区。

## 6. 数据保留策略

1. `rate_snapshots` 长期保留。
2. `crawl_raw_results.response_payload` 保留 90 到 180 天。
3. HTML 和截图可按对象存储生命周期策略清理。
