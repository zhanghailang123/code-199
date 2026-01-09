"""
LLM Analyzer Module
Uses OpenAI-compatible API to analyze exam questions.
"""
import os
import yaml
from pathlib import Path
from openai import OpenAI

# Import learning-focused prompts from centralized file
from prompts import (
    MATH_ANALYZE_PROMPT,
    LOGIC_ANALYZE_PROMPT,
    ENGLISH_ANALYZE_PROMPT,
    GENERAL_ANALYZE_PROMPT,
    WRITING_ANALYZE_PROMPT,
    VOCABULARY_ARTICLE_PROMPT
)

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yaml"

def load_config():
    """Load configuration from environment variables or config.yaml"""
    # Try environment variables first (for cloud deployment)
    if os.environ.get("LLM_API_KEY"):
        return {
            "llm": {
                "api_key": os.environ.get("LLM_API_KEY"),
                "base_url": os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
                "model": os.environ.get("LLM_MODEL", "gpt-4o-mini")
            }
        }
    # Fall back to config file
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

# Note: All prompts (MATH_ANALYZE_PROMPT, LOGIC_ANALYZE_PROMPT, ENGLISH_ANALYZE_PROMPT, GENERAL_ANALYZE_PROMPT)
# are now imported from prompts.py for centralized maintenance.


def analyze_question_with_image(image_base64: str, subject: str = None, mime_type: str = "image/png") -> dict:
    """
    Analyze a question from an image using LLM Vision.
    
    Args:
        image_base64: Base64 encoded image data
        subject: Optional hint for subject (math, logic, english)
        mime_type: Image MIME type (image/png or image/jpeg)
    
    Returns:
        Dictionary with analyzed question data
    """
    client = get_client()
    model = get_model()
    
    # Choose prompt based on subject
    if subject == 'math':
        prompt = MATH_ANALYZE_PROMPT.replace("{question_text}", "请识别图片中的数学题目内容，并进行分析。")
        system_msg = "你是一位资深的考研数学名师，擅长通过图片识别试题并进行深度讲解。"
    elif subject == 'logic':
        prompt = LOGIC_ANALYZE_PROMPT.replace("{question_text}", "请识别图片中的逻辑题目内容，并进行分析。")
        system_msg = "你是一位资深的考研逻辑名师，擅长通过图片识别试题并进行深度讲解。"
    elif subject == 'english':
        prompt = ENGLISH_ANALYZE_PROMPT.replace("{question_text}", "请识别图片中的英语题目内容，并进行分析。")
        system_msg = "你是一位资深的考研英语名师，擅长通过图片识别试题并进行深度讲解。"
    elif subject == 'writing':
        prompt = WRITING_ANALYZE_PROMPT.replace("{question_text}", "请识别图片中的写作题目内容，并进行全面分析，包括范文。")
        system_msg = "你是一位资深的管综写作名师，擅长论证有效性分析和论说文辅导。"
    else:
        prompt = GENERAL_ANALYZE_PROMPT.replace("{question_text}", "请识别图片中的题目内容，并进行分析。")
        system_msg = "你是一个专业的考研辅导老师，擅长通过图片识别试题并进行深度讲解。"
    
    # Add image-specific instruction
    image_instruction = """
【图片识别任务】
请先仔细识别图片中的题目内容（包括题干、选项、图形等），然后按照要求的JSON格式进行分析。
如果图片中包含几何图形，请在content中注明"（含几何图形，请参考原图）"。
如果图片模糊或无法识别，请在返回中注明。
"""
    full_prompt = image_instruction + "\n\n" + prompt
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": full_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=65536  # Increased for writing questions with long responses
        )
        
        content = response.choices[0].message.content
        
        # Debug: Log response for troubleshooting
        print(f"[LLM Response Preview]: {content[:500] if content else 'EMPTY'}...")
        
        if not content or not content.strip():
            return {
                "success": False,
                "error": "LLM返回了空内容，请稍后重试"
            }
        
        # Extract JSON from response
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
            "error": f"JSON解析失败: {str(e)}",
            "raw_response": content[:1000] if 'content' in dir() else "无响应内容"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def analyze_question(question_text: str, subject: str = None) -> dict:
    """
    Analyze a question using LLM.
    
    Args:
        question_text: Raw question text (can include options, answer, etc.)
        subject: Optional hint for subject (math, logic, english)
    
    Returns:
        Dictionary with analyzed question data
    """
    client = get_client()
    model = get_model()
    
    # Choose prompt based on subject
    if subject == 'math':
        prompt = MATH_ANALYZE_PROMPT
        system_msg = "你是一位资深的考研数学名师。"
    elif subject == 'logic':
        prompt = LOGIC_ANALYZE_PROMPT
        system_msg = "你是一位资深的考研逻辑名师。"
    elif subject == 'english':
        prompt = ENGLISH_ANALYZE_PROMPT # Use the detailed English prompt
        system_msg = "你是一位资深的考研英语名师。"
    elif subject == 'writing':
        prompt = WRITING_ANALYZE_PROMPT # Use the specialized writing prompt
        system_msg = "你是一位资深的管综写作名师，擅长论证有效性分析和论说文辅导。"
    else:
        # Fallback for old/generic calls
        prompt = GENERAL_ANALYZE_PROMPT
        system_msg = "你是一个专业的考研辅导老师，擅长分析管理类联考真题。"
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt.format(question_text=question_text)}
            ],
            temperature=0.3
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
            max_tokens=65536
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
            max_tokens=65536
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

