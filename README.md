# ScholarLens - 智能学术助手

> 一个基于AI的学术论文阅读、解析与发现平台

## 项目概述

ScholarLens 是一个面向研究人员和学生的智能学术助手，旨在帮助用户高效阅读、理解和管理学术论文。通过与arXiv官方API的深度集成，系统能够自动追踪用户感兴趣的领域，推送最新论文，确保文献的真实性和时效性。

## 核心功能

### 1. 论文智能解析
- **PDF结构解析**：自动识别论文标题、摘要、章节结构、参考文献
- **表格提取**：智能识别并提取论文中的表格数据
- **实体识别**：自动标注研究问题、方法、数据集、指标等关键实体
- **引用关系分析**：构建论文内部的引用网络

### 2. AI深度对话
- **多轮对话**：基于论文内容的智能问答系统
- **快速操作**：一键总结、解释难点、评估方法
- **多语言支持**：中英文无缝切换，消除语言障碍

### 3. arXiv 自动订阅推送
- **智能订阅**：支持关键词、分类、作者多维度订阅
- **自动爬取**：每6小时自动检查arXiv更新
- **匹配算法**：基于关键词(60%) + 分类(30%) + 作者(10%)的加权匹配
- **一键导入**：将arXiv论文直接导入本地库解析

### 4. 研究画像与趋势
- **个人画像**：基于阅读历史生成研究兴趣分布
- **趋势洞察**：可视化展示领域研究热点演变
- **智能推荐**：基于内容的个性化论文推荐

### 5. 阅读辅助工具
- **三种阅读模式**：浏览模式、深度模式、批判模式
- **进度追踪**：记录阅读时长和进度
- **笔记管理**：支持笔记记录和导出

## 技术架构

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.12+ | 开发语言 |
| FastAPI | 0.115.0 | Web框架 |
| SQLAlchemy | 2.0.35 | ORM框架 |
| SQLite | - | 数据库 |
| PyMuPDF | 1.24.10 | PDF解析 |
| OpenAI SDK | 1.50.0 | AI对话 |
| APScheduler | 3.10.4 | 定时任务 |
| Requests | 2.32.5 | HTTP客户端 |

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.x | UI框架 |
| TypeScript | 5.x | 类型系统 |
| Vite | 5.x | 构建工具 |
| TailwindCSS | 3.x | 样式框架 |
| Zustand | - | 状态管理 |
| Axios | - | HTTP客户端 |
| Lucide React | - | 图标库 |

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (React)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 论文上传 │ │ 阅读界面 │ │ AI对话   │ │ 订阅管理 │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│                      后端层 (FastAPI)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 论文API  │ │ 解析服务 │ │ arXivAPI │ │ 任务调度 │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                        数据层                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ SQLite   │ │ 文件存储 │ │ arXivAPI │ │ LLM API  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 核心模块详解

### arXiv 订阅推送系统

#### 订阅模型
```python
class ArxivSubscription(Base):
    id: str                    # 订阅ID
    user_id: str              # 用户ID
    name: str                 # 订阅名称
    keywords: List[str]       # 关键词列表
    categories: List[str]     # arXiv分类
    authors: List[str]        # 关注作者
    max_results: int          # 最大结果数
    is_active: bool           # 是否活跃
    last_crawled: datetime    # 上次爬取时间
```

#### 匹配算法
```python
# 关键词匹配 (权重: 60%)
keyword_score = (匹配关键词数 / 总关键词数) × 0.6

# 分类匹配 (权重: 30%)
category_score = (交集分类数 / 订阅分类数) × 0.3

# 作者匹配 (权重: 10%)
author_score = (匹配作者数 / 订阅作者数) × 0.1

# 综合得分
final_score = min(keyword_score + category_score + author_score, 1.0)
```

#### 定时任务
- 使用 APScheduler 实现后台定时任务
- 每6小时自动爬取所有活跃订阅
- 支持手动触发即时爬取

### PDF 解析引擎

#### 文本提取
- 基于 PyMuPDF 提取结构化文本
- 保留字体大小、粗细等格式信息
- 识别章节层级结构

#### 表格提取
- 智能识别表格边界
- 处理合并单元格
- 关联表格标题

### AI 对话系统

#### 上下文管理
- 维护对话历史
- 基于论文内容的RAG检索
- 支持多轮连贯对话

#### 提示词工程
- 角色设定：专业学术助手
- 输出格式：结构化Markdown
- 语言适配：中英文双语

## 项目结构

