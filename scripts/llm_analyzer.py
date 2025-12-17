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


if __name__ == "__main__":
    # Test the analyzer
    test_question = """
    甲、乙两人分别从 A、B 两地同时出发，相向而行。甲的速度是乙的 1.5 倍。两人第一次相遇后继续前进，到达对方出发点后立即返回。问：两人第二次相遇时，甲走过的路程是乙的多少倍？
    A. 1.2  B. 1.5  C. 1.8  D. 2.0  E. 2.5
    """
    
    result = analyze_question(test_question)
    print(result)
