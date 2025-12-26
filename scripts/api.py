"""
MEM Study System - FastAPI Backend
Provides REST API for question and knowledge point CRUD operations.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import yaml
from pathlib import Path

# Configuration
CONTENT_DIR = Path(__file__).parent.parent / "content"
QUESTIONS_DIR = CONTENT_DIR / "questions"
KNOWLEDGE_DIR = CONTENT_DIR / "knowledge"
CURRICULUM_DIR = CONTENT_DIR / "curriculum"
VOCAB_DIR = CONTENT_DIR / "vocabulary"
PASSAGES_DIR = CONTENT_DIR / "passages"

# Create directories if they don't exist
for d in [QUESTIONS_DIR, KNOWLEDGE_DIR, CURRICULUM_DIR, VOCAB_DIR, PASSAGES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="MEM Study API",
    description="Backend API for managing exam questions and knowledge points",
    version="1.0.0"
)

# CORS for Vue frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://hailang0616.xyz",  # Production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== Data Models ======

class QuestionCreate(BaseModel):
    id: str
    source: str = "管理类联考"
    subject: str  # math, logic, english
    type: str = "choice"
    difficulty: int = 3
    knowledge_points: List[str] = []
    tags: List[str] = []
    content: str  # 题目内容
    options: str = ""  # 选项文本
    answer: str = ""
    explanation: str = ""

class QuestionResponse(BaseModel):
    id: str
    subject: str
    type: str
    difficulty: int
    raw: str  # Full markdown content

class KnowledgePointCreate(BaseModel):
    id: str
    title: str
    category: str  # math, logic, english
    importance: str = "medium"
    related: List[str] = []
    core_concept: str = ""
    common_types: str = ""
    pitfalls: str = ""

class UpdateContentRequest(BaseModel):
    content: str


# ====== Helper Functions ======

def generate_question_md(q: QuestionCreate) -> str:
    """Generate markdown content from question data."""
    frontmatter = {
        "id": q.id,
        "source": q.source,
        "subject": q.subject,
        "type": q.type,
        "difficulty": q.difficulty,
        "knowledge_points": q.knowledge_points,
        "tags": q.tags
    }
    
    yaml_content = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)
    
    md_content = f"""---
{yaml_content.strip()}
---

## 题目
{q.content}

## 选项
{q.options}

## 答案
{q.answer}

## 解析
{q.explanation}
"""
    return md_content


def generate_knowledge_md(kp: KnowledgePointCreate) -> str:
    """Generate markdown content from knowledge point data."""
    frontmatter = {
        "id": kp.id,
        "title": kp.title,
        "category": kp.category,
        "importance": kp.importance,
        "related": kp.related
    }
    
    yaml_content = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)
    
    md_content = f"""---
{yaml_content.strip()}
---

## 核心概念
{kp.core_concept}

## 常见题型
{kp.common_types}

