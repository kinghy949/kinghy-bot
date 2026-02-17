# Repository Guidelines

## 模型回复规则
- 模型在本仓库中的每次回复都必须使用中文。

## 项目结构与模块组织
本仓库采用前后端分离：Flask 后端 + Vue 3 前端。
- `server/`：后端 API、编排器、生成器、任务管理与运行产物。
  - `server/api/`：REST 接口（`/generate`、`/task`、`/download`）。
  - `server/generators/`：功能/代码/HTML/截图/文档生成流水线。
  - `server/ai/`：AI 客户端、模型适配器、提示词辅助。
  - `server/task/`：异步任务管理与任务状态持久化。
  - `server/tech_stacks/`：技术栈 YAML 配置。
- `client/`：Vue + Vite 单页应用（`src/views`、`src/components`、`src/stores`、`src/api`）。
- `docs/`：设计与进度文档。
- `template/`：参考模板文档。

## 构建、测试与开发命令
后端：
- `cd server && pip install -r requirements.txt`：安装 Python 依赖。
- `cd server && playwright install chromium`：安装截图浏览器。
- `cd server && python app.py`：启动 Flask（默认 `:5000`）。

前端：
- `cd client && npm install`：安装 Node 依赖。
- `cd client && npm run dev`：启动 Vite（默认 `:5173`，代理后端）。
- `cd client && npm run build`：构建生产包。

## 代码风格与命名约定
- Python：4 空格缩进；函数/变量用 `snake_case`；类名用 `PascalCase`。
- Vue/JS：2 空格缩进；组件文件使用 `PascalCase`（如 `ProjectForm.vue`）；store/API 文件名用小写。
- 保持模块单一职责，明确异常处理，并提供可观测的降级逻辑。
- 统一 UTF-8 编码，严禁硬编码密钥。

## 测试规范
- 当前自动化测试较少，新功能需补充测试。
- 后端测试放在 `server/tests/`，命名建议 `test_<module>.py`。
- 前端测试引入后建议放在 `client/src/**/__tests__/`。
- 涉及流水线改动时，至少验证一次端到端流程（任务创建 -> 完成 -> 文件可下载）。

## 提交与合并请求规范
当前历史提交以简短中文摘要为主（如 `项目搭建`、`mvp闭环`）。建议保持：简短、明确、聚焦。
- Commit：单行描述，说明改动意图与范围。
- PR 至少包含：
  - 改动内容与原因；
  - 影响路径（如 `server/generators/orchestrator.py`）；
  - 手工验证步骤；
  - 涉及前端时附关键截图（如 `client/src/views/*`）。

## 安全与配置建议
- 基于 `server/.env.example` 创建本地 `.env`，不要提交真实 API Key。
- 部署前确认 `OUTPUT_DIR`、`SCREENSHOT_DIR`、任务保留策略等配置。
- `server/output/` 与 `server/screenshots/` 属于运行时产物，不作为源码管理对象。
