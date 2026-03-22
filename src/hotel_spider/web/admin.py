from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(include_in_schema=False)


def render_admin_html() -> str:
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
    @media (max-width: 960px) {
      .grid, .row {
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
    </section>

    <div class="grid">
      <div class="stack">
        <section class="panel">
          <h2>新增酒店</h2>
          <p class="hint">录入目标酒店基础信息。经纬度为空时，发现竞品会尝试通过高德 MCP 用地址或名称定位。</p>
          <form id="hotel-form">
            <div class="row">
              <label>酒店名称
                <input name="name" value="上海静安示例酒店" required />
              </label>
              <label>城市
                <input name="city" value="上海" />
              </label>
            </div>
            <label>地址
              <input name="address" value="静安区示例路 88 号" />
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
          <h2>采价任务</h2>
          <p class="hint">选择一个目标酒店，按未来日期抓取竞品价格。当前 OTA 仍是 mock adapter，高德发现可以切真实 MCP。</p>
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
                <option value="meituan" selected>meituan</option>
              </select>
            </label>
            <button type="submit">执行采价</button>
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
        </section>

        <section class="panel">
          <h2>状态与结果</h2>
          <p class="hint">下面会显示最近一次操作结果和目标酒店看板。</p>
          <div class="status" id="status-box">等待操作...</div>
          <pre class="code" id="result-box">{}</pre>
        </section>
      </div>
    </div>
  </div>

  <script>
    const apiPrefix = "/api/v1";
    const state = { hotels: [], selectedHotelId: null };

    function setStatus(text) {
      document.getElementById("status-box").textContent = text;
    }

    function setResult(payload) {
      document.getElementById("result-box").textContent = JSON.stringify(payload, null, 2);
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
      setStatus(`已加载 ${hotels.length} 家酒店`);
    }

    function renderHotelSelect() {
      const select = document.getElementById("target-hotel-id");
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
      setStatus(`正在为酒店 ${hotelId} 发现竞品...`);
      const result = await request(`${apiPrefix}/hotels/${hotelId}/discover-competitors`, {
        method: "POST",
        body: JSON.stringify({ radius_meters: 3000, limit: 10 }),
      });
      setResult(result);
      setStatus(`竞品发现完成，共返回 ${result.total} 家`);
    }

    async function loadDashboard(hotelId) {
      state.selectedHotelId = hotelId;
      renderHotelSelect();
      setStatus(`正在加载酒店 ${hotelId} 的看板...`);
      const result = await request(`${apiPrefix}/hotels/${hotelId}/dashboard`);
      setResult(result);
      setStatus(`看板已更新，竞品数 ${result.competitors.length}`);
    }

    async function collectRates(event) {
      event.preventDefault();
      const payload = normalizeFormData(event.target);
      payload.platforms = collectSelectedPlatforms();
      payload.target_hotel_id = Number(payload.target_hotel_id);
      setStatus(`正在执行酒店 ${payload.target_hotel_id} 的采价任务...`);
      const result = await request(`${apiPrefix}/rates/collect`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setResult(result);
      setStatus(`采价完成，共写入 ${result.total_snapshots} 条快照`);
    }

    document.getElementById("hotel-form").addEventListener("submit", (event) => {
      createHotel(event).catch((error) => setStatus(`创建失败: ${error.message}`));
    });

    document.getElementById("collect-form").addEventListener("submit", (event) => {
      collectRates(event).catch((error) => setStatus(`采价失败: ${error.message}`));
    });

    document.getElementById("refresh-hotels").addEventListener("click", () => {
      loadHotels().catch((error) => setStatus(`加载失败: ${error.message}`));
    });

    document.getElementById("hotel-table-body").addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      const hotelId = Number(button.dataset.id);
      const action = button.dataset.action;
      if (action === "select") {
        state.selectedHotelId = hotelId;
        renderHotelSelect();
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

    loadHotels().catch((error) => setStatus(`初始化失败: ${error.message}`));
  </script>
</body>
</html>"""


@router.get("/", response_class=RedirectResponse)
def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/admin", status_code=302)


@router.get("/admin", response_class=HTMLResponse)
def admin_page() -> HTMLResponse:
    return HTMLResponse(render_admin_html())
