# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言要求

**重要：在此仓库中工作时，必须使用中文回复所有消息和说明。**

## 项目概述

软著材料自动生成系统 - 基于Web的软著材料（源代码文档、操作手册、申请表）自动生成工具。详见 `docs/设计文档_v3.0.md`。

## 开发命令

```bash
# 后端
cd server
pip install -r requirements.txt
playwright install chromium
cp .env.example .env  # 配置AI模型API密钥
python app.py          # Flask，端口5000

# 前端
cd client
npm install
npm run dev            # Vite，端口5173，API代理到5000
npm run build          # 生产构建
```

## 架构

- 后端：Flask + ThreadPoolExecutor异步任务 + JSON文件持久化
- 前端：Vue3 + Vite + Element Plus + Pinia
- AI集成：智谱AI GLM-4（主）/ 通义千问（备），适配器模式
- 文档生成：python-docx
- 截图：Playwright无头Chromium
- 进度推送：SSE（降级轮询）

核心流程：6步编排器（功能清单→代码生成→HTML页面→截图→文档生成→打包）

## 注意事项

- 技术栈配置在 `server/tech_stacks/*.yaml`，新增技术栈只需添加YAML文件
- `server/generators/models.py` 中的 `ProjectContext` 是贯穿全流程的上下文对象
- `feature_list` 是三文档一致性的单一事实来源
- 编排器步骤中的 TODO 标记表示待实现的功能（Phase 3-4）