## 易错点
{kp.pitfalls}
"""
    return md_content


def list_questions() -> List[dict]:
    """List all questions from the questions directory."""
    questions = []
    if QUESTIONS_DIR.exists():
        for file in QUESTIONS_DIR.glob("*.md"):
            questions.append({
                "id": file.stem,
                "path": str(file)
            })
    return questions


# ====== API Endpoints ======

@app.get("/")
def root():
    return {"message": "MEM Study API", "version": "1.0.0"}


@app.get("/api/questions")
def get_questions():
    """List all questions."""
    questions = list_questions()
    return {"questions": questions, "total": len(questions)}


@app.post("/api/questions")
def create_question(question: QuestionCreate):
    """Create a new question."""
    file_path = QUESTIONS_DIR / f"{question.id}.md"
    
    if file_path.exists():
        raise HTTPException(status_code=400, detail=f"Question {question.id} already exists")
    
    # Generate markdown
    md_content = generate_question_md(question)
    
    # Ensure directory exists
    QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write file
    file_path.write_text(md_content, encoding="utf-8")
    
    return {"message": "Question created successfully", "id": question.id, "path": str(file_path)}


@app.get("/api/questions/{question_id}")
def get_question(question_id: str):
    """Get a single question by ID."""
    file_path = QUESTIONS_DIR / f"{question_id}.md"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
    
    content = file_path.read_text(encoding="utf-8")
    return {"id": question_id, "raw": content}


@app.delete("/api/questions/{question_id}")
def delete_question(question_id: str):
    """Delete a question by ID."""
    file_path = QUESTIONS_DIR / f"{question_id}.md"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
    
    file_path.unlink()
    return {"message": f"Question {question_id} deleted successfully"}


@app.put("/api/questions/{question_id}")
def update_question(question_id: str, question: QuestionCreate):
    """
    Update an existing question.
    Overwrites the entire file content.
    """
    if question_id != question.id:
        raise HTTPException(status_code=400, detail="Path ID does not match body ID")
        
    file_path = QUESTIONS_DIR / f"{question_id}.md"
    
    # Check if exists (not strictly necessary but good for 404)
    if not file_path.exists():
         raise HTTPException(status_code=404, detail=f"Question {question_id} not found")

    # Generate markdown
    md_content = generate_question_md(question)
    
    # Write file
    file_path.write_text(md_content, encoding="utf-8")
    
    return {"message": "Question updated successfully", "id": question.id, "path": str(file_path)}


@app.put("/api/questions/{question_id}/content")
def update_question_content(question_id: str, request: UpdateContentRequest):
    """
    Update question raw content directly.
    """
    file_path = QUESTIONS_DIR / f"{question_id}.md"
    
    if not file_path.exists():
         raise HTTPException(status_code=404, detail=f"Question {question_id} not found")

    # Overwrite the file with new content
    file_path.write_text(request.content, encoding="utf-8")
    
    return {"message": "Question content updated successfully", "id": question_id}


@app.post("/api/knowledge")
def create_knowledge_point(kp: KnowledgePointCreate):
    """Create a new knowledge point."""
    category_dir = KNOWLEDGE_DIR / kp.category
    file_path = category_dir / f"{kp.id}.md"
    
    if file_path.exists():
        raise HTTPException(status_code=400, detail=f"Knowledge point {kp.id} already exists")
    
    # Generate markdown
    md_content = generate_knowledge_md(kp)
    
    # Ensure directory exists
    category_dir.mkdir(parents=True, exist_ok=True)
    
    # Write file
    file_path.write_text(md_content, encoding="utf-8")
    
    return {"message": "Knowledge point created successfully", "id": kp.id, "path": str(file_path)}


@app.put("/api/knowledge/{category}/{kp_id}")
def update_knowledge_point(category: str, kp_id: str, kp: KnowledgePointCreate):
    """
    Update an existing knowledge point.
    """
    if kp_id != kp.id:
         raise HTTPException(status_code=400, detail="Path ID does not match body ID")

    category_dir = KNOWLEDGE_DIR / category
    file_path = category_dir / f"{kp_id}.md"
    
    if not file_path.exists():
        # Try finding it if category changed? For now assume path matches
        raise HTTPException(status_code=404, detail="Knowledge point not found")
    
    # Generate markdown
    md_content = generate_knowledge_md(kp)
    
    # Write file
    file_path.write_text(md_content, encoding="utf-8")
    
    return {"message": "Knowledge point updated successfully", "id": kp.id, "path": str(file_path)}


@app.put("/api/knowledge/{category}/{kp_id}/content")
def update_knowledge_content(category: str, kp_id: str, request: UpdateContentRequest):
    """
    Update knowledge point raw content directly.
    """
    category_dir = KNOWLEDGE_DIR / category
    file_path = category_dir / f"{kp_id}.md"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Knowledge point not found")
    
    # Overwrite the file with new content
    file_path.write_text(request.content, encoding="utf-8")
    
    return {"message": "Knowledge point content updated successfully", "id": kp_id}


@app.get("/api/knowledge")
def get_knowledge_points():
    """List all knowledge points."""
    kps = []
    if KNOWLEDGE_DIR.exists():
        for category_dir in KNOWLEDGE_DIR.iterdir():
            if category_dir.is_dir():
                for file in category_dir.glob("*.md"):
                    kps.append({
                        "id": file.stem,
                        "category": category_dir.name,
                        "path": str(file)
                    })
    return {"knowledge_points": kps, "total": len(kps)}


@app.get("/api/knowledge/{category}/{kp_id}")
def get_knowledge_detail(category: str, kp_id: str):
    """Get a specific knowledge point by category and ID."""
    file_path = KNOWLEDGE_DIR / category / f"{kp_id}.md"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Knowledge point not found")
    
    content = file_path.read_text(encoding="utf-8")
    meta = parse_frontmatter(content)
    
    return {
        "id": kp_id,
        "category": category,
        "raw": content,
        "meta": meta
    }


# --- Vocabulary API ---
from typing import Optional, List, Dict, Any
from pathlib import Path
import yaml

class VocabularyItem(BaseModel):
    id: str
    word: str
    phonetic: Optional[str] = None
    tags: List[str] = []
    status: str = "learning" # not_started, learning, mastered
    definitions: List[Dict[str, Any]] = [] # [{part: "v.", text: "...", translation: "..."}]
    related_questions: List[str] = []
    content: Optional[str] = None # Markdown body

def parse_vocabulary_file(file_path: Path) -> Optional[VocabularyItem]:
    try:
        content = file_path.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                if frontmatter and 'id' in frontmatter and 'word' in frontmatter:
                    return VocabularyItem(
                        **frontmatter,
                        content=parts[2].strip()
                    )
        
        # Fallback: create basic item from filename
        word = file_path.stem  # filename without extension
        return VocabularyItem(
            id=f"vocab-{word.lower()}",
            word=word,
            phonetic=None,
            tags=[],
            status="learning",
            definitions=[],
            related_questions=[],
            content=content
        )
    except Exception as e:
        print(f"Error parsing vocabulary {file_path}: {e}")
    return None

@app.get("/api/vocabulary")
def list_vocabulary():
    vocab_dir = CONTENT_DIR / "vocabulary"
    items = []
    
    if not vocab_dir.exists():
        return {"items": []}
        
    # Walk all subject subdirectories
    for file_path in vocab_dir.rglob("*.md"):
        item = parse_vocabulary_file(file_path)
        if item:
            # Don't send full content in list view for performance
            item.content = None 
            items.append(item)
            
    return {"items": items}

@app.get("/api/vocabulary/{id}")
def get_vocabulary(id: str):
    # Search for the file in all subdirs
    vocab_dir = CONTENT_DIR / "vocabulary"
    found_path = None
    
    for file_path in vocab_dir.rglob(f"*.md"):
        # Check if ID in frontmatter matches (safest) or filename
        # For speed let's assume filename ~ ID or we parse.
        # Ideally we index this. For now, linear scan is okay for small sets.
        item = parse_vocabulary_file(file_path)
        if item and item.id == id:
            found_path = file_path
            return item
            
    if not found_path:
        raise HTTPException(status_code=404, detail="Vocabulary not found")

class CreateVocabularyRequest(BaseModel):
    id: str
    word: str
    category: str = "english" # Default folder
    auto_generate: bool = False # New flag

@app.post("/api/vocabulary")
def create_vocabulary(req: CreateVocabularyRequest):
    vocab_dir = CONTENT_DIR / "vocabulary" / req.category
    vocab_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = vocab_dir / f"{req.word}.md"
    if file_path.exists():
        raise HTTPException(status_code=400, detail="Word already exists")
    
    if req.auto_generate:
        print(f"Auto-generating article for {req.word}...")
        from llm_analyzer import generate_vocabulary_article
        content = generate_vocabulary_article(req.word)
        
        # Force overwrite ID to match system requirements
        # Use regex to replace id: ... with correct id
        import re
        content = re.sub(r'^id:\s*.*$', f'id: "{req.id}"', content, flags=re.MULTILINE)
    else:
        # Template
        content = f"""---
