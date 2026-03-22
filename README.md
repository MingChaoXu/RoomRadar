# Hotel Spider MVP

第一版目标是先把酒店竞品价格监控的后端骨架跑通，覆盖：

1. 酒店录入
2. 周边竞品发现
3. 携程/美团价格采集接口骨架
4. 标准化价格快照存储
5. 基础看板查询

当前默认启用 `mock` 适配器模式，便于本地联调。后续接入高德 MCP、携程和美团真实采集时，只需要替换 adapter。

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
export AMAP_MCP_COMMAND=npx
export AMAP_MCP_ARGS="-y @amap/amap-maps-mcp-server"
uv run uvicorn hotel_spider.main:app --reload
```

当前实现走 `stdio MCP`，会在发现竞品时依次尝试：

1. `maps_geo` 用地址定位
2. `maps_text_search` 用酒店名兜底定位
3. `maps_around_search` 查周边酒店

如果你要试别的实现，例如 Python 版 `uvx amap-mcp-server`，也可以替换 `AMAP_MCP_COMMAND` 和 `AMAP_MCP_ARGS`，但我当前在这个项目里实际验证通过的是 npm 这一套。

## 环境变量

可参考 [`.env.example`](/mnt/d/Lab/workspace/trae_projects/hotel_spider/.env.example)

## 文档

1. [项目总方案](./docs/project-plan.md)
2. [PRD](./docs/prd.md)
3. [技术架构](./docs/architecture.md)
4. [数据库设计](./docs/database-schema.md)
5. [MVP 开发排期](./docs/roadmap.md)