def generate_vocab_card(word: str, phonetic: str, definitions) -> dict:
    """
    Generate clean card content for export using LLM.
    
    Args:
        word: The vocabulary word
        phonetic: Phonetic transcription
        definitions: List of definition dicts with 'pos' and 'meaning' (or string)
    
    Returns:
        Dict with card_data: {definition, memory_tip, example}
    """
    client = get_client()
    model = get_model()
    
    # Handle different formats of definitions
    import json
    
    # Try to parse string as JSON if it looks like a list
    if isinstance(definitions, str) and definitions.strip().startswith('['):
        try:
            definitions = json.loads(definitions)
        except json.JSONDecodeError:
            pass
            
    def_text = ""
    if isinstance(definitions, list) and definitions:
        def_parts = []
        for d in definitions[:2]:
            if isinstance(d, dict):
                # Handle various key names for part of speech and meaning
                pos = d.get('pos', d.get('part', 'n.'))
                meaning = d.get('meaning', d.get('translation', ''))
                def_parts.append(f"{pos} {meaning}")
            elif isinstance(d, str):
                def_parts.append(d)
        def_text = "\n".join(def_parts)
    elif isinstance(definitions, str):
        def_text = definitions
    else:
        def_text = "（释义待补充）"
    
    
    prompt = f"""为单词 "{word}" ({phonetic}) 生成一张精简的学习卡片内容。

已知释义：
{def_text}

请生成以下内容（JSON格式）：
1. definition: 核心释义（如果有多个词性，用分号分隔，每个词性最多一个义项，总计不超过40字。例如："n. 跨度；范围；v. 跨越"）
2. memory_tip: 一个简短的记忆技巧（可以是词根拆解、谐音、联想等，30字以内）
3. example: 一个简单实用的英文例句（15词以内，带中文翻译）
4. common_phrases: 两个最常用的短语搭配（英文即可，用 | 分隔，总长度控制在25字符以内，越短越好）

返回格式：
{{
  "definition": "n. 跨度；范围；v. 跨越；持续",
  "memory_tip": "ad(去) + apt(合适) → 让自己去变得合适",
  "example": "The bridge spans the river.|这座桥横跨河流。",
  "common_phrases": "span of time|short span"
}}

注意：
- 内容要简洁，适合打印成卡片
- 记忆技巧可以是词根拆解、谐音、联想等，30字以内
- 例句适当高级，适合写作背诵，不要太过简单
- 如果有多个词性，一定要都包含。
- 例句用 | 分隔英文和中文
- common_phrases只返回英文，用|分隔
- 只返回JSON，不要其他内容"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位考研英语单词记忆专家，擅长提炼核心信息。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        
        import json
        content = response.choices[0].message.content.strip()
        
        # Clean markdown code blocks if present
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines)
            
        card_data = json.loads(content)
        return {"success": True, "card_data": card_data}
        
    except Exception as e:
        import traceback
        print(f"Error generating card: {e}")
        traceback.print_exc()
        
        # Safe fallback for definition text
        fallback_def = "暂无释义"
        if isinstance(definitions, list) and definitions:
            d = definitions[0]
            if isinstance(d, dict):
                fallback_def = f"{d.get('pos', 'n.')} {d.get('meaning', '')}"
            elif isinstance(d, str):
                fallback_def = d
        elif isinstance(definitions, str):
            fallback_def = definitions
            
        # Fallback
        return {
            "success": False,
            "card_data": {
                "definition": fallback_def,
                "memory_tip": "暂无记忆技巧",
                "example": f"This is an example of {word}.|这是一个例句。"
            }
        }


def generate_curriculum_content(title: str, subject: str, chapter_id: str) -> str:
    """Generate structured curriculum content using LLM."""
    
    # Map subject to Chinese name for better context
    subject_map = {
        "math": "管理类联考数学 (Mathematics)",
        "logic": "管理类联考逻辑 (Logic)",
        "english": "考研英语 (English)",
        "writing": "管理类联考写作 (Writing)"
    }
    subject_cn = subject_map.get(subject, subject)

    prompt = f"""