id: {req.id}
word: "{req.word}"
phonetic: ""
tags: []
status: "learning"
definitions:
  - part: ""
    text: ""
    translation: ""
related_questions: []
---

## 记忆法

## 例句

## 解析
"""
    file_path.write_text(content, encoding="utf-8")
    return {"success": True, "id": req.id}

class UpdateVocabularyRequest(BaseModel):
    content: str # Full raw content

@app.put("/api/vocabulary/{id}")
def update_vocabulary(id: str, req: UpdateVocabularyRequest):
    vocab_dir = CONTENT_DIR / "vocabulary"
    found_path = None
    
    # Find file
    for file_path in vocab_dir.rglob("*.md"):
        item = parse_vocabulary_file(file_path)
        if item and item.id == id:
            found_path = file_path
            break
    
    if not found_path:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
        
    final_content = req.content
    
    # Check if content has frontmatter
    if not final_content.startswith("---"):
        print(f"Frontmatter missing for {id}, generating with LLM...")
        from llm_analyzer import generate_vocabulary_frontmatter
        frontmatter = generate_vocabulary_frontmatter(final_content)
        final_content = frontmatter + final_content
        
    found_path.write_text(final_content, encoding="utf-8")
    return {"success": True, "id": id}


@app.post("/api/vocabulary/{id}/regenerate")
def regenerate_vocabulary(id: str):
    """
    Regenerate vocabulary content using LLM.
    """
    from llm_analyzer import generate_vocabulary_article
    
    vocab_dir = CONTENT_DIR / "vocabulary"
    found_path = None
    word = None
    
    # Find the file and extract the word
    for file_path in vocab_dir.rglob("*.md"):
        item = parse_vocabulary_file(file_path)
        if item and item.id == id:
            found_path = file_path
            word = item.word
            break
    
    if not found_path or not word:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    
    # Generate new content
    try:
        new_content = generate_vocabulary_article(word)
        
        # Ensure ID matches
        import re
        new_content = re.sub(r'^id:\s*.*$', f'id: "{id}"', new_content, flags=re.MULTILINE)
        
        # Save to file
        found_path.write_text(new_content, encoding="utf-8")
        
        return {"success": True, "id": id, "content": new_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")


class AnalyzeRequest(BaseModel):
    question_text: str
    subject: Optional[str] = None

@app.post("/api/analyze")
def analyze_question_endpoint(request: AnalyzeRequest):
    """
    Analyze a raw question using LLM.
    Returns structured question data (subject, answer, explanation, etc.)
    """
    from llm_analyzer import analyze_question
    
    if not request.question_text.strip():
        raise HTTPException(status_code=400, detail="Question text is required")
    
    result = analyze_question(request.question_text, subject=request.subject)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed"))
    
    return result


class AnalyzeImageRequest(BaseModel):
    image_base64: str
    subject: Optional[str] = None
    mime_type: str = "image/png"

@app.post("/api/analyze-image")
def analyze_image_endpoint(request: AnalyzeImageRequest):
    """
    Analyze a question from an image using LLM Vision.
    Returns structured question data with learning-focused explanations.
    """
    from llm_analyzer import analyze_question_with_image
    
    if not request.image_base64:
        raise HTTPException(status_code=400, detail="Image data is required")
    
    result = analyze_question_with_image(
        request.image_base64, 
        subject=request.subject,
        mime_type=request.mime_type
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Image analysis failed"))
    
    return result


class EnglishAnalyzeRequest(BaseModel):
    question_text: str

@app.post("/api/analyze-english")
def analyze_english_endpoint(request: EnglishAnalyzeRequest):
    """
    Analyze an English question with multi-dimensional analysis.
    Returns vocabulary, associated words, key sentences, similar examples, etc.
    """
    from llm_analyzer import analyze_english_question
    
    if not request.question_text.strip():
        raise HTTPException(status_code=400, detail="Question text is required")
    
    result = analyze_english_question(request.question_text)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed"))
    
    return result



# ====== Knowledge Graph Endpoint ======

import re

def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown content."""
    match = re.match(r'^---\r?\n([\s\S]*?)\r?\n---', content)
    if not match:
        return {}
    
    meta = {}
    current_key = None
    
    for line in match.group(1).split('\n'):
        if line.strip().startswith('- '):
            if current_key and current_key not in meta:
                meta[current_key] = []
            if current_key and isinstance(meta.get(current_key), list):
                meta[current_key].append(line.strip()[2:])
            continue
        
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            if value:
                meta[key] = value
    
    return meta


