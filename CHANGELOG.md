# 更新日志 (Changelog)

本仓库遵循 [Keep a Changelog](https://keepachangelog.com/) 约定，版本号遵循 [语义化版本 SemVer](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-08-22

首个正式发行版。基于微信文章《租房30年和贷款30年买房，哪个更划算》提炼的「租房 vs 买房」参数化财务权衡分析框架——把"租房 X 年"与"贷款 X 年买房"两套现金流逐月模拟、月度复利，输出盈亏平衡门槛 `g*`、核心标尺与敏感性分析，辅助决策而不给结论。

### 新增 (Added)
- **Python 引擎** `rent_vs_buy_model.py`：纯标准库实现，`dataclass` 参数 + `simulate` / `break_even` / `report`，支持 CLI（`--basis net|gross`、`--config`、逐参数覆盖）与 `import` 为库。
- **交互页面** `index.html`：零安装，改任意参数实时出结果（胜负判定、情景表、敏感性柱状图、租金回报率标尺红绿灯、实际购买力）。
- **双口径一致**：同组输入同时驱动判定与盈亏平衡门槛 `g*`，「净收益」（扣购置/持有/房产税/卖房/投资税）与「毛资产」可一键切换，口径不自相矛盾。
- **6 项成本建模**：一次性购置成本、随通胀增长的持有成本、房产税、卖房成本、投资所得税、租金涨幅。
- **文档** `README.md`：假设、参数表、数学模型公式、指标判读、Python/HTML 用法、局限与扩展点；含 `g*` 敏感性速查表与 Mermaid 数据流图（GitHub 原生渲染）。
- **CI** `.github/workflows/ci.yml`：GitHub Actions，Python 3.11 / 3.12 / 3.13 矩阵，运行模型 CLI 与测试套件 `tests/test_model.py`（6 项回归）。
- **社区模板**：Issues（`bug_report.yml` / `feature_request.yml`）与 `PULL_REQUEST_TEMPLATE.md`。
- **预览截图** `assets/preview.png`：playwright chromium 真实渲染（2x DPR 全页），嵌入 README；附 `scripts/shot.js` 可复用截图脚本。
- **Topics 标签**：`finance` / `python` / `decision-model`。
- **示例** `examples/default_scenario.md`：默认场景完整输出（净/毛双口径）。
- **MIT License** `LICENSE` 与 `.gitignore`（Python 忽略项）。

### 默认场景参数
苏州 600 万、首付 30%、30 年、利率 3%、投资年化 5%、租金年涨幅 0%。

**关键结论（由引擎实测）**
- 月供 **1.7707 万/月**，贷款 420 万。
- 房价年化涨幅需超过 **约 3.20%（净）/ 3.29%（毛）**，买房才不输给租房定投。
- 租金回报率 1.67% < 房贷利率 3% → 红灯：持有现金流为负，房价不涨即"赔钱货"。
- 默认参数下租房（定投）净胜约 **83.7 万**。

---

[1.0.0]: https://github.com/ZoranAop/rent-vs-buy-framework/releases/tag/v1.0.0
