# ReguThink API Contract v1

## 全局展示边界

所有面向前端的页面必须长期显示：

```json
{
  "not_production_ready": true,
  "not_source_backed_pass": true,
  "not_human_reviewed": true,
  "prototype_context": true,
  "local_neural_reranker_status": "diagnostic_only",
  "bge_m3_status": "partially_effective"
}
```

## 前端不得只显示 final_score

每个 case 至少展示：

```text
final_score
programmatic_score
llm_score
grade
main_issue
source_trace status
evidence gap / missing materials
not production-ready badge
not source-backed badge
not human-reviewed badge
```

## 不允许的前端行为

- 把 diagnostic report 显示成正式法律意见；
- 隐藏低分 case；
- 隐藏 CAP / evidence gap / source trace caveat；
- 把 local neural reranker 显示为正式启用；
- 用 Markdown 正文反向解析 evidence/citation/score 数据。

## 推荐页面

1. `/baseline`：系统基线、模型状态、不可变边界。
2. `/cases`：18-case score matrix。
3. `/cases/:caseId`：报告 + evidence + citation + source trace + score breakdown。
4. `/runtime`：单 case dry-run / future controlled runtime。
