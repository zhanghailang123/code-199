# MEM考研学习系统

> **目标院校**: 北京工业大学 MEM（工程管理硕士）在职研究生  
> **个人背景**: 五年后端程序员  
> **时间节点**: 2025年12月启动 → 2026年12月考试

---

## 项目目标

1. **智能刷题**: 
  - 支持按章节、知识点筛选题目
  - 自动记录错题，生成个性化练习计划
  - **PDF真题导入**: 支持上传PDF试卷，AI自动识别题目并批量录入题库
2. **知识图谱**: 可视化展示知识点关联，构建完整的知识体系查漏补缺
3. **系统化学习**: 章节式逐步推进，线性学习路径
4. **LLM智能分析**: 通过OpenAI兼容接口，自动分析题目、归类知识点

---

## 🚀 快速开始

### 一键启动 (Windows)
```bash
双击 start.bat
```
这会同时启动：
- **后端API** (端口 8000)
- **前端页面** (端口 5173)

### 命令行启动
```bash
# 终端 1: 后端
cd d:\newIDeaProject\code-199\scripts
python api.py

# 终端 2: 前端
cd d:\newIDeaProject\code-199\web
npm run dev
```

打开浏览器访问: **http://localhost:5173**

---

## ✨ 已实现功能

### 📊 仪表盘 (`/`)
- 题目统计、知识点统计
- 快速访问最近题目

### 📝 手动录入 (`/new/question`)
- 表单录入题目
- 实时 Markdown 预览

### 🤖 智能录入 (`/smart-entry`)
- 粘贴原题文本
- LLM 自动分析生成答案、解析、知识点
- 一键保存为 Markdown 文件

### 🧠 知识图谱 (`/graph`)
- Cytoscape.js 可视化
- 题目与知识点关联展示
- 多种布局：力导向/环形/同心圆
- 点击节点查看详情

### 📖 题目详情页 (`/question/:id`)
- 美化的题目展示
- 分色显示：题目(蓝)/选项(灰)/答案(绿)/解析(黄)
- 难度星级、知识点标签

---

## 📁 项目结构

```
code-199/
├── content/                 # 📚 数据层
│   ├── questions/           # 真题 (8道)
│   │   ├── 2024-math-q01.md
│   │   ├── 2024-math-q80.md  # AI生成
│   │   └── ...
│   ├── knowledge_base/      # 知识点库 (4个)
│   │   ├── math/            # 2个知识点
│   │   ├── logic/           # 1个知识点
│   │   └── english/         # 1个知识点
│   ├── curriculum/          # 学习章节 (待开发)
│   └── papers/              # 完整试卷 (待开发)
│
├── config/
│   └── config.yaml          # ⚙️ LLM API 配置
│
├── scripts/                 # � Python 后端
│   ├── api.py               # FastAPI 服务 (8000端口)
│   └── llm_analyzer.py      # LLM 分析器
│
├── web/                     # 🌐 Vue 3 前端
│   ├── src/
│   │   ├── views/
│   │   │   ├── HomeView.vue         # 仪表盘
│   │   │   ├── ContentView.vue      # 题目详情
│   │   │   ├── NewQuestionView.vue  # 手动录入
│   │   │   ├── SmartEntryView.vue   # 智能录入
│   │   │   └── KnowledgeGraphView.vue # 知识图谱
│   │   └── style.css        # Tailwind CSS
│   └── package.json
│
├── start.bat                # Windows 一键启动
└── readme.md
```

---

## 开发进度

### ✅ Phase 1: 基础搭建
- [x] 目录结构
- [x] Vite + Vue 3 + Tailwind CSS
- [x] 仪表盘页面
- [x] Markdown 渲染

### ✅ Phase 2: 数据录入
- [x] 手动录入表单
- [x] VSCode Snippets 快捷模板
- [x] 示例数据 (8道题 + 4个知识点)

### ✅ Phase 3: LLM 集成
- [x] `llm_analyzer.py` 分析器
- [x] `/api/analyze` 接口
- [x] 智能录入页面

### ✅ Phase 4: 可视化
- [x] 知识图谱 (Cytoscape.js)
- [x] 题目详情页美化
- [x] 动态 API 加载

### 🔄 Phase 5: 待完成功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 全部题目列表页 | ⬜ | 分页/筛选/搜索 |
| 学习章节系统 | ⬜ | curriculum 目录结构 |
| 学习进度追踪 | ⬜ | 打卡/统计 |
| 知识点详情页 | ⬜ | 关联题目展示 |
| 题目搜索 | ⬜ | 全文搜索 |
| Docker 部署 | ⬜ | 容器化 |

---

## ⚙️ LLM 配置

编辑 `config/config.yaml`:

```yaml
llm:
  api_key: "sk-你的密钥"
  base_url: "https://api.openai.com/v1"  # 或兼容服务
  model: "gpt-4o-mini"
```

支持 OpenAI、DeepSeek、Azure 等兼容接口。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Tailwind CSS |
| 后端 | Python FastAPI |
| 数据 | Markdown + YAML Frontmatter |
| 图谱 | Cytoscape.js |
| LLM | OpenAI 兼容 API |

---

## 下一步计划

1. **继续录入真题** - 使用智能录入批量导入 2024 年完整真题
2. **完善知识点库** - 根据题目提取的知识点建立关联
3. **学习章节系统** - 设计系统化学习路径