你是一位资深的考研/MEM 备考专家，擅长总结学习要点、提炼解题技巧和分析命题趋势。

请为以下章节生成一份 **极具深度和实战价值** 的学习笔记（Markdown 格式）：

*   **主题：** {title}
*   **学科：** {subject_cn}
*   **章节编号：** {chapter_id}

请严格按照以下 7 个部分进行编写，内容要干货满满，拒绝废话：

### 第一部分：核心定义（基础地基）
*   列出本章最关键的概念、公式、定理。
*   数学公式请务必使用 $LaTeX$ 格式（例如 $x^2 + y^2 = r^2$）。
*   如果有容易混淆的概念，请用 *斜体* 或 **加粗** 强调。

### 第二部分：核心考点（考试套路）
*   提炼 2-3 个最常考的题型或考点。
*   每个考点包含：
    *   **原理：** 一句话解释核心逻辑。
    *   **公式/结论：** 相关的秒杀公式或重要结论。
    *   **应用场景：** 什么样的题目会用到这个考点。

### 第三部分：真题逻辑演练（文字解析）
*   提供 2 个典型例题（最好改编自真题）。
*   **格式要求：**
    **【例题 X】** 题目内容...
    *   **文字解析：**
        1. 第一步思路...
        2. 第二步计算...
        3. 结论...
    *   (解析要像老师讲课一样，展示逻辑链条，不仅仅是列算式)

### 第四部分：避坑指南（考试心理）
*   列出考生在这一章最容易犯的 2-3 个错误。
*   提供对应的"防坑口诀"或记忆技巧。

### 第五部分：考情分析（情报局）
*   **难度星级：** (1-5星，例如 ⭐⭐⭐)
*   **考频指数：** (1-5星，例如 ⭐⭐⭐⭐⭐)
*   **命题趋势：** 简述近几年的考察风向（变难、变活、结合实事等）。

### 第六部分：思维导图（知识网）
*   请使用 `mermaid` 代码块生成本章的知识结构图。
*   方向使用 `mindmap` 或 `graph LR` 均可，力求结构清晰。
    ```mermaid
    mindmap
      root(({title}))
        核心概念
          ...
        考点一
          ...
    ```

### 第七部分：针对 MEM/MBA 的复习建议
*   结合在职考生的特点，给出 2-3 条高效复习建议。

**输出要求：**
1.  **只返回 Markdown 内容**，不要包含 YAML frontmatter (由后端处理)。
2.  内容长度控制在 800-1500 字，确保深度。
3.  语气要专业、犀利、干练，像一位经验丰富的辅导老师。
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位考研命题研究专家，擅长编写高质量的教辅材料。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating curriculum: {e}")
        return f"Error generation failed: {str(e)}"

if __name__ == "__main__":
    pass
