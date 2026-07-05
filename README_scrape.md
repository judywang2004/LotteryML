说明

这个脚本用于在本地使用 Playwright 抓取宾夕法尼亚彩票网站的“Winning Numbers History”页面并提取 Powerball 在 2025 和 2026 年的每期开奖数据。

准备与运行

1. 创建并激活虚拟环境（可选但推荐）

```bash
python3 -m venv venv
source venv/bin/activate
```

2. 安装依赖并安装浏览器二进制

```bash
pip install -r requirements.txt
python -m playwright install
```

3. 运行脚本

```bash
python scrape_palottery_powerball.py
```

输出

- `powerball_2025_2026.csv` 包含字段 `date, white_balls, power_ball, raw_row_text`
- `powerball_2025_2026.json` 包含结构化 JSON 数组

注意

- 该网站使用广告/跟踪跳转和部分动态加载，脚本使用浏览器自动化来呈现页面并抓取表格数据；在极少数情况下可能需要手动在无头浏览器窗口中观察并微调选择器。
- 如果需要，我可以根据抓取到的实际页面 DOM 调整脚本以更可靠地解析列。