@app.get("/api/graph")
def get_knowledge_graph():
    """
    Generate knowledge graph data in Cytoscape.js format.
    Nodes: Questions and Knowledge Points
    Edges: Question -> Knowledge Point relationships
    """
    nodes = []
    edges = []
    kp_set = set()  # Track unique knowledge points
    
    # Process all questions
    if QUESTIONS_DIR.exists():
        for file in QUESTIONS_DIR.glob("*.md"):
            content = file.read_text(encoding="utf-8")
            meta = parse_frontmatter(content)
            
            q_id = file.stem
            subject = 'math' if 'math' in q_id else 'logic' if 'logic' in q_id else 'english'
            
            # Add question node
            nodes.append({
                "data": {
                    "id": q_id,
                    "label": q_id.split('-')[-1].upper(),  # e.g., "Q01"
                    "type": "question",
                    "subject": subject,
                    "difficulty": meta.get("difficulty", 3)
                }
            })
            
            # Process knowledge points
            kps = meta.get("knowledge_points", [])
            if isinstance(kps, list):
                for kp in kps:
                    kp_id = f"kp_{kp}"
                    kp_set.add((kp_id, kp, subject))
                    
                    # Add edge
                    edges.append({
                        "data": {
                            "id": f"{q_id}_to_{kp_id}",
                            "source": q_id,
                            "target": kp_id
                        }
                    })
    
    # Add knowledge point nodes
    for kp_id, kp_name, subject in kp_set:
        nodes.append({
            "data": {
                "id": kp_id,
                "label": kp_name,
                "type": "knowledge",
                "subject": subject
            }
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "questions": len([n for n in nodes if n["data"]["type"] == "question"]),
            "knowledge_points": len(kp_set)
        }
    }