```
paper_assitant/
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── api/v1/            # API路由
│   │   │   ├── arxiv.py       # arXiv相关API
│   │   │   ├── papers.py      # 论文管理API
│   │   │   └── ...
│   │   ├── core/              # 核心模块
│   │   │   └── pdf_parser/    # PDF解析器
│   │   ├── models/            # 数据模型
│   │   │   ├── arxiv.py       # arXiv模型
│   │   │   ├── paper.py       # 论文模型
│   │   │   └── task.py        # 任务模型
│   │   ├── services/          # 业务服务
│   │   │   ├── arxiv_service.py    # arXiv服务
│   │   │   ├── arxiv_crawler.py    # arXiv爬虫
│   │   │   └── parsing_service.py  # 解析服务
│   │   └── tasks/             # 后台任务
│   │       ├── scheduler.py   # 定时调度器
│   │       └── worker.py      # 任务执行器
│   ├── data/                  # 数据目录
│   ├── uploads/               # 上传文件目录
│   └── main.py                # 应用入口
│
├── frontend/                   # 前端项目
│   ├── src/
│   │   ├── api/               # API客户端
│   │   │   └── arxiv.ts       # arXiv API
│   │   ├── components/        # 组件
│   │   │   ├── arxiv/         # arXiv相关组件
│   │   │   ├── chat/          # 聊天组件
│   │   │   └── layout/        # 布局组件
│   │   ├── pages/             # 页面
│   │   │   ├── SubscriptionsPage.tsx  # 订阅管理
│   │   │   ├── ArxivPushesPage.tsx    # 推送列表
│   │   │   └── PaperPage.tsx          # 论文阅读
│   │   └── store/             # 状态管理
│   └── package.json
│
└── README.md                  # 项目说明
```

## 安装与运行

### 环境要求
- Python 3.12+
- Node.js 18+
- Git

### 后端部署

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 创建 .env 文件，添加：
# LLM_API_KEY=your_api_key
# LLM_BASE_URL=https://api.kimi.com/coding/v1

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端部署

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 访问应用

- 前端界面：http://localhost:5173
- 后端API文档：http://localhost:8000/docs

## API 文档

### arXiv 订阅管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/arxiv/subscriptions` | 创建订阅 |
| GET | `/api/v1/arxiv/subscriptions/{user_id}` | 获取用户订阅 |
| PUT | `/api/v1/arxiv/subscriptions/{id}` | 更新订阅 |
| DELETE | `/api/v1/arxiv/subscriptions/{id}` | 删除订阅 |
| POST | `/api/v1/arxiv/crawl/{subscription_id}` | 手动触发爬取 |

### arXiv 推送管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/arxiv/pushes/{user_id}` | 获取用户推送 |
| GET | `/api/v1/arxiv/pushes/{user_id}/unread-count` | 获取未读数量 |
| POST | `/api/v1/arxiv/pushes/{push_id}/read` | 标记已读 |
| POST | `/api/v1/arxiv/import` | 导入arXiv论文 |

### 论文管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/papers` | 上传论文 |
| GET | `/api/v1/papers/{paper_id}` | 获取论文详情 |
| GET | `/api/v1/papers/{paper_id}/sections` | 获取论文章节 |
| GET | `/api/v1/papers/{paper_id}/entities` | 获取实体标注 |
| POST | `/api/v1/chat` | AI对话 |

## 特色亮点

### 1. 真实可靠的文献源
- 直接对接arXiv官方API
- 100%真实论文，无伪造风险
- 自动获取最新研究成果

### 2. 智能匹配算法
- 多维度匹配（关键词+分类+作者）
- 可配置的匹配阈值
- 基于阅读历史的动态调整

### 3. 本地优先设计
- SQLite数据库，无需额外配置
- 本地文件存储，数据可控
- 离线可查看已导入论文

### 4. 扩展性架构
- 模块化设计，易于扩展
- 插件化PDF解析器
- 可配置的LLM提供商

## 应用场景

### 学术研究
- 跟踪研究领域最新进展
- 快速筛选相关论文
- 深度阅读和理解论文内容

### 文献综述
- 批量导入和分析论文
- 提取关键信息和方法
- 生成综述报告

### 学习辅助
- 理解复杂概念和方法
- 多语言翻译和解释
- 互动式问答学习

## 未来规划

### 短期计划
- [ ] 支持更多论文源（PubMed, IEEE等）
- [ ] 论文相似度推荐
- [ ] 阅读笔记导出

### 长期愿景
- [ ] 协作阅读功能
- [ ] 研究知识图谱
- [ ] 学术社交网络

## 贡献指南

欢迎提交Issue和Pull Request！

### 提交规范
- 使用清晰的提交信息
- 遵循现有代码风格
- 添加必要的测试

## 许可证

MIT License

## 联系方式

- 项目地址：https://github.com/yourusername/scholarlens
- 问题反馈：请提交GitHub Issue

---

> **注意**：本项目仅供学习和研究使用，请遵守相关学术规范和版权法规。
