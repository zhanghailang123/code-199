"""
LLM Analyzer Module
Uses OpenAI-compatible API to analyze exam questions.
"""
import yaml
from pathlib import Path
from openai import OpenAI

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yaml"

def load_config():
    """Load configuration from config.yaml"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

def get_client():
    """Get OpenAI client with config"""
    config = load_config()
    llm_config = config.get("llm", {})
    
    return OpenAI(
        api_key=llm_config.get("api_key", ""),
        base_url=llm_config.get("base_url", "https://api.openai.com/v1")
    )

def get_model():
    """Get configured model name"""
    config = load_config()
    return config.get("llm", {}).get("model", "gpt-4o-mini")


ANALYZE_PROMPT = """你是一个专业的管理类联考（MEM/MBA）辅导老师，请分析以下考研真题。

题目内容：
{question_text}

请按照以下JSON格式返回分析结果（确保返回的是合法的JSON）：

```json
{{
    "subject": "math或logic或english",
    "type": "choice或fill或essay",
    "difficulty": 1到5的数字,
    "content": "题目主体内容（不含选项）",
    "options": "选项文本，格式为 A. xxx\\nB. xxx\\n...",
    "answer": "正确答案，如 C",
    "explanation": "详细解析步骤，包含解题思路和技巧",
    "knowledge_points": ["知识点1", "知识点2"],
    "tags": ["标签1", "标签2"]
}}
```

注意：
1. subject 只能是 math、logic、english 之一
2. difficulty: 1=简单, 3=中等, 5=困难
3. explanation 要详细，包含解题步骤
4. knowledge_points 提取核心考点
5. 返回纯JSON，不要有其他文字"""


# English-specialized analysis prompt with vocabulary and sentence dimensions
ENGLISH_ANALYZE_PROMPT = """你是一位资深的考研英语辅导专家，请对以下英语真题进行多维度深度分析。

题目内容：
{question_text}

请按照以下JSON格式返回分析结果（确保返回的是合法的JSON）：

```json
{{
    "subject": "english",
    "type": "choice或reading或translation或writing",
    "difficulty": 1到5的数字,
    "content": "题目主体内容",
    "options": "选项文本（如有）",
    "answer": "正确答案",
    "explanation": "详细解析，包含解题思路",
    "knowledge_points": ["考点1", "考点2"],
    "tags": ["标签"],
    
    "vocabulary": [
        {{
            "word": "核心词汇",
            "phonetic": "音标",
            "meaning": "中文释义",
            "example": "例句",
            "associated_words": ["联想词1", "联想词2", "联想词3"]
        }}
    ],
    
    "key_sentences": [
        {{
            "original": "题目中的关键句/长难句",
            "translation": "中文翻译",
            "structure": "句子结构分析（主干+修饰成分）",
            "similar_sentences": [
                "类似结构的句子示例1",
                "类似结构的句子示例2"
            ]
        }}
    ],
    
    "reading_skills": {{
        "question_type": "题型分类（主旨/细节/推理/态度/词义）",
        "solving_strategy": "解题策略",
        "distractor_analysis": "干扰项分析"
    }}
}}
```

分析要求：
1. vocabulary：提取3-5个核心词汇，每个词汇附带2-3个联想词（同义词/反义词/词根相关）
2. key_sentences：提取1-2个长难句，分析结构，并给出2个结构类似的句子示例
3. reading_skills：仅阅读理解题需要填写此项
4. 确保所有中文翻译准确流畅
5. 返回纯JSON，不要有其他文字"""


def analyze_question(question_text: str) -> dict:
    """
    Analyze a question using LLM.
    
    Args:
        question_text: Raw question text (can include options, answer, etc.)
    
    Returns:
        Dictionary with analyzed question data
    """
    client = get_client()
    model = get_model()
    
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的考研辅导老师，擅长分析管理类联考真题。请务必按照用户要求的JSON格式返回结果。"},
                {"role": "user", "content": ANALYZE_PROMPT.format(question_text=question_text)}
            ],
            temperature=0.3
            # Note: removed response_format for compatibility with non-OpenAI models
        )
        
        content = response.choices[0].message.content
        
        # Extract JSON from response (handle markdown code blocks)
        import json
        import re
        
        # Try to find JSON in code blocks first
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Try to find raw JSON object
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content
        
        result = json.loads(json_str)
        
        return {
            "success": True,
            "data": result
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON解析失败: {str(e)}\n原始响应: {content[:500] if 'content' in dir() else 'N/A'}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def analyze_english_question(question_text: str) -> dict:
    """
    Analyze an English question with multi-dimensional analysis.
    Includes vocabulary, associated words, key sentences, and similar examples.
    
    Args:
        question_text: Raw English question text
    
    Returns:
        Dictionary with comprehensive English analysis data
    """
    client = get_client()
    model = get_model()
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位资深的考研英语辅导专家，擅长词汇、语法、阅读理解和写作分析。请务必按照用户要求的JSON格式返回结果。"},
                {"role": "user", "content": ENGLISH_ANALYZE_PROMPT.format(question_text=question_text)}
            ],
            temperature=0.3,
            max_tokens=4096
        )
        
        content = response.choices[0].message.content
        
        import json
        import re
        
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content
        
        result = json.loads(json_str)
        
        return {
            "success": True,
            "data": result
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON解析失败: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


BATCH_ANALYZE_PROMPT = """你是一个专业的管理类联考（MEM/MBA）辅导老师。请批量分析以下考研真题。