# ====== Curriculum Endpoints ======

CURRICULUM_DIR = CONTENT_DIR / "curriculum"

@app.get("/api/curriculum")
def get_curriculum():
    """Get all curriculum chapters grouped by subject."""
    chapters = []
    
    if CURRICULUM_DIR.exists():
        for subject_dir in CURRICULUM_DIR.iterdir():
            if subject_dir.is_dir():
                for file in subject_dir.glob("*.md"):
                    content = file.read_text(encoding="utf-8")
                    meta = parse_frontmatter(content)
                    
                    chapters.append({
                        "id": meta.get("id", file.stem),
                        "title": meta.get("title", file.stem),
                        "subject": meta.get("subject", subject_dir.name),
                        "order": int(meta.get("order", 99)),
                        "status": meta.get("status", "not_started"),
                        "estimated_hours": int(meta.get("estimated_hours", 0)),
                        "knowledge_points": meta.get("knowledge_points", []),
                        "related_questions": meta.get("related_questions", []),
                        "path": str(file)
                    })
    
    # Sort by subject then order
    chapters.sort(key=lambda x: (x["subject"], x["order"]))
    
    return {
        "chapters": chapters,
        "total": len(chapters),
        "by_subject": {
            "math": len([c for c in chapters if c["subject"] == "math"]),
            "logic": len([c for c in chapters if c["subject"] == "logic"]),
            "english": len([c for c in chapters if c["subject"] == "english"])
        }
    }


@app.get("/api/curriculum/{chapter_id}")
def get_chapter(chapter_id: str):
    """Get a single chapter by ID."""
    if CURRICULUM_DIR.exists():
        for subject_dir in CURRICULUM_DIR.iterdir():
            if subject_dir.is_dir():
                for file in subject_dir.glob("*.md"):
                    content = file.read_text(encoding="utf-8")
                    meta = parse_frontmatter(content)
                    
                    if meta.get("id") == chapter_id or file.stem == chapter_id:
                        return {
                            "id": meta.get("id", file.stem),
                            "raw": content,
                            "meta": meta
                        }
    
    raise HTTPException(status_code=404, detail=f"Chapter {chapter_id} not found")


class UpdateStatusRequest(BaseModel):
    status: str  # not_started, in_progress, completed

