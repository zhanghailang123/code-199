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
