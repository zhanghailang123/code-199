# 云端部署设计文档

## 架构概览

```mermaid
graph LR
    subgraph Cloudflare
        A[CF Pages<br/>前端]
    end
    subgraph Render.com
        B[Web Service<br/>FastAPI 后端]
        C[持久化磁盘<br/>content/]
    end
    D[用户浏览器] --> A
    A --> B
    B --> C
```

- **前端**：Cloudflare Pages（免费，无限请求）
- **后端**：Render.com Web Service（免费层：750小时/月，带磁盘）
- **数据**：Markdown 文件持久化存储在 Render 磁盘上

---

## 需要的改动

### 1. 前端配置（Cloudflare Pages）

#### [新增] `web/.env.production`
```bash
VITE_API_BASE_URL=https://mem-study-api.onrender.com
```

#### [修改] 前端 API 调用
将所有硬编码的 `http://localhost:8000` 替换为环境变量：
```javascript
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

**需要修改的文件：**
- `web/src/views/VocabularyView.vue`
- `web/src/views/ContentView.vue`
- `web/src/components/VocabularyDetail.vue`

---

### 2. 后端配置（Render.com）

#### [新增] `render.yaml`
```yaml
services:
  - type: web
    name: mem-study-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn scripts.api:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
    disk:
      name: content-data
      mountPath: /opt/render/project/src/content
      sizeGB: 1
```

#### [新增] `requirements.txt`
```text
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pyyaml>=6.0
openai>=1.0.0
pypdfium2>=4.0.0
python-multipart>=0.0.6
```

#### [修改] `scripts/api.py`
更新 CORS 配置以允许生产域名：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://hailang0616.xyz",  # 你的 CF Pages 域名
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 3. LLM 配置

#### [新增] `config/config.yaml.example`
```yaml
llm:
  api_key: "your-api-key-here"
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o-mini"
```

> **重要提示**：在 Render 上部署时，请使用环境变量 `LLM_API_KEY` 而不是配置文件。

#### [修改] `scripts/llm_analyzer.py`
添加环境变量回退机制：
```python
import os

def load_config():
    # 优先使用环境变量（云端部署）
    if os.environ.get("LLM_API_KEY"):
        return {
            "llm": {
                "api_key": os.environ.get("LLM_API_KEY"),
                "base_url": os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
                "model": os.environ.get("LLM_MODEL", "gpt-4o-mini")
            }
        }
    # 回退到本地配置文件
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}
```

---

## 部署步骤

### 前端（Cloudflare Pages）
1. 将代码推送到 GitHub
2. 进入 [Cloudflare 控制台](https://dash.cloudflare.com) → Pages
3. 创建项目 → 连接 GitHub 仓库
4. 配置：
   - 构建命令：`npm run build`
   - 输出目录：`dist`
   - 根目录：`web`
5. 添加环境变量：`VITE_API_BASE_URL`

### 后端（Render.com）
1. 将代码推送到 GitHub
2. 进入 [Render 控制台](https://dashboard.render.com)
3. 新建 → Web Service → 连接 GitHub 仓库
4. 配置：
   - 运行时：Python 3
   - 构建命令：`pip install -r requirements.txt`
   - 启动命令：`uvicorn scripts.api:app --host 0.0.0.0 --port $PORT`
5. 添加磁盘（1GB，挂载到 `/opt/render/project/src/content`）
6. 添加环境变量：`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`

---

## 验证计划

### 冒烟测试
- [ ] 前端在 CF Pages 域名上正常加载
- [ ] API 在 Render URL 上正常响应
- [ ] CORS 允许跨域请求
- [ ] 单词增删改查功能正常
- [ ] LLM 生成功能正常（使用环境变量）

### 数据持久化
- [ ] 创建新单词 → 重启 Render 服务 → 单词仍然存在

---

## 本地开发兼容性

所有改动都采用**向后兼容**设计：

| 场景 | 行为 |
|------|------|
| 本地开发（无环境变量） | 自动使用 `localhost:8000` 和本地 `config.yaml` |
| 云端部署（有环境变量） | 自动使用生产配置 |

**不会影响现有的本地开发流程。**