@app.put("/api/curriculum/{chapter_id}/status")
def update_chapter_status(chapter_id: str, request: UpdateStatusRequest):
    """Update chapter learning status."""
    if CURRICULUM_DIR.exists():
        for subject_dir in CURRICULUM_DIR.iterdir():
            if subject_dir.is_dir():
                for file in subject_dir.glob("*.md"):
                    content = file.read_text(encoding="utf-8")
                    meta = parse_frontmatter(content)
                    
                    if meta.get("id") == chapter_id or file.stem == chapter_id:
                        # Update status in frontmatter
                        new_content = content.replace(
                            f"status: {meta.get('status', 'not_started')}",
                            f"status: {request.status}"
                        )
                        file.write_text(new_content, encoding="utf-8")
                        return {"message": "Status updated", "status": request.status}
    
    raise HTTPException(status_code=404, detail=f"Chapter {chapter_id} not found")

# 
@app.put("/api/curriculum/{chapter_id}/content")
def update_chapter_content(chapter_id: str, request: UpdateContentRequest):
    """Update chapter raw content."""
    if CURRICULUM_DIR.exists():
        for subject_dir in CURRICULUM_DIR.iterdir():
            if subject_dir.is_dir():
                for file in subject_dir.glob("*.md"):
                    content = file.read_text(encoding="utf-8")
                    meta = parse_frontmatter(content)
                    
                    if meta.get("id") == chapter_id or file.stem == chapter_id:
                        # Overwrite the file with new content
                        file.write_text(request.content, encoding="utf-8")
                        return {"message": "Content updated"}
    
    raise HTTPException(status_code=404, detail=f"Chapter {chapter_id} not found")


# ====== PDF Upload Endpoints ======

from fastapi import File, UploadFile
import base64
import shutil

PDF_IMAGES_DIR = Path(__file__).parent.parent / "pdf_images"