题目列表：
{questions_json}

请对每一道题进行分析，并返回一个包含所有题目分析结果的数组。

请严格按照以下JSON数组格式返回：
```json
[
  {{
    "original_number": "题目原始编号",
    "subject": "math或logic或english",
    "type": "choice或fill或essay",
    "difficulty": 1到5的数字,
    "content": "题目主体内容",
    "options": "选项文本，格式为 A. xxx\\nB. xxx...",
    "answer": "正确答案",
    "explanation": "详细解析步骤",
    "knowledge_points": ["考点1", "考点2"],
    "tags": ["标签1"]
  }},
  ...
]
```

注意：
1. 数组长度必须与输入题目数量一致。
2. 保持顺序对应。
3. 如果某题无法分析，也请返回一个基本对象，并在 explanation 中说明原因。
"""

def batch_analyze_questions(questions: list) -> list:
    """
    Batch analyze multiple questions using LLM.
    
    Args:
        questions: List of dicts, each with 'number', 'content', 'options'
        
    Returns:
        List of dicts with analyzed data
    """
    client = get_client()
    model = get_model()
    
    import json
    questions_str = json.dumps(questions, ensure_ascii=False, indent=2)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的考研辅导老师。请批量处理题目分析任务。"},
                {"role": "user", "content": BATCH_ANALYZE_PROMPT.format(questions_json=questions_str)}
            ],
            temperature=0.3,
            max_tokens=4096
        )
        
        content = response.choices[0].message.content
        
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content
                
        results = json.loads(json_str)
        return results
        
    except Exception as e:
        # Fallback: process individually if batch fails
        print(f"Batch analysis failed: {e}, falling back to individual processing")
        results = []
        for q in questions:
            q_text = f"题号：{q.get('number')}\n题目：{q.get('content')}\n选项：{q.get('options')}"
            res = analyze_question(q_text)
            if res['success']:
                res['data']['original_number'] = q.get('number')
                results.append(res['data'])
            else:
                results.append({"error": res.get("error"), "original_number": q.get("number")})
        return results



VOCABULARY_FRONTMATTER_PROMPT = """你是一个专业的考研词汇助手。请根据用户提供的单词笔记内容，提取并生成 YAML Frontmatter 信息。

用户提供的笔记内容：
{content}

请提取以下信息并返回 JSON 格式：
1. word: 单词本身（从内容中推断）
2. phonetic: 单词的国际音标（IPA），必须生成
3. definitions: 定义列表，包含 part(词性), translation(简短释义), text(详细释义/英文释义)
4. tags: 标签列表（基于内容推断，如：考研, 阅读, 写作, 高频等）
5. status: 默认为 "learning"

要求：
- id 生成格式为 "vocab-" + 单词小写
- definitions 中的 translation 要简练
- phonetic 必须提供，例如 "/ˈskræpɪŋ/"
- 返回纯 JSON 格式，不要包含 ```json 包裹

示例返回：
{{
  "id": "vocab-scrapping",
  "word": "Scrapping",
  "phonetic": "/ˈskræpɪŋ/",
  "tags": ["考研", "阅读"],
  "status": "learning",
  "definitions": [
    {{ "part": "v.", "translation": "废除", "text": "废除，取消；扔掉" }}
  ],
  "related_questions": []
}}
"""

def generate_vocabulary_frontmatter(content: str) -> str:
    """
    Generate YAML frontmatter for vocabulary content using LLM.
    
    Args:
        content: The raw markdown content of the vocabulary note
        
    Returns:
        String containing the YAML frontmatter (including --- separators)
    """
    client = get_client()
    model = get_model()
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个辅助生成 Markdown Frontmatter 的工具。"},
                {"role": "user", "content": VOCABULARY_FRONTMATTER_PROMPT.format(content=content[:2000])} # Limit context
            ],
            temperature=0.3
        )
        
        json_str = response.choices[0].message.content.strip()
        
        # Clean up potential markdown blocks
        if json_str.startswith("```"):
            import re
            match = re.search(r'```(?:json)?\s*([\s\S]*?)```', json_str)
            if match:
                json_str = match.group(1).strip()
        
        import json
        data = json.loads(json_str)
        
        # Convert to YAML manually to match specific format requirements
        lines = ["---"]
        lines.append(f'id: "{data.get("id", "")}"')
        lines.append(f'word: "{data.get("word", "")}"')
        lines.append(f'phonetic: "{data.get("phonetic", "")}"')
        
        # Tags
        tags = data.get("tags", [])
        tags_str = ", ".join([f'"{t}"' for t in tags])
        lines.append(f'tags: [{tags_str}]')
        
        lines.append(f'status: "{data.get("status", "learning")}"')
        
        # Definitions - Flatten to single line style if possible, or standard flow
        defs = data.get("definitions", [])
        import json as j
        # Use JSON stringify for the list of dicts to match user preference: definitions: [{"part":...}]
        # But ensure it's valid YAML. JSON is valid YAML.
        lines.append(f'definitions: {j.dumps(defs, ensure_ascii=False)}')
        
        lines.append('related_questions: []')
        lines.append('---')
        lines.append('')
        
        return "\n".join(lines)
        
    except Exception as e:
        print(f"Error generating frontmatter: {e}")
        # Fallback minimal frontmatter
        return "---\nid: vocab-unknown\nword: Unknown\nstatus: learning\n---\n"


