# MEM考研学习系统

> **目标院校**: 北京工业大学 MEM（工程管理硕士）在职研究生  
> **个人背景**: 五年后端程序员  
> **时间节点**: 2025年12月启动 → 2026年12月考试

---

## 🎯 项目目标

1. **智能刷题**: 按知识点筛选、自动记录错题、个性化练习
2. **PDF真题导入**: 上传PDF试卷 → AI识别题目 → 批量录入题库
3. **英语多维分析**: 词汇联想、长难句拆解、阅读技巧
4. **知识图谱**: 可视化知识点关联，查漏补缺
5. **系统化学习**: 章节式学习路径

---

## 🚀 快速开始

### 1. 拉取项目
```bash
git clone https://github.com/zhanghailang123/code-199.git
cd code-199
```

### 2. 安装依赖

**后端 (Python)**
```bash
pip install fastapi uvicorn pyyaml openai pypdfium2 pillow
```

**前端 (Node.js)**
```bash
cd web
npm install
cd ..
```

### 3. 配置 LLM
编辑 `config/config.yaml`:
```yaml
llm:
  api_key: "your-api-key"
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o-mini"
```

### 4. 启动项目

**方式一：一键启动 (Windows)**
```bash
双击 start.bat
```

**方式二：手动启动**
```bash
# 终端1 - 后端
cd scripts
python api.py

# 终端2 - 前端
cd web
npm run dev
```

### 5. 访问
- **后端API**: http://localhost:8000
- **前端页面**: http://localhost:5173


---

## ✨ 已实现功能

### 📊 仪表盘 (`/`)
- 题目统计、知识点统计、连续打卡
- 快速访问题目和知识点列表

### 📝 题目管理
| 功能 | 路由 | 说明 |
|------|------|------|
| 全部题目 | `/questions` | 按科目筛选、搜索、网格展示 |
| 手动录入 | `/new/question` | 表单录入 + Markdown预览 |
| 智能录入 | `/smart-entry` | 粘贴原题 → LLM自动分析 |
| 题目详情 | `/question/:id` | 分色展示题目/选项/答案/解析 |

### 📄 PDF真题导入 (`/pdf-import`) ⭐ NEW
- 上传PDF → 自动转换为图片
- 逐页分析 or **整卷分析**（处理跨页题目）
- 批量录入到题库
- 支持英语真题的多维度分析

### 🧠 知识图谱 (`/graph`)
- Cytoscape.js 可视化
- 题目↔知识点关联
- 力导向/环形/同心圆布局

### 📚 学习路径 (`/curriculum`)
| 科目 | 章节 |
|------|------|
| 数学 | 算术 → 代数 → 几何 → 数据分析 |
| 逻辑 | 形式逻辑 → 论证逻辑 → 分析推理 |
| 英语 | 词汇语法 → 阅读理解 → 写作翻译 |

### 🇬🇧 英语专项分析 ⭐ NEW
- **核心词汇**: 音标 + 释义 + 例句 + 联想词
- **长难句分析**: 结构拆解 + 类似句子示例
- **阅读技巧**: 题型分类 + 解题策略 + 干扰项分析

---

## 🎮 待开发功能（学习助力）

### 🔥 高优先级
| 功能 | 说明 | 价值 |
|------|------|------|
| 📅 **每日打卡** | 每天完成N题解锁徽章 | 养成习惯 |
| 🎯 **错题本** | 自动记录做错的题，智能复习 | 针对性提升 |
| ⏱️ **限时模拟** | 模拟真实考试环境计时答题 | 适应考场 |
| 📈 **学习统计** | 每日/周/月做题量、正确率趋势 | 可视化进步 |

### 💡 趣味功能
| 功能 | 说明 | 价值 |
|------|------|------|
| 🎲 **随机一题** | 随机抽取一道题开始练习 | 碎片时间利用 |
| 🏆 **成就系统** | 解锁成就徽章（首次满分、连续7天等） | 激励坚持 |
| 📊 **能力雷达图** | 知识点掌握程度可视化 | 明确薄弱点 |
| 🔔 **每日一句** | 每天推送一个长难句 | 渐进式学习 |

### 🛠️ 系统增强
| 功能 | 说明 |
|------|------|
| 🐳 Docker部署 | 一键部署到服务器 |
| 📱 移动端适配 | 手机刷题 |
| 🔍 全文搜索 | 搜索题目内容 |
| 📤 导出功能 | 导出错题本为PDF |

---

## 📁 项目结构

```
code-199/
├── content/                 # 📚 数据层
│   ├── questions/           # 题库
│   ├── knowledge_base/      # 知识点库
│   └── curriculum/          # 学习章节
│       ├── math/            # 4章
│       ├── logic/           # 3章
│       └── english/         # 3章
│
├── config/config.yaml       # ⚙️ LLM配置
│
├── scripts/                 # 🐍 Python后端
│   ├── api.py              # FastAPI服务
│   ├── llm_analyzer.py     # LLM分析器
│   └── pdf_processor.py    # PDF处理器
│
├── web/                     # 🌐 Vue3前端
│   └── src/views/
│       ├── HomeView.vue           # 仪表盘
│       ├── QuestionsView.vue      # 题目列表
│       ├── ContentView.vue        # 题目详情
│       ├── SmartEntryView.vue     # 智能录入
│       ├── PdfUploadView.vue      # PDF导入
│       ├── KnowledgeGraphView.vue # 知识图谱
│       └── CurriculumView.vue     # 学习路径
│
├── start.bat               # Windows启动
└── readme.md
```

---

## ⚙️ LLM 配置

编辑 `config/config.yaml`:

```yaml
llm:
  api_key: "your-api-key"
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o-mini"
```

支持: OpenAI / DeepSeek / Gemini 等兼容接口

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Tailwind CSS |
| 后端 | Python FastAPI |
| 数据 | Markdown + YAML Frontmatter |
| 图谱 | Cytoscape.js |
| LLM | OpenAI 兼容 API |
| PDF | pypdfium2 |

---

## 开发日志

- **2025-12-17**: PDF真题导入、整卷分析、英语多维分析
- **2025-12-16**: 知识图谱、学习路径、智能录入
- **2025-12-15**: 项目初始化、基础框架