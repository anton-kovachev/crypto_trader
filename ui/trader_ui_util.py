from enum import Enum

css = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    color-scheme: dark;
    --dashboard-bg: #0b0912;
    --surface: rgba(22, 18, 34, 0.88);
    --surface-raised: #1c172a;
    --border: rgba(183, 148, 255, 0.17);
    --border-bright: rgba(183, 148, 255, 0.32);
    --text-primary: #f4efff;
    --text-muted: #a79bbd;
    --purple: #c4a5ff;
    --purple-bright: #a878ff;
    --green: #58e6b1;
    --red: #ff7797;
}

html,
body {
    min-height: 100%;
    background: var(--dashboard-bg) !important;
}

body {
    color: var(--text-primary);
    font-family: 'DM Sans', sans-serif !important;
    background-image:
        radial-gradient(ellipse at 12% 0%, rgba(111, 57, 183, 0.2), transparent 38%),
        radial-gradient(ellipse at 92% 16%, rgba(72, 46, 132, 0.17), transparent 34%),
        linear-gradient(145deg, #0b0912 0%, #100d1b 48%, #0d0b15 100%) !important;
    background-attachment: fixed;
}

.gradio-container {
    max-width: 1800px !important;
    color: var(--text-primary) !important;
    background: transparent !important;
    font-family: 'DM Sans', sans-serif !important;
}

.dashboard {
    gap: 22px !important;
    padding: 26px clamp(14px, 3vw, 42px) 40px !important;
}

.trader-card {
    min-width: 0;
    padding: clamp(16px, 2vw, 26px) !important;
    border: 1px solid var(--border) !important;
    border-radius: 22px !important;
    background:
        linear-gradient(145deg, rgba(35, 27, 53, 0.82), rgba(18, 15, 28, 0.94)) !important;
    box-shadow:
        0 22px 60px rgba(0, 0, 0, 0.27),
        inset 0 1px 0 rgba(255, 255, 255, 0.035) !important;
    backdrop-filter: blur(16px);
}

.dashboard-title {
    padding: 2px 0 16px;
    color: var(--text-primary);
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(23px, 2.3vw, 32px);
    font-weight: 700;
    letter-spacing: -0.045em;
    text-align: center;
}

.dashboard-title span {
    color: var(--purple) !important;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.62em !important;
    font-weight: 500;
    letter-spacing: 0;
}

.portfolio-value {
    display: flex;
    align-items: baseline;
    justify-content: center;
    flex-wrap: wrap;
    gap: 6px 18px;
    padding: 17px 20px;
    border: 1px solid var(--border);
    border-radius: 16px;
    background: linear-gradient(110deg, rgba(133, 80, 217, 0.17), rgba(72, 48, 111, 0.08));
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
    text-align: center;
}

.portfolio-total {
    color: var(--text-primary);
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(28px, 3vw, 38px);
    font-weight: 700;
    letter-spacing: -0.04em;
}

.portfolio-pnl {
    color: var(--green);
    font-size: 17px;
    font-weight: 700;
}

.portfolio-pnl.negative {
    color: var(--red);
}

.trader-card .block,
.trader-card .panel,
.trader-card .form {
    border-color: var(--border) !important;
}

.trader-card .plot-container,
.trader-card .wrap:has(> .plot-container) {
    overflow: hidden;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    background: rgba(13, 11, 21, 0.68) !important;
}

.trader-card label,
.trader-card .prose,
.trader-card .wrap > span {
    color: var(--purple) !important;
    font-weight: 600;
}

.dataframe-fix-small .table-wrap {
    min-height: 150px;
    max-height: 220px;
}

.dataframe-fix .table-wrap {
    min-height: 200px;
    max-height: 300px;
}

.dataframe-fix-small .table-wrap,
.dataframe-fix .table-wrap {
    overflow: auto;
    border: 1px solid var(--border-bright) !important;
    border-radius: 13px !important;
    background: rgba(12, 10, 19, 0.58) !important;
    scrollbar-color: #684b91 #171321;
}

.dataframe-fix-small table,
.dataframe-fix table {
    border-collapse: separate !important;
    border-spacing: 0 !important;
    color: var(--text-primary) !important;
}

.dataframe-fix-small thead,
.dataframe-fix thead {
    background: linear-gradient(90deg, rgba(111, 72, 162, 0.32), rgba(65, 48, 96, 0.24)) !important;
    color: #d9c6ff !important;
}

.dataframe-fix-small th,
.dataframe-fix th {
    border-color: var(--border) !important;
    font-weight: 700 !important;
}

.dataframe-fix-small td,
.dataframe-fix td {
    border-color: rgba(183, 148, 255, 0.1) !important;
    background: transparent !important;
}

.dataframe-fix-small tbody tr:hover td,
.dataframe-fix tbody tr:hover td {
    background: rgba(156, 112, 224, 0.1) !important;
}

.activity-log {
    overflow: hidden;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    background: rgba(10, 9, 17, 0.68) !important;
    color: var(--text-muted);
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    line-height: 1.75;
}

button,
input,
textarea,
select {
    border-color: var(--border-bright) !important;
}

button.primary {
    border: 1px solid rgba(195, 160, 255, 0.4) !important;
    background: linear-gradient(110deg, #7543b5, #9a5de0) !important;
}

footer {
    display: none !important;
}

@media (max-width: 640px) {
    .dashboard {
        gap: 14px !important;
        padding: 14px 10px 24px !important;
    }

    .trader-card {
        padding: 15px !important;
        border-radius: 17px !important;
    }
}
"""


js = """
function refresh() {
    const url = new URL(window.location);

    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""


class Color(Enum):
    RED = "#dd0000"
    GREEN = "#00dd00"
    YELLOW = "#dddd00"
    BLUE = "#0000ee"
    MAGENTA = "#aa00dd"
    CYAN = "#00dddd"
    WHITE = "#87CEEB"
