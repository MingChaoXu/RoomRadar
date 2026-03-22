# Hotel Spider MVP

第一版目标是先把酒店竞品价格监控的后端骨架跑通，覆盖：

1. 酒店录入
2. 周边竞品发现
3. 携程/美团价格采集接口骨架
4. 标准化价格快照存储
5. 基础看板查询

当前已经支持真实链路接入：

1. 高德 MCP 发现竞品
2. 携程 Playwright 登录态采价
3. 美团 Playwright 登录态采价
4. `/admin` 控制台地图、价格对比、采价状态展示

`mock` 模式仍然保留，便于在没有真实账号和 Key 的环境下联调。

## Quick Start

```bash
uv sync
uv run uvicorn hotel_spider.main:app --reload
```

默认服务地址：

```text
http://127.0.0.1:8000
```

管理台入口：

```text
http://127.0.0.1:8000/admin
```

## 主要接口

1. `GET /healthz`
2. `POST /api/v1/hotels`
3. `GET /api/v1/hotels`
4. `POST /api/v1/hotels/{hotel_id}/discover-competitors`
5. `POST /api/v1/rates/collect`
6. `GET /api/v1/hotels/{hotel_id}/dashboard`

## 高德 MCP 接入

默认 `AMAP_PROVIDER=mock`。如果要切真实高德 MCP：

```bash
export AMAP_PROVIDER=mcp
export AMAP_MAPS_API_KEY=你的高德Key
export AMAP_JS_API_KEY=你的高德Web端JSAPI Key
export AMAP_MCP_COMMAND=npx
export AMAP_MCP_ARGS="-y @amap/amap-maps-mcp-server"
uv run uvicorn hotel_spider.main:app --reload
```

当前实现走 `stdio MCP`，会在发现竞品时依次尝试：

1. `maps_geo` 用地址定位
2. `maps_text_search` 用酒店名兜底定位
3. `maps_around_search` 查周边酒店

如果你要试别的实现，例如 Python 版 `uvx amap-mcp-server`，也可以替换 `AMAP_MCP_COMMAND` 和 `AMAP_MCP_ARGS`，但我当前在这个项目里实际验证通过的是 npm 这一套。

如果你要在 `/admin` 里显示地图窗口，还需要配置 `AMAP_JS_API_KEY`。后端的 MCP Key 和前端 JSAPI Key 在实际项目里建议分开配置；如果没单独配置，当前实现会回退尝试复用 `AMAP_MAPS_API_KEY`。

## 当前真实接入状态

截至 `2026-03-22`，当前项目内已实际验证：

1. 高德 MCP 可用，能够基于酒店地址和名称发现周边竞品
2. 携程真实可用，已能抓到目标酒店和竞品酒店的真实房型价格
3. 美团单酒店真实可用，已能抓到列表最低价
4. 美团批量端到端采价仍会偶发触发风控，系统会明确返回验证地址，而不是只显示“暂无”

一次独立临时库的端到端验证结果是：

1. 目标酒店：`上海静安香格里拉大酒店`
2. 高德发现竞品：`璞丽酒店`、`Jing'anKerryApartments`
3. 携程价格可成功写入快照
4. 美团在该轮批量采价里返回 `blocked`，并附带 `verify.meituan.com` 验证链接

## 携程登录态接入

如果要抓携程真实价格，需要提供已登录的 `storage_state.json`：

```bash
export PLAYWRIGHT_BROWSERS_PATH=/home/你的用户名/tools/playwright-browsers
export CTRIP_PROVIDER=playwright
export CTRIP_STORAGE_STATE_PATH=/mnt/d/Lab/workspace/trae_projects/hotel_spider/storage_state.json
export CTRIP_HEADLESS=true
export MEITUAN_PROVIDER=playwright
export MEITUAN_STORAGE_STATE_PATH=/mnt/d/Lab/workspace/trae_projects/hotel_spider/meituan_storage_state.json
export MEITUAN_HEADLESS=true
```

当前项目已经验证：

1. 酒店名可映射到携程 `hotelId`
2. 详情页能触发真实房型接口 `33278/getHotelRoomListInland`
3. 未登录态价格会被隐藏
4. 所以真实价格抓取依赖登录态

## 美团接入说明

当前美团实现已经接到真实链路：

1. 可通过美团城市搜索接口把城市名映射到 `cityId`
2. 可构造酒店列表页 URL，并拿到真实 `hbsearch/HotelSearch` 请求
3. 提供登录态后，可抓取列表最低价
4. 如果命中风控，当前会明确返回：
   `美团触发风控验证，请先完成验证: https://verify.meituan.com/...`

建议实际操作流程：

1. 在 Windows 浏览器打开 `https://i.meituan.com/awp/h5/hotel/search/search.html`
2. 完成登录
3. 进入酒店搜索页、列表页、详情页至少各一次
4. 如出现风控验证，先人工完成
5. 重新导出 `meituan_storage_state.json`
6. 再回到 `/admin` 执行美团采价

如果单酒店能成功、批量采价又被拦，这是当前美团风控的正常表现，不是前端显示错误。

## `/admin` 控制台说明

当前 `/admin` 已支持：

1. 新增目标酒店
2. 触发真实高德发现竞品
3. 触发 `ctrip / meituan` 采价
4. 价格对比表、低价竞品告警、地图视图
5. 明确展示 `未采价 / 未匹配 / 无可售 / 风控验证` 等原因

页面顶部会展示：

1. `AMap Provider`
2. `Ctrip Provider / Ctrip State`
3. `Meituan Provider / Meituan State`

## 环境变量

可参考 [`.env.example`](/mnt/d/Lab/workspace/trae_projects/hotel_spider/.env.example)

## 文档

1. [项目总方案](./docs/project-plan.md)
2. [PRD](./docs/prd.md)
3. [技术架构](./docs/architecture.md)
4. [数据库设计](./docs/database-schema.md)
5. [MVP 开发排期](./docs/roadmap.md)
