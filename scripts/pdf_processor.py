"""
PDF to Questions Processor
Converts PDF pages to images and uses LLM vision to extract questions.
"""
import os
import base64
import yaml
from pathlib import Path
from openai import OpenAI

# Load config
CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

llm_config = config.get("llm", {})

client = OpenAI(
    api_key=llm_config.get("api_key", ""),
    base_url=llm_config.get("base_url", "https://api.openai.com/v1")
)
MODEL = llm_config.get("model", "gpt-4o-mini")

EXTRACT_PROMPT = """你是一个专业的中文试卷OCR助手。请严格识别图片中的**中文文本**。

CRITICAL INSTRUCTION: Analyze the image pixel-by-pixel. Transcribe the text EXACTLY as it appears in the image. DO NOT TRANSLATE. DO NOT HALLUCINATE.
如果图片是中文试卷，必须输出中文。

识别任务：
1. 逐字识别图片中的所有题目内容。
2. 保持原始语言（中文）。绝对不要翻译成英文。
3. 提取每一道题：
   - 题号 (Number): 如 "1", "2", "26" 等
   - 题干 (Content): 必须是图片上的原始中文文本
   - 选项 (Options): 必须是图片上的原始中文选项
   - 科目 (Subject): math/logic/english/writing

输出格式 (JSON ONLY):
```json
{
  "questions": [
    {
      "number": "原始题号",
      "content": "图片上的原始中文题目内容...",
      "options": ["A. 原始选项", "B. 原始选项", "C. ..."],
      "subject": "math", 
      "note": "题目类型"
    }
  ],
  "page_type": "questions",
  "notes": "页面说明"
}
```

注意事项：
- **禁止翻译**：如果是中文题，Content和Options必须是中文。
- **禁止编造**：只识别图片上真实存在的文字。如果看不清，不要猜测。
- 如果图片是封面、目录或无题目，questions 返回空数组。
- 严格输出 JSON。"""


def encode_image(image_path: str) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_questions_from_image(image_path: str) -> dict:
    """Use LLM vision to extract questions from an image."""
    base64_image = encode_image(image_path)
    
    # Determine mime type
    ext = Path(image_path).suffix.lower()
    mime_type = "image/png" if ext == ".png" else "image/jpeg"
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACT_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4096
        )
        
        result_text = response.choices[0].message.content
        
        # Extract JSON from response
        import re
        import json
        
        # Try to find JSON in the response
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result_text)
        if json_match:
            result_text = json_match.group(1)
        
        # Try to find JSON object directly
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result_text = json_match.group(0)
        
        return json.loads(result_text)
        
    except Exception as e:
        return {"error": str(e), "questions": []}


def pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 150) -> list:
    """Convert PDF pages to images using pypdfium2 (cross-platform)."""
    import pypdfium2 as pdfium
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    pdf = pdfium.PdfDocument(pdf_path)
    image_paths = []
    
    for i, page in enumerate(pdf):
        # Render page to image
        bitmap = page.render(scale=dpi/72)  # 72 is default PDF DPI
        pil_image = bitmap.to_pil()
        
        # Save image
        image_path = os.path.join(output_dir, f"page_{i+1:03d}.png")
        pil_image.save(image_path)
        image_paths.append(image_path)
        print(f"Converted page {i+1}/{len(pdf)}")
    
    return image_paths


# Prompt for full PDF analysis (handles cross-page questions)
FULL_PDF_PROMPT = """你是一位资深的英语考研辅导专家。请分析这份完整的英语真题试卷（共{page_count}页）。

**重要说明**：
- 题目可能跨越多页，请仔细阅读所有页面后再进行分析
- 阅读理解的文章和题目可能分布在不同页面，请将它们整合在一起

请按照以下JSON格式返回分析结果：

```json
{{
  "exam_info": {{
    "year": "考试年份",
    "type": "考试类型（如：英语二）",
    "total_questions": "题目总数"
  }},
  "sections": [
    {{
      "section_name": "题型名称（如：完形填空、阅读理解Text1等）",
      "page_range": "所在页码范围",
      "questions": [
        {{
          "number": "题号",
          "content": "题目内容",
          "options": ["A. xxx", "B. xxx", "C. xxx", "D. xxx"],
          "answer": "正确答案（如有）",
          "passage": "相关文章段落（阅读理解需要）"
        }}
      ]
    }}
  ],
  "vocabulary_highlights": [
    {{
      "word": "核心词汇",
      "meaning": "释义",
      "context": "原文语境"
    }}
  ],
  "key_sentences": [
    {{
      "sentence": "重点长难句",
      "translation": "中文翻译",
      "source": "来源（如Text1第2段）"
    }}
  ]
}}
```

请确保：
1. 完整提取所有题目，不要遗漏
2. 阅读理解题请附带相关文章段落
3. 提取5-10个核心词汇和3-5个长难句
4. 返回纯JSON，不要有其他文字
"""


