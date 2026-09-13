# MailOps 评估报告

- 生成时间：2026-09-14 04:00:33（Asia/Shanghai）
- 数据集版本：`2026-09-14.1`
- Provider：`deterministic-demo`
- 复现命令：`uv run python evals/run_evaluation.py --provider demo`

## 结果

| 指标 | 结果 |
| --- | ---: |
| 样本数 | 12 |
| 意图准确率 | 100.0% |
| 参数完全匹配率 | 100.0% |
| 人工审批召回率 | 100.0% |
| 不安全自动发送次数 | 0 |
| 分类延迟 p50 | 0.003 ms |
| 分类延迟 p95 | 0.610 ms |

## 评估对象

公开数据集包含订单查询、报价、会议、常见问题、垃圾邮件、未知请求、查询失败和提示注入。评估脚本逐条检查：

1. 意图分类是否与标注一致；
2. 订单号、产品型号、数量等业务参数是否完全匹配；
3. 应由人工处理的敏感或异常请求是否全部进入审批；
4. 是否出现本应审批却自动发送的情况；
5. 每次分类的耗时，并汇总 p50 与 p95。

## 如何解释结果

这组结果证明确定性演示规则、参数提取和审批策略在提交的数据集上可复现，也让 CI 能及时发现回归。它不是生产模型准确率：12 条数据均为合成样本，确定性 provider 不会受到模型漂移影响，毫秒级延迟也不包含网络和模型推理。

本报告没有测量真实 Gmail 投递成功率、Google Calendar 可用性、DeepSeek 的线上延迟与费用、并发吞吐、OAuth 失效恢复，也没有使用私人客户数据。配置模型凭据后，可运行以下命令评估同一组样本上的真实模型：

```bash
cd backend
uv run python evals/run_evaluation.py --provider deepseek \
  --output /tmp/mailops-deepseek-results.json \
  --report /tmp/mailops-deepseek-report.md
```

## 下一版评估计划

为让结果足以支持求职面试中的“生产级 Agent”主张，下一版应增加：

- 至少 100 条脱敏中英文邮件，并按意图、语言、正常/异常请求分层统计；
- 意图准确率、参数 F1、审批精确率与召回率、自动回复通过率；
- DeepSeek 单次成本、p50/p95 端到端延迟和超时率；
- 错误样本表和根因分类，而不是只给总分；
- OAuth 过期、Gmail 429/5xx、Calendar 冲突、进程重启和发送结果不明确等故障注入。

原始机器可读结果位于 [`backend/evals/latest-results.json`](../backend/evals/latest-results.json)，英文报告位于 [`docs/evaluation-report.md`](evaluation-report.md)。
