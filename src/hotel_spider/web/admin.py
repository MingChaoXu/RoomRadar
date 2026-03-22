import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

from hotel_spider.core.config import get_settings

router = APIRouter(include_in_schema=False)


def render_admin_html() -> str:
    settings = get_settings()
    amap_js_api_key = settings.amap_js_api_key or settings.amap_maps_api_key or ""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Hotel Spider Control Room</title>
  <style>
    :root {
      --bg: #f1ecdf;
      --panel: rgba(255, 250, 240, 0.82);
      --ink: #14281d;
      --muted: #50615b;
      --line: rgba(20, 40, 29, 0.14);
      --accent: #c8553d;
      --accent-soft: #f0b67f;
      --shadow: 0 18px 50px rgba(48, 39, 33, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", "PingFang SC", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(240, 182, 127, 0.35), transparent 28%),
        radial-gradient(circle at top right, rgba(200, 85, 61, 0.18), transparent 24%),
        linear-gradient(180deg, #f7f1e6 0%, #ece4d5 100%);
      min-height: 100vh;
    }
    .wrap {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 40px;
    }
    .hero {
      display: grid;
      gap: 12px;
      margin-bottom: 22px;
    }
    .eyebrow {
      letter-spacing: 0.18em;
      text-transform: uppercase;
      font-size: 12px;
      color: var(--muted);
    }
    h1 {
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
      font-size: clamp(32px, 5vw, 54px);
      line-height: 0.95;
      font-weight: 700;
    }
    .hero p {
      margin: 0;
      max-width: 760px;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.6;
    }
    .quicklinks {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 8px;
    }
    .quicklinks a {
      color: var(--ink);
      text-decoration: none;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.55);
      padding: 10px 14px;
      border-radius: 999px;
      font-size: 14px;
    }
    .grid {
      display: grid;
      grid-template-columns: 1.1fr 1.3fr;
      gap: 16px;
      align-items: start;
    }
    .dashboard-grid {
      display: grid;
      grid-template-columns: 1.5fr 0.9fr;
      gap: 16px;
      align-items: start;
      margin-bottom: 16px;
    }
    .panel {
      background: var(--panel);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255,255,255,0.7);
      border-radius: 24px;
      box-shadow: var(--shadow);
      padding: 18px;
    }
    .panel h2 {
      margin: 0 0 6px;
      font-size: 18px;
    }
    .hint {
      margin: 0 0 14px;
      font-size: 13px;
      color: var(--muted);
    }
    form {
      display: grid;
      gap: 10px;
    }
    .row {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    label {
      display: grid;
      gap: 6px;
      font-size: 13px;
      color: var(--muted);
    }
    input, select, button, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 11px 12px;
      font: inherit;
      color: var(--ink);
      background: rgba(255,255,255,0.82);
    }
    button {
      cursor: pointer;
      background: linear-gradient(135deg, var(--accent), #8f2d1a);
      color: #fff7ef;
      border: none;
      font-weight: 600;
    }
    button.secondary {
      background: #fff6ea;
      color: var(--ink);
      border: 1px solid var(--line);
    }
    .table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    .scroll-panel {
      max-height: 720px;
      overflow: auto;
      padding-right: 4px;
    }
    .scroll-panel.compact {
      max-height: 560px;
    }
    .scroll-panel::-webkit-scrollbar {
      width: 10px;
      height: 10px;
    }
    .scroll-panel::-webkit-scrollbar-thumb {
      background: rgba(20, 40, 29, 0.18);
      border-radius: 999px;
    }
    .scroll-panel::-webkit-scrollbar-track {
      background: rgba(20, 40, 29, 0.04);
      border-radius: 999px;
    }
    .table th, .table td {
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }
    .table th {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }
    .pill {
      display: inline-flex;
      align-items: center;
      padding: 5px 10px;
      border-radius: 999px;
      background: rgba(20, 40, 29, 0.08);
      font-size: 12px;
    }
    .stack {
      display: grid;
      gap: 16px;
    }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }
    .status {
      min-height: 40px;
      padding: 10px 12px;
      border-radius: 14px;
      background: rgba(20, 40, 29, 0.05);
      color: var(--muted);
      font-size: 13px;
      white-space: pre-wrap;
    }
    .code {
      margin: 0;
      border-radius: 18px;
      padding: 14px;
      background: #18231d;
      color: #e9e2d0;
      overflow: auto;
      font-size: 13px;
      line-height: 1.5;
    }
    .metric {
      font-size: 12px;
      color: var(--muted);
    }
    .alert-list {
      display: grid;
      gap: 10px;
      margin: 12px 0 0;
    }
    .alert-card {
      border: 1px solid rgba(200, 85, 61, 0.18);
      background: rgba(200, 85, 61, 0.08);
      border-radius: 18px;
      padding: 12px;
    }
    .alert-card strong {
      display: block;
      margin-bottom: 6px;
    }
    .alert-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      font-size: 12px;
      color: var(--muted);
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin: 12px 0;
    }
    .stat-card {
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 12px;
      background: rgba(255,255,255,0.62);
    }
    .stat-card strong {
      display: block;
      margin-top: 6px;
      font-size: 22px;
      line-height: 1;
      font-variant-numeric: tabular-nums;
    }
    .price {
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }
    .positive {
      color: #8f2d1a;
    }
    .negative {
      color: #1e6f5c;
    }
    .target-row {
      background: rgba(240, 182, 127, 0.14);
    }
    .risk-row {
      background: rgba(200, 85, 61, 0.08);
    }
    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: end;
      margin: 12px 0;
    }
    .side-stack {
      display: grid;
      gap: 16px;
    }
    .map-shell {
      border: 1px solid var(--line);
      border-radius: 20px;
      overflow: hidden;
      background: rgba(255,255,255,0.42);
    }
    .map-canvas {
      width: 100%;
      height: 320px;
      background:
        linear-gradient(135deg, rgba(240, 182, 127, 0.18), rgba(200, 85, 61, 0.08)),
        repeating-linear-gradient(
          45deg,
          rgba(20, 40, 29, 0.03),
          rgba(20, 40, 29, 0.03) 10px,
          transparent 10px,
          transparent 20px
        );
    }
    .map-meta {
      padding: 12px;
      border-top: 1px solid var(--line);
    }
    .map-marker {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      border-radius: 999px;
      color: #fff;
      font-size: 10px;
      font-weight: 700;
      box-shadow: 0 6px 16px rgba(20, 40, 29, 0.22);
      border: 2px solid rgba(255,255,255,0.92);
    }
    .map-marker.target {
      background: #14281d;
    }
    .map-marker.competitor {
      background: #c8553d;
    }
    .controls label {
      min-width: 180px;
    }
    .checkbox {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      color: var(--muted);
    }
    .checkbox input {
      width: auto;
      margin: 0;
    }
    .row-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: var(--muted);
      margin-top: 4px;
    }
    .warn {
      color: #8f2d1a;
      font-weight: 600;
    }
    .safe {
      color: #1e6f5c;
      font-weight: 600;
    }
    @media (max-width: 960px) {
      .grid, .row, .dashboard-grid {
        grid-template-columns: 1fr;
      }
      .stats-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="eyebrow">Hotel Spider MVP</div>
      <h1>竞品价格控制台</h1>
      <p>这个页面直接挂在后端服务里，方便你先联调“酒店录入 -> 高德发现竞品 -> OTA 采价 -> 看板查看”这条链路。真实高德 MCP 配好之后，发现竞品接口会直接切到 MCP 返回值。</p>
      <div class="quicklinks">
        <a href="/docs" target="_blank" rel="noreferrer">Swagger Docs</a>
        <a href="/openapi.json" target="_blank" rel="noreferrer">OpenAPI JSON</a>
        <a href="/healthz" target="_blank" rel="noreferrer">Health Check</a>
      </div>
      <div class="toolbar">
        <span class="pill" id="provider-pill">AMap Provider: loading...</span>
        <span class="pill" id="key-pill">API Key: checking...</span>
        <span class="pill" id="map-key-pill">Map Key: checking...</span>
        <span class="pill" id="ctrip-pill">Ctrip Provider: loading...</span>
        <span class="pill" id="ctrip-state-pill">Ctrip State: checking...</span>
        <span class="pill" id="meituan-pill">Meituan Provider: loading...</span>
        <span class="pill" id="meituan-state-pill">Meituan State: checking...</span>
      </div>
    </section>

    <div class="dashboard-grid">
      <section class="panel">
        <h2>价格对比</h2>
        <p class="hint">这里会把目标酒店和竞品酒店放在一张表里，按各平台当前抓到的最低价进行对比。</p>
        <div class="status" id="comparison-summary">等待采价结果...</div>
        <div class="scroll-panel">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="metric">当前口径目标最低价</div>
              <strong id="stat-target-price">-</strong>
            </div>
            <div class="stat-card">
              <div class="metric">低于我方的竞品数</div>
              <strong id="stat-undercut-count">-</strong>
            </div>
            <div class="stat-card">
              <div class="metric">最低竞品价差</div>
              <strong id="stat-best-gap">-</strong>
            </div>
          </div>
          <div class="controls">
            <label>平台视图
              <select id="comparison-platform">
                <option value="all">全部平台</option>
                <option value="ctrip">仅携程</option>
                <option value="meituan">仅美团</option>
              </select>
            </label>
            <label>排序方式
              <select id="comparison-sort">
                <option value="gap_asc">价差从低到高</option>
                <option value="gap_desc">价差从高到低</option>
                <option value="price_asc">最低价从低到高</option>
                <option value="distance_asc">距离从近到远</option>
              </select>
            </label>
            <label class="checkbox">
              <input id="comparison-undercut-only" type="checkbox" />
              只看低于我方的竞品
            </label>
          </div>
          <table class="table">
            <thead>
              <tr>
                <th>角色</th>
                <th>酒店</th>
                <th>距离</th>
                <th>最低价</th>
                <th>携程价</th>
                <th>美团价</th>
                <th>最低价差</th>
                <th>房型</th>
              </tr>
            </thead>
            <tbody id="comparison-table-body"></tbody>
          </table>
          <div class="hint" style="margin-top: 14px;">低价竞品告警</div>
          <div class="status" id="alert-summary">暂无告警。</div>
          <div class="alert-list" id="alert-list"></div>
        </div>
      </section>

      <div class="side-stack">
        <section class="panel">
          <h2>地图视图</h2>
          <p class="hint">展示目标酒店和已发现竞品的地理位置。点击地图点位可以查看酒店名、距离和当前价格口径。</p>
          <div class="map-shell">
            <div id="hotel-map" class="map-canvas"></div>
            <div class="map-meta">
              <div class="status" id="map-status">等待酒店和竞品数据...</div>
            </div>
          </div>
        </section>

        <section class="panel">
          <h2>状态与结果</h2>
          <p class="hint">下面保留原始接口结果，方便排查数据和联调。</p>
          <div class="status" id="status-box">等待操作...</div>
          <div class="scroll-panel compact">
            <pre class="code" id="result-box">{}</pre>
          </div>
        </section>
      </div>
    </div>

    <div class="grid">
      <div class="stack">
        <section class="panel">
          <h2>新增酒店</h2>
          <p class="hint">录入目标酒店基础信息。经纬度为空时，发现竞品会尝试通过高德 MCP 用地址或名称定位。</p>
          <form id="hotel-form">
            <div class="row">
              <label>酒店名称
                <input name="name" value="上海静安香格里拉大酒店" required />
              </label>
              <label>城市
                <input name="city" value="上海" />
              </label>
            </div>
            <label>地址
              <input name="address" value="上海市静安区延安中路1218号" />
            </label>
            <div class="row">
              <label>品牌
                <input name="brand" placeholder="可选" />
              </label>
              <label>星级
                <input name="star_level" type="number" min="0" max="5" placeholder="可选" />
              </label>
            </div>
            <div class="row">
              <label>经度
                <input name="lng" type="number" step="0.000001" placeholder="可选" />
              </label>
              <label>纬度
                <input name="lat" type="number" step="0.000001" placeholder="可选" />
              </label>
            </div>
            <button type="submit">创建酒店</button>
          </form>
        </section>

        <section class="panel">
          <h2>高德发现参数</h2>
          <p class="hint">这个区域用于验证真实高德 MCP 链路。发现竞品后，页面会自动刷新目标酒店看板。</p>
          <form id="discover-form">
            <label>目标酒店
              <select id="discover-hotel-id" name="hotel_id"></select>
            </label>
            <div class="row">
              <label>搜索半径（米）
                <input name="radius_meters" type="number" min="100" max="10000" value="2000" />
              </label>
              <label>返回数量
                <input name="limit" type="number" min="1" max="50" value="10" />
              </label>
            </div>
            <button type="submit">发现竞品并刷新看板</button>
          </form>
        </section>

        <section class="panel">
          <h2>采价任务</h2>
          <p class="hint">选择一个目标酒店，按未来日期抓取竞品价格。当前默认会优先走真实携程 Playwright 登录态；美团仍可保留为 mock。</p>
          <form id="collect-form">
            <label>目标酒店
              <select id="target-hotel-id" name="target_hotel_id"></select>
            </label>
            <div class="row">
              <label>入住日期
                <input name="check_in_date" type="date" required />
              </label>
              <label>离店日期
                <input name="check_out_date" type="date" required />
              </label>
            </div>
            <div class="row">
              <label>成人数
                <input name="adults" type="number" min="1" max="8" value="2" />
              </label>
              <label>儿童数
                <input name="children" type="number" min="0" max="4" value="0" />
              </label>
            </div>
            <label>平台
              <select id="platforms" multiple size="2">
                <option value="ctrip" selected>ctrip</option>
                <option value="meituan">meituan</option>
              </select>
            </label>
            <button type="submit">执行采价并刷新看板</button>
          </form>
        </section>
      </div>

      <div class="stack">
        <section class="panel">
          <div class="toolbar">
            <div>
              <h2>酒店与竞品</h2>
              <p class="hint">选中一条酒店后，可以直接触发高德竞品发现和看板查询。</p>
            </div>
            <button class="secondary" id="refresh-hotels">刷新酒店列表</button>
          </div>
          <div class="scroll-panel compact">
            <table class="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>酒店</th>
                  <th>城市</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody id="hotel-table-body"></tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  </div>

  <script>
    const amapJsApiKey = __AMAP_JS_API_KEY__;
    const apiPrefix = "/api/v1";
    const state = {
      hotels: [],
      selectedHotelId: null,
      runtime: null,
      comparisonDashboard: null,
      map: null,
      mapMarkers: [],
      mapInfoWindow: null,
      amapLoader: null,
    };

    function setStatus(text) {
      document.getElementById("status-box").textContent = text;
    }

    function setResult(payload) {
      document.getElementById("result-box").textContent = JSON.stringify(payload, null, 2);
    }

    function setComparisonStats({ targetPrice = "-", undercutCount = "-", bestGap = "-" } = {}) {
      document.getElementById("stat-target-price").textContent = targetPrice;
      document.getElementById("stat-undercut-count").textContent = undercutCount;
      document.getElementById("stat-best-gap").textContent = bestGap;
    }

    function formatCurrency(value) {
      return value === null || value === undefined ? "-" : `CNY ${Number(value).toFixed(0)}`;
    }

    function formatGap(value) {
      if (value === null || value === undefined) return "-";
      if (value === 0) return "持平";
      return `${value > 0 ? "+" : ""}${Number(value).toFixed(0)}`;
    }

    function safeNumber(value, fallback = Number.POSITIVE_INFINITY) {
      return value === null || value === undefined ? fallback : Number(value);
    }

    function currentComparisonPlatform() {
      return document.getElementById("comparison-platform").value;
    }

    function setMapStatus(text) {
      document.getElementById("map-status").textContent = text;
    }

    function statusForPlatform(statuses, platform) {
      return (statuses || []).find((item) => item.platform === platform) || null;
    }

    function statusReasonText(status) {
      if (!status) return "未采价";
      return status.reason || status.attempt_status || "未采价";
    }

    function combinedReasonText(statuses) {
      if (!statuses || !statuses.length) return "未采价";
      return statuses.map((item) => `${item.platform}: ${statusReasonText(item)}`).join("；");
    }

    function comparisonRate(rates) {
      const platform = currentComparisonPlatform();
      return platform === "all" ? lowestRate(rates || []) : lowestRate(rates || [], platform);
    }

    function updateAlertPanel(alertRows, targetBest) {
      const summary = document.getElementById("alert-summary");
      const list = document.getElementById("alert-list");
      list.innerHTML = "";

      if (!targetBest) {
        summary.textContent = "目标酒店当前口径下还没有价格，无法生成低价竞品告警。";
        return;
      }

      if (!alertRows.length) {
        summary.textContent = "当前没有低于我方的竞品。";
        return;
      }

      summary.textContent =
        `发现 ${alertRows.length} 家低于我方的竞品，当前目标酒店基准价为 ${formatCurrency(targetBest.final_price)}。`;

      for (const row of alertRows) {
        const card = document.createElement("div");
        card.className = "alert-card";
        card.innerHTML = `
          <strong>${row.hotel_name}</strong>
          <div class="alert-meta">
            <span>价差 ${formatGap(row.gap)}</span>
            <span>最低价 ${formatCurrency(row.best?.final_price)}</span>
            <span>距离 ${row.distance_meters || "-"}m</span>
            <span>房型 ${row.best?.room_name || "-"}</span>
            <span>平台 ${row.best?.platform || "-"}</span>
          </div>
        `;
        list.appendChild(card);
      }
    }

    function loadAmapScript() {
      if (window.AMap) return Promise.resolve(window.AMap);
      if (state.amapLoader) return state.amapLoader;
      if (!amapJsApiKey) {
        return Promise.reject(new Error("AMAP_JS_API_KEY 未配置"));
      }

      state.amapLoader = new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(amapJsApiKey)}&plugin=AMap.Scale,AMap.ToolBar`;
        script.async = true;
        script.onload = () => resolve(window.AMap);
        script.onerror = () => reject(new Error("高德地图脚本加载失败"));
        document.head.appendChild(script);
      });
      return state.amapLoader;
    }

    async function ensureMap() {
      if (state.map) return state.map;
      const AMap = await loadAmapScript();
      state.map = new AMap.Map("hotel-map", {
        zoom: 13,
        resizeEnable: true,
        center: [121.4737, 31.2304],
      });
      state.map.addControl(new AMap.Scale());
      state.map.addControl(new AMap.ToolBar({ position: "RB" }));
      state.mapInfoWindow = new AMap.InfoWindow({ offset: new AMap.Pixel(0, -20) });
      return state.map;
    }

    function markerContent(type) {
      return `<div class="map-marker ${type}">${type === "target" ? "我" : "竞"}</div>`;
    }

    function pointSummaryText(point) {
      if (point.best) return `${point.best.platform} ${formatCurrency(point.best.final_price)}`;
      if (currentComparisonPlatform() === "all") return combinedReasonText(point.collection_statuses);
      return statusReasonText(statusForPlatform(point.collection_statuses, currentComparisonPlatform()));
    }

    function pointInfoHtml(point) {
      const distanceText = point.role === "目标" ? "本酒店" : `${point.distance_meters || "-"}m`;
      return `
        <div style="min-width:220px;line-height:1.5;">
          <strong>${point.hotel_name}</strong><br />
          <span>${point.role === "目标" ? "目标酒店" : "竞品酒店"}</span><br />
          <span>距离: ${distanceText}</span><br />
          <span>当前口径: ${pointSummaryText(point)}</span><br />
          <span>地址: ${point.address || "-"}</span>
        </div>
      `;
    }

    async function renderMapDashboard(dashboard) {
      if (!dashboard) {
        setMapStatus("等待酒店和竞品数据...");
        return;
      }

      if (!amapJsApiKey) {
        setMapStatus("未配置 AMAP_JS_API_KEY，地图窗口无法加载。");
        return;
      }

      const points = [
        {
          role: "目标",
          hotel_name: dashboard.target_hotel.name,
          address: dashboard.target_hotel.address,
          distance_meters: 0,
          lng: dashboard.target_hotel.lng,
          lat: dashboard.target_hotel.lat,
          latest_rates: dashboard.target_latest_rates || [],
          collection_statuses: dashboard.target_collection_statuses || [],
          best: comparisonRate(dashboard.target_latest_rates || []),
        },
        ...(dashboard.competitors || []).map((item) => ({
          role: "竞品",
          hotel_name: item.hotel_name,
          address: item.address,
          distance_meters: item.distance_meters,
          lng: item.lng,
          lat: item.lat,
          latest_rates: item.latest_rates || [],
          collection_statuses: item.collection_statuses || [],
          best: comparisonRate(item.latest_rates || []),
        })),
      ].filter((item) => item.lng !== null && item.lng !== undefined && item.lat !== null && item.lat !== undefined);

      if (!points.length) {
        setMapStatus("当前酒店和竞品没有可用坐标，无法渲染地图。");
        return;
      }

      try {
        const map = await ensureMap();
        if (state.mapMarkers.length) {
          map.remove(state.mapMarkers);
        }
        state.mapMarkers = points.map((point) => {
          const marker = new window.AMap.Marker({
            position: [Number(point.lng), Number(point.lat)],
            title: point.hotel_name,
            content: markerContent(point.role === "目标" ? "target" : "competitor"),
            offset: new window.AMap.Pixel(-9, -9),
          });
          marker.on("click", () => {
            state.mapInfoWindow.setContent(pointInfoHtml(point));
            state.mapInfoWindow.open(map, marker.getPosition());
          });
          return marker;
        });
        map.add(state.mapMarkers);
        map.setFitView(state.mapMarkers, false, [60, 60, 60, 60]);
        setMapStatus(`地图已加载 ${points.length} 个点位，包含目标酒店和竞品酒店。`);
      } catch (error) {
        setMapStatus(`地图加载失败: ${error.message}`);
      }
    }

    function setProviderStatus(runtime) {
      state.runtime = runtime;
      document.getElementById("provider-pill").textContent =
        `AMap Provider: ${runtime.amap_provider} via ${runtime.amap_mcp_command}`;
      document.getElementById("key-pill").textContent =
        runtime.amap_api_key_configured ? "API Key: configured" : "API Key: missing";
      document.getElementById("map-key-pill").textContent =
        runtime.amap_js_api_key_configured ? "Map Key: configured" : "Map Key: missing";
      document.getElementById("ctrip-pill").textContent =
        `Ctrip Provider: ${runtime.ctrip_provider} ${runtime.ctrip_headless ? "(headless)" : "(headed)"}`;
      document.getElementById("ctrip-state-pill").textContent =
        runtime.ctrip_storage_state_exists ? "Ctrip State: loaded" : "Ctrip State: missing";
      document.getElementById("meituan-pill").textContent =
        `Meituan Provider: ${runtime.meituan_provider} ${runtime.meituan_headless ? "(headless)" : "(headed)"}`;
      document.getElementById("meituan-state-pill").textContent =
        runtime.meituan_storage_state_exists ? "Meituan State: loaded" : "Meituan State: missing";
    }

    function collectSelectedPlatforms() {
      return Array.from(document.getElementById("platforms").selectedOptions).map((option) => option.value);
    }

    function normalizeFormData(form) {
      const data = new FormData(form);
      const payload = {};
      for (const [key, value] of data.entries()) {
        if (value === "") continue;
        payload[key] = value;
      }
      for (const field of ["lng", "lat"]) {
        if (payload[field] !== undefined) payload[field] = Number(payload[field]);
      }
      if (payload.star_level !== undefined) payload.star_level = Number(payload.star_level);
      if (payload.adults !== undefined) payload.adults = Number(payload.adults);
      if (payload.children !== undefined) payload.children = Number(payload.children);
      return payload;
    }

    async function request(path, options = {}) {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options,
      });
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      if (!response.ok) {
        throw new Error(data.detail || response.statusText || "request failed");
      }
      return data;
    }

    async function loadHotels() {
      setStatus("正在加载酒店列表...");
      const hotels = await request(`${apiPrefix}/hotels`);
      state.hotels = hotels;
      if (!state.selectedHotelId && hotels.length) {
        state.selectedHotelId = hotels[0].id;
      }
      renderHotels();
      renderHotelSelect();
      renderDiscoverSelect();
      setStatus(`已加载 ${hotels.length} 家酒店`);
    }

    function renderHotelSelect() {
      const select = document.getElementById("target-hotel-id");
      populateHotelSelect(select);
    }

    function renderDiscoverSelect() {
      const select = document.getElementById("discover-hotel-id");
      populateHotelSelect(select);
    }

    function populateHotelSelect(select) {
      select.innerHTML = "";
      for (const hotel of state.hotels) {
        const option = document.createElement("option");
        option.value = hotel.id;
        option.textContent = `${hotel.id} · ${hotel.name}`;
        option.selected = hotel.id === state.selectedHotelId;
        select.appendChild(option);
      }
    }

    function renderHotels() {
      const tbody = document.getElementById("hotel-table-body");
      tbody.innerHTML = "";
      for (const hotel of state.hotels) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${hotel.id}</td>
          <td>
            <strong>${hotel.name}</strong><br />
            <span class="pill">${hotel.address || "未填写地址"}</span>
          </td>
          <td>${hotel.city || "-"}</td>
          <td>
            <div class="toolbar">
              <button class="secondary" data-action="select" data-id="${hotel.id}">选中</button>
              <button class="secondary" data-action="discover" data-id="${hotel.id}">发现竞品</button>
              <button class="secondary" data-action="dashboard" data-id="${hotel.id}">查看看板</button>
            </div>
          </td>
        `;
        tbody.appendChild(tr);
      }
    }

    function selectedCheckInDate() {
      return document.querySelector('input[name="check_in_date"]').value || null;
    }

    function selectedCheckOutDate() {
      return document.querySelector('input[name="check_out_date"]').value || null;
    }

    function buildDashboardPath(hotelId) {
      const checkInDate = selectedCheckInDate();
      const checkOutDate = selectedCheckOutDate();
      const params = new URLSearchParams();
      if (checkInDate) params.set("check_in_date", checkInDate);
      if (checkOutDate) params.set("check_out_date", checkOutDate);
      const suffix = params.toString();
      return suffix ? `${apiPrefix}/hotels/${hotelId}/dashboard?${suffix}` : `${apiPrefix}/hotels/${hotelId}/dashboard`;
    }

    function lowestRate(rates, platform = null) {
      const filtered = platform ? rates.filter((item) => item.platform === platform) : rates;
      if (!filtered.length) return null;
      return filtered.reduce((best, current) => (
        current.final_price < best.final_price ? current : best
      ));
    }

    function renderComparisonDashboard(dashboard) {
      state.comparisonDashboard = dashboard;
      const tbody = document.getElementById("comparison-table-body");
      const summary = document.getElementById("comparison-summary");
      tbody.innerHTML = "";

      if (!dashboard) {
        summary.textContent = "等待采价结果...";
        setComparisonStats();
        return;
      }

      const rows = [
        {
          role: "目标",
          hotel_id: dashboard.target_hotel.id,
          hotel_name: dashboard.target_hotel.name,
          distance_meters: 0,
          latest_rates: dashboard.target_latest_rates || [],
          collection_statuses: dashboard.target_collection_statuses || [],
        },
        ...(dashboard.competitors || []).map((item) => ({
          role: "竞品",
          ...item,
        })),
      ];

      const targetBest = comparisonRate(dashboard.target_latest_rates || []);
      const pricedRows = rows.filter((item) => item.latest_rates && item.latest_rates.length > 0);
      const sortBy = document.getElementById("comparison-sort").value;
      const undercutOnly = document.getElementById("comparison-undercut-only").checked;
      const platformLabel = currentComparisonPlatform() === "all" ? "全部平台" : currentComparisonPlatform();

      if (!rows.length) {
        summary.textContent = "当前没有可对比的酒店。";
        setComparisonStats();
        updateAlertPanel([], null);
        return;
      }

      const targetRow = rows[0];
      let competitorRows = rows.slice(1).map((row) => {
        const best = comparisonRate(row.latest_rates || []);
        const ctrip = lowestRate(row.latest_rates || [], "ctrip");
        const meituan = lowestRate(row.latest_rates || [], "meituan");
        const gap = best && targetBest ? best.final_price - targetBest.final_price : null;
        return {
          ...row,
          best,
          ctrip,
          meituan,
          gap,
          ctripStatus: statusForPlatform(row.collection_statuses, "ctrip"),
          meituanStatus: statusForPlatform(row.collection_statuses, "meituan"),
        };
      });

      if (undercutOnly) {
        competitorRows = competitorRows.filter((row) => row.gap !== null && row.gap < 0);
      }

      competitorRows.sort((left, right) => {
        if (sortBy === "gap_desc") return safeNumber(right.gap) - safeNumber(left.gap);
        if (sortBy === "price_asc") return safeNumber(left.best?.final_price) - safeNumber(right.best?.final_price);
        if (sortBy === "distance_asc") return safeNumber(left.distance_meters) - safeNumber(right.distance_meters);
        return safeNumber(left.gap) - safeNumber(right.gap);
      });

      const visibleRows = [
        {
          ...targetRow,
          best: targetBest,
          ctrip: lowestRate(targetRow.latest_rates || [], "ctrip"),
          meituan: lowestRate(targetRow.latest_rates || [], "meituan"),
          gap: 0,
          ctripStatus: statusForPlatform(targetRow.collection_statuses, "ctrip"),
          meituanStatus: statusForPlatform(targetRow.collection_statuses, "meituan"),
        },
        ...competitorRows,
      ];

      for (const row of visibleRows) {
        const tr = document.createElement("tr");
        if (row.role === "目标") {
          tr.className = "target-row";
        } else if (row.gap !== null && row.gap < 0) {
          tr.className = "risk-row";
        }
        tr.innerHTML = `
          <td><span class="pill">${row.role}</span></td>
          <td>
            <strong>${row.hotel_name}</strong><br />
            <span class="metric">已抓取 ${row.latest_rates?.length || 0} 条快照</span><br />
            <span class="row-tag ${row.role === "目标" ? "" : row.gap !== null && row.gap < 0 ? "warn" : "safe"}">
              ${row.role === "目标" ? "对比基准" : row.gap !== null && row.gap < 0 ? "竞品低于我方" : "竞品不低于我方"}
            </span>
          </td>
          <td>${row.role === "目标" ? "本酒店" : `${row.distance_meters || "-"}m`}</td>
          <td>
            <span class="price">${formatCurrency(row.best?.final_price)}</span><br />
            <span class="metric">${row.best ? row.best.platform : currentComparisonPlatform() === "all" ? combinedReasonText(row.collection_statuses) : statusReasonText(statusForPlatform(row.collection_statuses, currentComparisonPlatform()))}</span>
          </td>
          <td>${row.ctrip ? formatCurrency(row.ctrip.final_price) : `<span class="metric">${statusReasonText(row.ctripStatus)}</span>`}</td>
          <td>${row.meituan ? formatCurrency(row.meituan.final_price) : `<span class="metric">${statusReasonText(row.meituanStatus)}</span>`}</td>
          <td class="${row.gap !== null && row.gap < 0 ? "negative" : "positive"}">${row.role === "目标" ? "基准" : formatGap(row.gap)}</td>
          <td>${row.best ? row.best.room_name : "-"}</td>
        `;
        tbody.appendChild(tr);
      }

      if (!pricedRows.length) {
        summary.textContent = "当前还没有采价数据，请先执行一次采价任务。";
        setComparisonStats();
        updateAlertPanel([], null);
        return;
      }

      if (!targetBest) {
        summary.textContent = `已加载 ${rows.length} 家酒店，但目标酒店在 ${platformLabel} 口径下还没有价格数据，暂时无法计算价差。`;
        setComparisonStats({
          targetPrice: "-",
          undercutCount: "-",
          bestGap: "-",
        });
        updateAlertPanel([], null);
        return;
      }

      const allCompetitorRows = rows.slice(1).map((item) => {
        const best = comparisonRate(item.latest_rates || []);
        return {
          ...item,
          best,
          gap: best ? best.final_price - targetBest.final_price : null,
        };
      });
      const lowerCompetitors = allCompetitorRows.filter((item) => item.gap !== null && item.gap < 0).length;
      const bestGap = allCompetitorRows
        .filter((item) => item.gap !== null)
        .reduce((value, item) => Math.min(value, item.gap), Number.POSITIVE_INFINITY);

      setComparisonStats({
        targetPrice: formatCurrency(targetBest.final_price),
        undercutCount: String(lowerCompetitors),
        bestGap: Number.isFinite(bestGap) ? formatGap(bestGap) : "-",
      });
      updateAlertPanel(
        allCompetitorRows
          .filter((item) => item.gap !== null && item.gap < 0)
          .sort((left, right) => safeNumber(left.gap) - safeNumber(right.gap)),
        targetBest,
      );

      summary.textContent =
        `当前按 ${platformLabel} 口径对比，目标酒店最低价 ${formatCurrency(targetBest.final_price)}，共纳入 ${rows.length} 家酒店，` +
        `${pricedRows.length} 家已有价格，其中 ${lowerCompetitors} 家竞品低于目标酒店。` +
        `${undercutOnly ? " 当前已过滤为仅展示低价竞品。" : ""}`;
    }

    async function createHotel(event) {
      event.preventDefault();
      const payload = normalizeFormData(event.target);
      setStatus("正在创建酒店...");
      const result = await request(`${apiPrefix}/hotels`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      state.selectedHotelId = result.id;
      await loadHotels();
      setResult(result);
      setStatus(`酒店已创建，ID=${result.id}`);
    }

    async function discoverCompetitors(hotelId) {
      state.selectedHotelId = hotelId;
      renderHotelSelect();
      renderDiscoverSelect();
      const form = document.getElementById("discover-form");
      const payload = normalizeFormData(form);
      setStatus(`正在通过 ${state.runtime?.amap_provider || "unknown"} 为酒店 ${hotelId} 发现竞品...`);
      const result = await request(`${apiPrefix}/hotels/${hotelId}/discover-competitors`, {
        method: "POST",
        body: JSON.stringify({
          radius_meters: Number(payload.radius_meters || 2000),
          limit: Number(payload.limit || 10),
        }),
      });
      await loadHotels();
      const dashboard = await request(buildDashboardPath(hotelId));
      renderComparisonDashboard(dashboard);
      renderMapDashboard(dashboard);
      setResult({ discovery: result, dashboard });
      setStatus(`竞品发现完成，共返回 ${result.total} 家，已同步刷新看板`);
    }

    async function loadDashboard(hotelId) {
      state.selectedHotelId = hotelId;
      renderHotelSelect();
      setStatus(`正在加载酒店 ${hotelId} 的看板...`);
      const result = await request(buildDashboardPath(hotelId));
      renderComparisonDashboard(result);
      renderMapDashboard(result);
      setResult(result);
      setStatus(`看板已更新，竞品数 ${result.competitors.length}`);
    }

    async function collectRates(event) {
      event.preventDefault();
      const payload = normalizeFormData(event.target);
      payload.platforms = collectSelectedPlatforms();
      payload.target_hotel_id = Number(payload.target_hotel_id);
      setStatus(`正在执行酒店 ${payload.target_hotel_id} 的采价任务，平台=${payload.platforms.join(", ")}...`);
      const result = await request(`${apiPrefix}/rates/collect`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const dashboard = await request(buildDashboardPath(payload.target_hotel_id));
      const summary = summarizeSnapshots(result.snapshots);
      renderComparisonDashboard(dashboard);
      renderMapDashboard(dashboard);
      setResult({ collection: result, summary, dashboard });
      setStatus(`采价完成，共写入 ${result.total_snapshots} 条快照，已刷新看板`);
    }

    function summarizeSnapshots(snapshots) {
      const byPlatform = {};
      for (const item of snapshots) {
        const platform = item.platform;
        byPlatform[platform] ??= { count: 0, min_price: null, max_price: null };
        byPlatform[platform].count += 1;
        byPlatform[platform].min_price = byPlatform[platform].min_price === null
          ? item.final_price
          : Math.min(byPlatform[platform].min_price, item.final_price);
        byPlatform[platform].max_price = byPlatform[platform].max_price === null
          ? item.final_price
          : Math.max(byPlatform[platform].max_price, item.final_price);
      }
      return byPlatform;
    }

    document.getElementById("hotel-form").addEventListener("submit", (event) => {
      createHotel(event).catch((error) => setStatus(`创建失败: ${error.message}`));
    });

    document.getElementById("collect-form").addEventListener("submit", (event) => {
      collectRates(event).catch((error) => setStatus(`采价失败: ${error.message}`));
    });

    document.getElementById("discover-form").addEventListener("submit", (event) => {
      event.preventDefault();
      const hotelId = Number(new FormData(event.target).get("hotel_id"));
      discoverCompetitors(hotelId).catch((error) => setStatus(`发现竞品失败: ${error.message}`));
    });

    document.getElementById("refresh-hotels").addEventListener("click", () => {
      loadHotels().catch((error) => setStatus(`加载失败: ${error.message}`));
    });

    document.getElementById("comparison-sort").addEventListener("change", () => {
      renderComparisonDashboard(state.comparisonDashboard);
      renderMapDashboard(state.comparisonDashboard);
    });

    document.getElementById("comparison-undercut-only").addEventListener("change", () => {
      renderComparisonDashboard(state.comparisonDashboard);
      renderMapDashboard(state.comparisonDashboard);
    });

    document.getElementById("comparison-platform").addEventListener("change", () => {
      renderComparisonDashboard(state.comparisonDashboard);
      renderMapDashboard(state.comparisonDashboard);
    });

    document.getElementById("hotel-table-body").addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      const hotelId = Number(button.dataset.id);
      const action = button.dataset.action;
      if (action === "select") {
        state.selectedHotelId = hotelId;
        renderHotelSelect();
        renderDiscoverSelect();
        setStatus(`已选中酒店 ${hotelId}`);
      } else if (action === "discover") {
        discoverCompetitors(hotelId).catch((error) => setStatus(`发现竞品失败: ${error.message}`));
      } else if (action === "dashboard") {
        loadDashboard(hotelId).catch((error) => setStatus(`看板加载失败: ${error.message}`));
      }
    });

    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);
    document.querySelector('input[name="check_in_date"]').value = today.toISOString().slice(0, 10);
    document.querySelector('input[name="check_out_date"]').value = tomorrow.toISOString().slice(0, 10);

    request(`${apiPrefix}/system/runtime`)
      .then(setProviderStatus)
      .then(loadHotels)
      .catch((error) => setStatus(`初始化失败: ${error.message}`));
  </script>
</body>
</html>""".replace("__AMAP_JS_API_KEY__", json.dumps(amap_js_api_key))


@router.get("/", response_class=RedirectResponse)
def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/admin", status_code=302)


@router.get("/admin", response_class=HTMLResponse)
def admin_page() -> HTMLResponse:
    return HTMLResponse(render_admin_html())
