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
    VOCABULARY_ARTICLE_PROMPT,
    BATCH_ANALYZE_PROMPT,
    VOCABULARY_FRONTMATTER_PROMPT,
    VOCABULARY_CARD_PROMPT
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
    
    
    
    
    prompt = VOCABULARY_CARD_PROMPT.format(word=word, phonetic=phonetic, def_text=def_text)

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
    
    from prompts import CURRICULUM_CONTENT_PROMPT

    # Map subject to Chinese name for better context
    subject_map = {
        "math": "管理类联考数学 (Mathematics)",
        "logic": "管理类联考逻辑 (Logic)",
        "english": "考研英语 (English)",
        "writing": "管理类联考写作 (Writing)"
    }
    subject_cn = subject_map.get(subject, subject)

    prompt = CURRICULUM_CONTENT_PROMPT.format(
        title=title,
        subject_cn=subject_cn,
        chapter_id=chapter_id
    )
    
    client = get_client()
    model = get_model()
    
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