def analyze_pdf_direct(pdf_path: str) -> dict:
    """
    Analyze PDF by converting to images first, then sending all images to LLM.
    This is more compatible with OpenAI-compatible API proxies.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Dictionary with comprehensive analysis results
    """
    import json
    import re
    import tempfile
    import pypdfium2 as pdfium
    
    print(f"Analyzing PDF: {pdf_path}")
    
    # Convert PDF to images in memory
    pdf = pdfium.PdfDocument(pdf_path)
    page_count = len(pdf)
    print(f"Converting {page_count} pages to images...")
    
    # Build content array with all page images
    content = [
        {"type": "text", "text": FULL_PDF_PROMPT.format(page_count=page_count)}
    ]
    
    for i, page in enumerate(pdf):
        # Render page to image
        bitmap = page.render(scale=150/72)  # 150 DPI
        pil_image = bitmap.to_pil()
        
        # Convert to base64
        import io
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_base64}",
                "detail": "high"
            }
        })
        print(f"Added page {i+1}/{page_count}")
    
    try:
        print("Sending all pages to LLM for analysis...")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ],
            max_tokens=8192
        )
        
        result_text = response.choices[0].message.content
        print("Received response, parsing JSON...")
        print(f"Response preview: {result_text[:200]}...")
        
        # Extract JSON
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result_text)
        if json_match:
            result_text = json_match.group(1)
        
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result_text = json_match.group(0)
        
        return json.loads(result_text)
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        return {"error": f"JSON解析失败: {e}", "raw_response": result_text[:500] if 'result_text' in dir() else ""}
    except Exception as e:
        print(f"Analysis failed: {e}")
        return {"error": str(e)}


def analyze_full_pdf(image_paths: list, max_pages: int = 20) -> dict:
    """
    Analyze entire PDF by sending all page images to LLM at once.
    Handles cross-page questions like reading comprehension.
    
    Args:
        image_paths: List of image file paths (in order)
        max_pages: Maximum pages to send (to avoid token limits)
    
    Returns:
        Dictionary with comprehensive analysis results
    """
    # Limit pages to avoid token overflow
    if len(image_paths) > max_pages:
        print(f"Warning: Limiting to first {max_pages} pages")
        image_paths = image_paths[:max_pages]
    
    # Build content array with all images
    content = [
        {"type": "text", "text": FULL_PDF_PROMPT.format(page_count=len(image_paths))}
    ]
    
    for i, image_path in enumerate(image_paths):
        base64_image = encode_image(image_path)
        ext = Path(image_path).suffix.lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"
        
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{base64_image}",
                "detail": "high"
            }
        })
        print(f"Added page {i+1}/{len(image_paths)}")
    
    try:
        print("Sending to LLM for analysis...")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ],
            max_tokens=8192
        )
        
        result_text = response.choices[0].message.content
        print("Received response, parsing JSON...")
        
        # Extract JSON
        import re
        import json
        
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result_text)
        if json_match:
            result_text = json_match.group(1)
        
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result_text = json_match.group(0)
        
        return json.loads(result_text)
        
    except Exception as e:
        return {"error": str(e)}


def process_pdf(pdf_path: str, output_dir: str = None):
    """Process entire PDF: convert to images and extract questions."""
    pdf_path = Path(pdf_path)
    
    if output_dir is None:
        output_dir = pdf_path.parent / "pdf_images" / pdf_path.stem
    
    print(f"Processing: {pdf_path}")
    print(f"Output dir: {output_dir}")
    
    # Step 1: Convert PDF to images
    print("\n[1/2] Converting PDF to images...")
    image_paths = pdf_to_images(str(pdf_path), str(output_dir))
    print(f"Created {len(image_paths)} images")
    
    # Step 2: Extract questions from each image
    print("\n[2/2] Extracting questions with LLM vision...")
    all_questions = []
    
    for i, image_path in enumerate(image_paths):
        print(f"Processing image {i+1}/{len(image_paths)}...")
        result = extract_questions_from_image(image_path)
        
        if "error" in result:
            print(f"  Error: {result['error']}")
        elif result.get("questions"):
            print(f"  Found {len(result['questions'])} questions")
            for q in result["questions"]:
                q["source_page"] = i + 1
                all_questions.append(q)
        else:
            print(f"  Page type: {result.get('page_type', 'unknown')}")
    
    print(f"\n=== Total questions found: {len(all_questions)} ===")
    
    # Save results
    import json
    result_path = output_dir / "extracted_questions.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)
    print(f"Results saved to: {result_path}")
    
    return all_questions


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_processor.py <pdf_path>")
        print("Example: python pdf_processor.py 2025.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    process_pdf(pdf_path)