@app.post("/api/pdf/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload PDF and convert to images."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    # Save uploaded PDF
    pdf_name = Path(file.filename).stem
    pdf_dir = PDF_IMAGES_DIR / pdf_name
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_path = pdf_dir / file.filename
    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Convert to images using pypdfium2
    try:
        import pypdfium2 as pdfium
        
        pdf = pdfium.PdfDocument(str(pdf_path))
        image_paths = []
        
        for i, page in enumerate(pdf):
            bitmap = page.render(scale=150/72)  # 150 DPI
            pil_image = bitmap.to_pil()
            
            image_path = pdf_dir / f"page_{i+1:03d}.png"
            pil_image.save(str(image_path))
            image_paths.append(f"page_{i+1:03d}.png")
        
        return {
            "success": True,
            "pdf_name": pdf_name,
            "total_pages": len(image_paths),
            "images": image_paths
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF conversion failed: {str(e)}")


@app.get("/api/pdf/list")
def list_pdfs():
    """List all uploaded PDFs and their images."""
    pdfs = []
    
    if PDF_IMAGES_DIR.exists():
        for pdf_dir in PDF_IMAGES_DIR.iterdir():
            if pdf_dir.is_dir():
                images = sorted([f.name for f in pdf_dir.glob("*.png")])
                pdfs.append({
                    "name": pdf_dir.name,
                    "images": images,
                    "total": len(images)
                })
    
    return {"pdfs": pdfs}


@app.get("/api/pdf/{pdf_name}/image/{image_name}")
def get_pdf_image(pdf_name: str, image_name: str):
    """Get a PDF page image as base64."""
    image_path = PDF_IMAGES_DIR / pdf_name / image_name
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    return {"image": image_data, "name": image_name}


class AnalyzeImageRequest(BaseModel):
    pdf_name: str
    image_name: str

@app.post("/api/pdf/analyze-image")
def analyze_pdf_image(request: AnalyzeImageRequest):
    """Analyze a PDF page image with LLM vision."""
    from pdf_processor import extract_questions_from_image
    
    image_path = PDF_IMAGES_DIR / request.pdf_name / request.image_name
    
    print(f"DEBUG: Analyzing image: {image_path}")  # Debug print
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    result = extract_questions_from_image(str(image_path))
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


class AnalyzeFullPdfRequest(BaseModel):
    pdf_name: str

@app.post("/api/pdf/analyze-full")
def analyze_full_pdf_endpoint(request: AnalyzeFullPdfRequest):
    """
    Analyze entire PDF at once by sending PDF file directly to LLM.
    More efficient - no image conversion needed.
    """
    from pdf_processor import analyze_pdf_direct, analyze_full_pdf
    
    # Use project root directory
    project_root = Path(__file__).parent.parent
    pdf_path = project_root / f"{request.pdf_name}.pdf"
    
    print(f"DEBUG: Looking for PDF at: {pdf_path}")
    print(f"DEBUG: PDF exists: {pdf_path.exists()}")
    
    if pdf_path.exists():
        # Direct PDF analysis (more efficient)
        print(f"✅ Found PDF, analyzing directly: {pdf_path}")
        result = analyze_pdf_direct(str(pdf_path))
        
        # If direct analysis failed, fallback to image-based
        if result.get("fallback_needed"):
            pdf_dir = PDF_IMAGES_DIR / request.pdf_name
            if pdf_dir.exists():
                image_files = sorted(pdf_dir.glob("page_*.png"))
                if image_files:
                    print("Using image-based fallback...")
                    result = analyze_full_pdf([str(f) for f in image_files])
    else:
        # Fallback: use pre-converted images
        pdf_dir = PDF_IMAGES_DIR / request.pdf_name
        
        if not pdf_dir.exists():
            raise HTTPException(status_code=404, detail=f"PDF not found: {request.pdf_name}")
        
        image_files = sorted(pdf_dir.glob("page_*.png"))
        
        if not image_files:
            raise HTTPException(status_code=404, detail="No images found for this PDF")
        
        print(f"Using image-based analysis: {len(image_files)} pages")
        result = analyze_full_pdf([str(f) for f in image_files])
    
    if "error" in result and not result.get("fallback_needed"):
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


class BatchImportRequest(BaseModel):
    questions: List[dict]

@app.post("/api/pdf/batch-import")
def batch_import_questions(request: BatchImportRequest):
    """
    Batch analyze and import multiple questions.
    """
    from llm_analyzer import batch_analyze_questions
    
    if not request.questions:
        return {"success": True, "results": []}
        
    # Analyze questions
    analyzed_data = batch_analyze_questions(request.questions)
    
    results = []
    
    # Process and save each question
    import datetime
    
    for item in analyzed_data:
        if "error" in item:
            results.append({"success": False, "error": item["error"], "number": item.get("original_number")})
            continue
            
        try:
            # Create question object similar to generate_question_md input
            q_id = f"{datetime.datetime.now().year}-{item.get('subject', 'math')}-q{int(hash(item.get('content')) % 10000):04d}"
            
            # Map analyzed data to markdown structure
            # (Reusing logic from generate_question_md would be better but simple construction here is faster)
            
            # Helper to create markdown
            md = f"""---
id: {q_id}
difficulty: {item.get('difficulty', 3)}
subject: {item.get('subject', 'math')}
knowledge_points:
"""
            for kp in item.get('knowledge_points', []):
                md += f"  - {kp}\n"
                
            md += f"""tags:
"""
            for tag in item.get('tags', []):
                md += f"  - {tag}\n"
                
            md += f"""---

## 题目
{item.get('content')}

## 选项
{item.get('options')}

## 答案
{item.get('answer')}

## 解析
{item.get('explanation')}
"""
            
            # Save file
            file_path = QUESTIONS_DIR / f"{q_id}.md"
            QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
            
            # Avoid overwriting
            counter = 1
            while file_path.exists():
                file_path = QUESTIONS_DIR / f"{q_id}_{counter}.md"
                counter += 1
                
            file_path.write_text(md, encoding="utf-8")
            
            results.append({
                "success": True, 
                "number": item.get("original_number"),
                "id": q_id,
                "path": str(file_path)
            })
            
        except Exception as e:
            results.append({
                "success": False, 
                "error": str(e),
                "number": item.get("original_number")
            })
            
    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    print("Starting MEM Study API on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
