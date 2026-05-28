# Architecture

ReguThink 的展示架构分为前端交互层、FastAPI 后端层、多智能体编排层、Hybrid RAG/知识图谱设计层、报告生成层和评价体系层。

## Frontend

前端位于 `services/frontend_api_v2`，使用 React、TypeScript 和 Vite。它承担材料上传、对话式审查、智能体状态展示、知识图谱视图、报告中心和人工复核入口。

公开展示版默认使用相对 `/api/v1` 请求路径。本地开发时由 Vite proxy 转发到后端服务。

## Backend

后端位于 `services/backend_api_v2`，使用 FastAPI 暴露 REST API。展示版保留接口壳、会话/任务管理原型、文件上传入口、报告和图谱相关 API 形态。

公开仓库不包含真实数据库、私有法规知识库、向量索引、图数据库数据或真实上传材料。

## Multi-Agent Workflow

多智能体流程把合规审查拆成可解释步骤：

1. 业务事实解析
2. 处理活动识别
3. 法律依据检索
4. 风险识别
5. 证据与引用整理
6. 报告生成
7. 人工复核 Gate

## Hybrid RAG And Knowledge Graph

Hybrid RAG 设计结合关键词检索、语义检索和图谱关系。知识图谱用于展示法规主题、处理活动、风险类型、证据片段和报告结论之间的关系。公开仓库只保留设计说明和脱敏示例。

## Report And Evaluation

报告生成阶段输出结构化章节，并把结论绑定到证据或人工复核提示。评价体系关注依据覆盖、证据一致性、引用准确性、风险识别、边界控制和可读性。