VOCABULARY_ARTICLE_PROMPT = """你是一位资深的考研英语辅导名师，讲课风格风趣幽默，直击痛点，擅长用最直观的逻辑帮学生死磕核心词汇。

请为单词 "{word}" 撰写一篇考研风格的深度单词笔记。

### 风格要求：
1.  **语气**：像面对面辅导一样，开篇要直接（"考研党你好！"），中间要穿插鼓励和警示（"千万别搞混..."，"这是拿分的关键！"）。
2.  **排版**：严格遵守 Markdown 格式，使用 **粗体** 强调重点，使用 > 引用块展示例句。
3.  **结构**：必须包含以下五个部分（标题要完全一致）：
    -   开篇引入（一两句话，直击单词在考研中的地位或常见误区）
    -   ### 一、 核心记忆锚点（Root & Logic）
    -   ### 二、 考研核心考法（The "Killer" Meaning）
    -   ### 三、 考研“视觉陷阱”警报（Visual Trap） (如果有形近词/易混词，没有则跳过)
    -   ### 四、 考研写作替换（Writing Upgrade）
    -   ### 五、 沉浸式记忆（Scenario）
    -   结尾鼓励（一句话总结）

### 内容要求：
1.  **Frontmatter**：文章开头必须包含标准的 YAML Frontmatter（id, word, phonetic, tags, status, definitions, related_questions）。
2.  **Definitions 格式**：definitions 列表中的每一项必须严格包含以下字段：
    -   `part`: 词性（如 v., adj., n.）
    -   `translation`: 简短中文释义（用于列表显示）
    -   `text`: 详细释义（可包含英文或扩展）
    -   ❌ **禁止使用** `part_of_speech` 或 `meaning` 此类字段名。
3.  **Tags**：自动推断标签，如 ["考研", "阅读", "高频"]。
4.  **真题模拟**：在"考研核心考法"中，必须编造或引用一句类似于考研真题的例句，并附带解析。
5.  **写作替换**：提供 Low Level vs High Level 的对比。
6.  **音标**：必须包含 IPA 音标。

### 示例参考：
(Frontmatter...)
考研党你好！看到 **Scrapping** 这个词，千万别以为是“刮擦”...
### 一、 核心记忆锚点（Root & Logic）
...

### 重要提示：
-   **直接输出 Markdown 内容**，不要用 ```markdown 或 ``` 包含整个回复。
-   确保第一行是 `---`。
-   确保 Frontmatter 格式正确。

请开始创作：
"""

def generate_vocabulary_article(word: str) -> str:
    """
    Generate a full vocabulary article with frontmatter using LLM.
    
    Args:
        word: The word to generate content for
        
    Returns:
        Full Markdown string
    """
    client = get_client()
    model = get_model()
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位考研英语名师。"},
                {"role": "user", "content": VOCABULARY_ARTICLE_PROMPT.format(word=word)}
            ],
            temperature=0.7 # Slight creativity for tone
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up code blocks if present
        # Fix: Regex should match ANY language identifier (e.g. yaml, markdown) and strip it
        if content.startswith("```"):
            import re
            match = re.search(r'```(?:\w+)?\s*([\s\S]*?)```', content)
            if match:
                content = match.group(1).strip()
        
        # Ensure it starts with Frontmatter
        if not content.startswith("---"):
            # If the LLM returned just YAML logic without ---, or just text, we try to fix or wrap
            # But likely if it's "yaml\n..." we already stripped "yaml" with regex if it was in fence. 
            # If it was NOT in fence but started with "yaml", we handle that:
            lines = content.split('\n')
            if lines[0].strip().lower() == 'yaml':
                content = '\n'.join(lines[1:]).strip()
            
            if not content.startswith("---"):
                 # Force add wrapper if missing
                 content = f"---\n{content}"
                 # We might also need to close it if missing, but let's assume LLM follows format mostly
                 
        return content
        
    except Exception as e:
        print(f"Error generating article: {e}")
        # Fallback
        return f"---\nid: vocab-{word.lower()}\nword: {word}\nstatus: learning\n---\n\n## Generation Failed\n\nError: {e}"

if __name__ == "__main__":
    pass
