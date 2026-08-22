## 变更说明
<!-- 简述本次 PR 改了什么、为什么 -->

## 关联 Issue
<!-- 例如 Closes #12 -->

## 检查清单
- [ ] `python tests/test_model.py` 本地通过
- [ ] `python rent_vs_buy_model.py --basis net` 与 `--basis gross` 正常输出
- [ ] 若改了公式 / 默认参数，已同步更新 README §3 / §4 / §7 与 `examples/default_scenario.md`
- [ ] 新增参数已在 `Params` 与 CLI 暴露（自动出现在 `--help`）
- [ ] 文档中的 `g*` 敏感性方向已核对（投资回报↑ → g*↑；租金涨幅↑ → g*↓）
