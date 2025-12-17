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


if __name__ == "__main__":
    # Test batch analyzer
    pass
