<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
// import { marked } from 'marked' // Removed
import { API_BASE, handleUploadImages } from '../config/api.js'
import MarkdownEditor from '../components/MarkdownEditor.vue'

// ByteMD Imports for Viewer
import { Viewer } from '@bytemd/vue-next'
import gfm from '@bytemd/plugin-gfm'
import highlight from '@bytemd/plugin-highlight'
import math from '@bytemd/plugin-math'
import gemoji from '@bytemd/plugin-gemoji'
import breaks from '@bytemd/plugin-breaks'
import mermaid from '@bytemd/plugin-mermaid'
import 'bytemd/dist/index.css'
import 'highlight.js/styles/github-dark.css' 
import 'katex/dist/katex.css'

// Custom plugin to rewrite relative /assets/ URLs for images
const imageRewritePlugin = () => ({
  viewerEffect({ el }) {
    if (!el) return
    const imgs = el.querySelectorAll('img');
    imgs.forEach(img => {
      const src = img.getAttribute('src');
      if (src && src.startsWith('/assets/')) {
        img.setAttribute('src', `${API_BASE}${src}`);
      }
    });
  }
});

const plugins = [
  gfm(),
  breaks(),
  highlight(),
  math(),
  gemoji(),
  mermaid(),
  imageRewritePlugin(),
]

const router = useRouter()
const loading = ref(true)
const error = ref('')
const chapters = ref([])
const bySubject = ref({})
const selectedChapter = ref(null)
const chapterContent = ref(null) // This will now hold raw markdown
const activeSubject = ref('all')
const activeType = ref('all')  // Add type filter
const isEditing = ref(false)
const saving = ref(false)

// Create Modal State
const showCreateModal = ref(false)
const creating = ref(false)
const autoGenerateOnCreate = ref(true) // New: auto-generate after creation
const newChapter = ref({
  id: '',
  title: '',
  subject: 'math',
  type: 'topic',
  description: ''
})
const newChapterImages = ref([])
const newChapterImagePreviews = ref([])

function handleNewChapterImagePaste(event) {
  const items = event.clipboardData?.items
  if (!items) return
  
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) {
        newChapterImages.value.push(file)
        const reader = new FileReader()
        reader.onload = (e) => {
          newChapterImagePreviews.value.push(e.target.result)
        }
        reader.readAsDataURL(file)
        event.preventDefault()
      }
      break
    }
  }
}

function removeNewChapterImage(idx) {
  newChapterImages.value.splice(idx, 1)
  newChapterImagePreviews.value.splice(idx, 1)
}

function clearNewChapterImages() {
  newChapterImages.value = []
  newChapterImagePreviews.value = []
}

// Global paste listener when create modal is open
function globalPasteHandler(event) {
  // Only capture paste if modal is open and auto-generate is enabled
  if (!showCreateModal.value || !autoGenerateOnCreate.value) return
  
  handleNewChapterImagePaste(event)
}

// Watch modal open/close to register/unregister global paste listener
watch(showCreateModal, (isOpen) => {
  if (isOpen) {
    document.addEventListener('paste', globalPasteHandler)
  } else {
    document.removeEventListener('paste', globalPasteHandler)
  }
})

// Auto-generate chapter ID from title
function generateChapterId(title, subject) {
  if (!title) return ''
  // Use timestamp for unique ID to avoid conflicts
  return Date.now().toString()
}

// Watch title to auto-fill ID
import { watch } from 'vue'
watch(() => newChapter.value.title, (newTitle) => {
  // Only auto-fill if ID is empty or was auto-generated
  if (!newChapter.value.id || /^\d{3}$/.test(newChapter.value.id)) {
    newChapter.value.id = generateChapterId(newTitle, newChapter.value.subject)
  }
})
watch(() => newChapter.value.subject, (newSubject) => {
  if (!newChapter.value.id || /^\d{3}$/.test(newChapter.value.id)) {
    newChapter.value.id = generateChapterId(newChapter.value.title, newSubject)
  }
})

async function createChapter() {
  if (!newChapter.value.id || !newChapter.value.title) return
  
  const shouldAutoGenerate = autoGenerateOnCreate.value
  const chapterData = { ...newChapter.value }
  
  // Close modal immediately
  showCreateModal.value = false
  creating.value = true
  
  try {
    const res = await fetch(`${API_BASE}/api/curriculum`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(chapterData)
    })
    
    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || '创建失败')
    }
    
    const successData = await res.json()
    // Sanitize ID: remove any quotes that might have been returned or entered
    const newId = String(successData.id).replace(/['"]/g, '').trim()
    
    // Reset form
    newChapter.value = { id: '', title: '', subject: 'math', type: 'topic', description: '' }
    const savedImages = [...newChapterImages.value]
    clearNewChapterImages()
    
    await loadCurriculum()
    
    // Auto-open the new chapter
    console.log('[Curriculum] Looking for new chapter ID:', newId)
    
    // Robust lookup: ensure string comparison and handle potential delays
    let createdChapter = chapters.value.find(c => String(c.id).trim() === newId)
    
    // Fallback: if not found in list (e.g. index delay), construct temp object to allow generation
    if (!createdChapter) {
        console.warn('[Curriculum] Chapter not found in list after refresh, using temp object')
        createdChapter = {
            id: newId,
            ...chapterData
        }
    }
    
    if (createdChapter) {
        selectedChapter.value = createdChapter
        chapterContent.value = '' // Reset to empty string to avoid Editor crash
        isEditing.value = true
        
        // Auto-generate if checkbox was checked
        if (shouldAutoGenerate) {
            console.log('[Curriculum] Auto-generate enabled, starting generation...')
            isGenerating.value = true
            try {
                // Convert images to base64 if provided
                let imagesBase64 = []
                if (savedImages.length > 0) {
                  imagesBase64 = await Promise.all(
                    savedImages.map(img => {
                      return new Promise((resolve) => {
                        const reader = new FileReader()
                        reader.onload = (e) => {
                          const base64 = e.target.result.split(',')[1]
                          resolve(base64)
                        }
                        reader.readAsDataURL(img)
                      })
                    })
                  )
                }
                
                const genRes = await fetch(`${API_BASE}/api/curriculum/${newId}/generate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        title: chapterData.title, 
                        subject: chapterData.subject, 
                        images_base64: imagesBase64.length > 0 ? imagesBase64 : null 
                    })
                })
                console.log('[Curriculum] Generation response status:', genRes.status)
                if (genRes.ok) {
                    console.log('[Curriculum] Generation successful, loading chapter...')
                    // Reload specific chapter to get content
                    await loadChapter(createdChapter)
                    isEditing.value = false // Show preview
                } else {
                    const err = await genRes.json()
                    alert('AI 生成失败: ' + (err.detail || '未知错误'))
                }
            } catch (e) {
                alert('AI 生成失败: ' + e.message)
            } finally {
                isGenerating.value = false
            }
        } else {
            // Only load if it's a real object from list, otherwise might fail if file not ready?
            // Actually API created it so it should be loadable by ID
            await loadChapter(createdChapter)
        }
    }
    
  } catch (e) {
    alert(e.message)
  } finally {
    creating.value = false
  }
}

const filteredChapters = computed(() => {
  let filtered = chapters.value
  
  // Filter by subject
  if (activeSubject.value !== 'all') {
    filtered = filtered.filter(c => c.subject === activeSubject.value)
  }
  
  // Filter by type
  if (activeType.value !== 'all') {
    filtered = filtered.filter(c => c.type === activeType.value)
  }
  
  return filtered
})

const statusLabels = {
  not_started: { text: '未开始', color: 'bg-zinc-800 text-zinc-400 border-zinc-700' },
  in_progress: { text: '进行中', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  completed: { text: '已完成', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' }
}

const subjectLabels = {
  math: { text: '数学', color: 'text-red-400 bg-red-500/10 border-red-500/20' },
  logic: { text: '逻辑', color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' },
  english: { text: '英语', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
  soft_exam_senior: { text: '软考高级', color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20' }
}

async function loadCurriculum() {
  loading.value = true
  error.value = ''
  
  try {
    const res = await fetch(`${API_BASE}/api/curriculum`)
    if (!res.ok) throw new Error('无法加载课程')
    
    const data = await res.json()
    chapters.value = data.chapters
    bySubject.value = data.by_subject
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function loadChapter(chapter) {
  selectedChapter.value = chapter
  chapterContent.value = '' // Reset to empty string instead of null to prevent Editor crash
  isEditing.value = false // Default to view mode
  
  try {
    const res = await fetch(`${API_BASE}/api/curriculum/${chapter.id}`)
    if (!res.ok) throw new Error('无法加载章节')
    
    const data = await res.json()
    
    // Store FULL raw content including frontmatter for editing
    chapterContent.value = data.raw || ''
  } catch (e) {
    error.value = e.message
  }
}

const isGenerating = ref(false)
const uploadedImages = ref([])
const imagePreviews = ref([])

function handleImageUpload(event) {
  const files = Array.from(event.target.files)
  if (!files.length) return
  
  files.forEach(file => {
    uploadedImages.value.push(file)
    const reader = new FileReader()
    reader.onload = (e) => {
      imagePreviews.value.push(e.target.result)
    }
    reader.readAsDataURL(file)
  })
}

function removeUploadedImage(idx) {
  uploadedImages.value.splice(idx, 1)
  imagePreviews.value.splice(idx, 1)
}

function clearImages() {
  uploadedImages.value = []
  imagePreviews.value = []
}

async function generateWithAI() {
  if (!selectedChapter.value) return

  isGenerating.value = true
  try {
    let imagesBase64 = []
    
    // Convert images to base64 if provided
    if (uploadedImages.value.length > 0) {
      imagesBase64 = await Promise.all(
        uploadedImages.value.map(img => {
          return new Promise((resolve) => {
            const reader = new FileReader()
            reader.onload = (e) => {
              const base64 = e.target.result.split(',')[1]
              resolve(base64)
            }
            reader.readAsDataURL(img)
          })
        })
      )
    }
    
    const res = await fetch(`${API_BASE}/api/curriculum/${selectedChapter.value.id}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: selectedChapter.value.title,
        subject: selectedChapter.value.subject,
        images_base64: imagesBase64.length > 0 ? imagesBase64 : null
      })
    })
    
    if (res.ok) {
      await loadChapter(selectedChapter.value)
      isEditing.value = false
      clearImages() // Clear images after successful generation
    } else {
      const err = await res.json()
      throw new Error(err.detail || '生成失败')
    }
  } catch (e) {
    alert('生成失败: ' + e.message)
  } finally {
    isGenerating.value = false
  }
}

async function saveChapter() {
  if (!selectedChapter.value || !chapterContent.value) return
  
  saving.value = true
  try {
    const res = await fetch(`${API_BASE}/api/curriculum/${selectedChapter.value.id}/content`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        content: chapterContent.value,
        title: selectedChapter.value.title  // Include updated title
      })
    })
    
    if (!res.ok) throw new Error('保存失败')
    
    isEditing.value = false
    // Refresh
    loadChapter(selectedChapter.value)
    
  } catch (e) {
    alert('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}

function closeDetail() {
  selectedChapter.value = null
  chapterContent.value = null
  isEditing.value = false
}

async function deleteChapter() {
  if (!selectedChapter.value) return
  
  const chapterTitle = selectedChapter.value.title || selectedChapter.value.id
  if (!confirm(`确定要删除章节 "${chapterTitle}" 吗？\n\n此操作不可恢复！`)) {
    return
  }
  
  try {
    const res = await fetch(`${API_BASE}/api/curriculum/${selectedChapter.value.id}`, {
      method: 'DELETE'
    })
    
    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || '删除失败')
    }
    
    // Close detail and refresh list
    closeDetail()
    await loadCurriculum()
    
  } catch (e) {
    alert('删除失败: ' + e.message)
  }
}

// Delete chapter by ID (for list view)
async function deleteChapterById(chapterId, chapterTitle) {
  if (!confirm(`确定要删除章节 "${chapterTitle || chapterId}" 吗？\n\n此操作不可恢复！`)) {
    return
  }
  
  try {
    const res = await fetch(`${API_BASE}/api/curriculum/${chapterId}`, {
      method: 'DELETE'
    })
    
    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || '删除失败')
    }
    
    await loadCurriculum()
    
  } catch (e) {
    alert('删除失败: ' + e.message)
  }
}

// Handle Custom Link Clicks (Delegate)
function handleEditorClick(e) {
  // Unused for now
}

// Pre-process markdown to inject raw HTML spans for question links
function renderWithLinks(mdContent) {
  if (!mdContent) return ''
  
  // Regex replace [[id]] with HTML span for question linking
  // ByteMD Viewer renders raw HTML by default.
  return mdContent.replace(/\[\[([^\]]+)\]\]/g, (match, id) => {
    return `<span class="question-link" data-question-id="${id}">${id}</span>`
  })
}

// Handle clicks on content area (event delegation for question links)
function handleContentClick(event) {
  const target = event.target
  if (target.classList.contains('question-link')) {
    const questionId = target.dataset.questionId
    if (questionId) {
      // Close the modal first
      closeDetail()
      // Navigate to question detail
      router.push({ name: 'question', params: { id: questionId } })
    }
  }
}

// Parse markdown content for rich view
const parsedChapter = computed(() => {
  if (!chapterContent.value) return null
  
  // Basic frontmatter parsing
  const text = chapterContent.value
  const fmMatch = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/)
  
  let content = text
  if (fmMatch) {
    content = fmMatch[2]
  }
  
  // Split into Main Sections by H2 headers
  const sections = {}
  
  // Split by lines starting with "## "
  const lines = content.split(/\r?\n/)
  let currentSection = null
  let currentBody = []
  
  for (const line of lines) {
    if (line.startsWith('## ')) {
      // Save previous section
      if (currentSection) {
        sections[currentSection] = currentBody.join('\n').trim()
      }
      // Start new section
      currentSection = line.replace('## ', '').trim()
      currentBody = []
    } else if (currentSection) {
      currentBody.push(line)
    }
  }
  
  // Save last section
  if (currentSection) {
    sections[currentSection] = currentBody.join('\n').trim()
  }
  
  // Fallback content (Markdown, not HTML)
  const fullContent = content
  
  return {
    sections,
    fullContent // Renamed from fullHtml
  }
})

onMounted(() => {
  loadCurriculum()
})
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <header class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-3xl font-extrabold text-white">📚 学习路径</h1>
        <p class="text-zinc-500 mt-1">系统化学习，逐章突破</p>
      </div>
      <div class="flex gap-3">
        <button @click="showCreateModal = true" class="btn bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700">➕ 新增章节</button>
        <button @click="loadCurriculum" class="btn btn-primary" :disabled="loading">🔄 刷新</button>
      </div>
    </header>

    <!-- ... (Progress and Tabs remain same) ... -->
    <!-- Progress Bar -->
    <div class="card p-6 mb-8 border border-white/5 bg-zinc-900/50">
       <!-- ... content same ... -->
       <div class="flex justify-between items-center mb-3">
        <span class="font-semibold text-zinc-300">总体进度</span>
        <span class="text-sm text-zinc-500 font-mono">{{ (chapters.length > 0) ? Math.round((chapters.filter(c => c.status === 'completed').length / chapters.length) * 100) : 0 }}%</span>
      </div>
      <div class="h-2 bg-zinc-800 rounded-full overflow-hidden">
        <div class="h-full bg-gradient-to-r from-blue-600 to-indigo-500 transition-all duration-500 shadow-[0_0_10px_rgba(59,130,246,0.3)]"
             :style="{ width: ((chapters.length > 0) ? Math.round((chapters.filter(c => c.status === 'completed').length / chapters.length) * 100) : 0) + '%' }"></div>
      </div>
       <!-- ... -->
    </div>
    
     <!-- Filter Tabs -->
    <div class="flex gap-2 mb-6 border-b border-white/5 pb-4">
      <button @click="activeSubject = 'all'" class="px-4 py-2 rounded-lg font-medium transition-all text-sm" :class="activeSubject === 'all' ? 'bg-zinc-800 text-white shadow-sm ring-1 ring-white/10' : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/5'">全部</button>
      <button @click="activeSubject = 'math'" class="px-4 py-2 rounded-lg font-medium transition-all text-sm" :class="activeSubject === 'math' ? 'bg-red-500/10 text-red-400 ring-1 ring-red-500/20' : 'text-zinc-500 hover:text-red-400 hover:bg-red-500/5'">数学</button>
      <button @click="activeSubject = 'logic'" class="px-4 py-2 rounded-lg font-medium transition-all text-sm" :class="activeSubject === 'logic' ? 'bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20' : 'text-zinc-500 hover:text-amber-400 hover:bg-amber-500/5'">逻辑</button>
      <button @click="activeSubject = 'english'" class="px-4 py-2 rounded-lg font-medium transition-all text-sm" :class="activeSubject === 'english' ? 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20' : 'text-zinc-500 hover:text-emerald-400 hover:bg-emerald-500/5'">英语</button>
      <button @click="activeSubject = 'soft_exam_senior'" class="px-4 py-2 rounded-lg font-medium transition-all text-sm" :class="activeSubject === 'soft_exam_senior' ? 'bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/20' : 'text-zinc-500 hover:text-cyan-400 hover:bg-cyan-500/5'">软考高级</button>
    </div>
    
    <!-- Type Filter Tabs -->
    <div class="flex gap-2 mb-6 pb-4">
      <span class="text-xs text-zinc-500 self-center mr-2">类型筛选:</span>
      <button @click="activeType = 'all'" class="px-3 py-1.5 rounded-lg font-medium transition-all text-xs" :class="activeType === 'all' ? 'bg-zinc-800 text-white shadow-sm ring-1 ring-white/10' : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/5'">全部</button>
      <button @click="activeType = 'topic'" class="px-3 py-1.5 rounded-lg font-medium transition-all text-xs" :class="activeType === 'topic' ? 'bg-blue-500/10 text-blue-400 ring-1 ring-blue-500/20' : 'text-zinc-500 hover:text-blue-400 hover:bg-blue-500/5'">知识点讲解</button>
      <button @click="activeType = 'practice'" class="px-3 py-1.5 rounded-lg font-medium transition-all text-xs" :class="activeType === 'practice' ? 'bg-purple-500/10 text-purple-400 ring-1 ring-purple-500/20' : 'text-zinc-500 hover:text-purple-400 hover:bg-purple-500/5'">习题训练</button>
      <button @click="activeType = 'writing'" class="px-3 py-1.5 rounded-lg font-medium transition-all text-xs" :class="activeType === 'writing' ? 'bg-pink-500/10 text-pink-400 ring-1 ring-pink-500/20' : 'text-zinc-500 hover:text-pink-400 hover:bg-pink-500/5'">英文作文</button>
    </div>

    <!-- Chapter List -->
    <div class="grid gap-4">
      <div v-if="loading" class="text-center py-12">
        <div class="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p class="text-zinc-500">加载课程中...</p>
      </div>
      
      <div v-else-if="filteredChapters.length === 0" class="text-center py-12 text-zinc-500">
        暂无课程内容
      </div>

      <div v-else
           v-for="chapter in filteredChapters" 
           :key="chapter.id"
           class="card p-5 hover:bg-zinc-900/40 transition-all border border-white/5 group relative overflow-hidden">
           
        <!-- Background Gradient based on subject -->
        <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
             :class="{
               'bg-gradient-to-r from-red-500/5 via-transparent to-transparent': chapter.subject === 'math',
               'bg-gradient-to-r from-amber-500/5 via-transparent to-transparent': chapter.subject === 'logic',
               'bg-gradient-to-r from-emerald-500/5 via-transparent to-transparent': chapter.subject === 'english',
               'bg-gradient-to-r from-cyan-500/5 via-transparent to-transparent': chapter.subject === 'soft_exam_senior'
             }"></div>

        <div class="relative flex items-center gap-4">
          <!-- Subject Icon -->
          <div class="w-12 h-12 rounded-xl flex items-center justify-center text-xl border border-white/5 shadow-inner"
               :class="{
                 'bg-zinc-900 text-red-500': chapter.subject === 'math',
                 'bg-zinc-900 text-amber-500': chapter.subject === 'logic',
                 'bg-zinc-900 text-emerald-500': chapter.subject === 'english',
                 'bg-zinc-900 text-cyan-500': chapter.subject === 'soft_exam_senior'
               }">
            {{ chapter.subject === 'math' ? '📐' : chapter.subject === 'logic' ? '🧠' : chapter.subject === 'english' ? '🔤' : '💻' }}
          </div>
          
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs px-2 py-0.5 rounded border font-medium" 
                    :class="subjectLabels[chapter.subject]?.color">
                 {{ subjectLabels[chapter.subject]?.text }}
              </span>
              <h3 class="font-bold text-lg text-zinc-200 truncate">{{ chapter.title }}</h3>
            </div>
            <p class="text-sm text-zinc-500 truncate">{{ chapter.description || '暂无描述' }}</p>
          </div>

          <div class="flex items-center gap-4">
            <!-- Status Badge -->
            <span class="text-xs px-2.5 py-1 rounded-full border font-medium flex items-center gap-1.5"
                  :class="statusLabels[chapter.status || 'not_started'].color">
              <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
              {{ statusLabels[chapter.status || 'not_started'].text }}
            </span>
            
            <button @click="loadChapter(chapter)" 
                    class="btn btn-secondary text-sm py-1.5 hover:bg-white/10 hover:text-white">
              开始学习
            </button>
            
            <button @click.stop="deleteChapterById(chapter.id, chapter.title)" 
                    class="btn text-sm py-1.5 bg-red-600/10 text-red-400 hover:bg-red-600/20 border border-red-500/20 opacity-60 hover:opacity-100 transition-opacity"
                    title="删除章节">
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Chapter Detail Modal -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="selectedChapter" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
        <div class="bg-[#09090b] w-full max-w-6xl h-[95vh] rounded-2xl flex flex-col border border-white/10 shadow-2xl overflow-hidden animate-fade-in relative">
           <!-- Glow Effect -->
           <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>

          <div class="p-4 border-b border-white/5 flex justify-between items-center bg-zinc-900/50 flex-shrink-0">
            <div>
               <div class="flex items-center gap-2 mb-1">
                  <span class="text-xs px-2 py-0.5 rounded border font-medium uppercase tracking-wider" 
                        :class="subjectLabels[selectedChapter.subject]?.color">
                    {{ selectedChapter.subject }}
                  </span>
                  <span class="text-zinc-500 text-xs font-mono">ID: {{ selectedChapter.id }}</span>
               </div>
               <!-- Editable Title -->
               <input 
                  v-if="isEditing"
                  v-model="selectedChapter.title"
                  type="text"
                  class="text-xl font-bold text-white bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1 w-full max-w-md focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none"
                  placeholder="章节标题"
               />
               <h2 v-else class="text-xl font-bold text-white">{{ selectedChapter.title }}</h2>
            </div>
            
            <div class="flex items-center gap-3">
                <!-- Multiple Image Upload for AI context -->
                <div v-if="isEditing" class="flex items-center gap-2">
                   <input 
                      ref="imageInput"
                      type="file" 
                      accept="image/*" 
                      multiple
                      @change="handleImageUpload" 
                      class="hidden"
                   />
                   
                   <!-- Show previews if any -->
                   <div v-if="imagePreviews.length > 0" class="flex items-center gap-1.5 bg-zinc-800 rounded-lg p-1 border border-zinc-700">
                      <div v-for="(preview, idx) in imagePreviews" :key="idx" class="relative group">
                        <img :src="preview" class="h-8 w-8 object-cover rounded" />
                        <button @click="removeUploadedImage(idx)" class="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-3 h-3 flex items-center justify-center text-[8px] opacity-0 group-hover:opacity-100">✕</button>
                      </div>
                      <button @click="$refs.imageInput.click()" class="w-8 h-8 flex items-center justify-center text-zinc-500 hover:text-white hover:bg-white/5 rounded text-lg">+</button>
                   </div>

                   <button 
                      v-else
                      @click="$refs.imageInput.click()"
                      class="btn bg-zinc-800 text-zinc-400 hover:bg-zinc-700 border border-zinc-700 text-sm px-3"
                      title="上传参考图片（支持多张）"
                   >📷</button>
                </div>

               <button 
                  v-if="isEditing"
                  @click="generateWithAI"
                  class="btn bg-purple-600/20 text-purple-400 hover:bg-purple-600/30 border border-purple-500/30 text-sm flex items-center gap-2 mr-2"
                  :disabled="isGenerating">
                  <span v-if="isGenerating" class="animate-spin h-3 w-3 border-2 border-current border-t-transparent rounded-full"></span>
                  {{ isGenerating ? 'AI 生成中...' : '🤖 AI 自动生成' }}
               </button>

               <button @click="isEditing = !isEditing" 
                      class="btn btn-ghost text-sm flex items-center gap-2"
                      :class="isEditing ? 'text-blue-400 bg-blue-500/10' : 'text-zinc-400'">
                 {{ isEditing ? '👁️ 预览' : '✏️ 编辑' }}
               </button>
               
               <button v-if="isEditing" 
                       @click="saveChapter" 
                       class="btn btn-primary text-sm py-1.5"
                       :disabled="saving">
                  {{ saving ? '保存中...' : '💾 保存' }}
               </button>
               
               <button v-if="isEditing" 
                       @click="deleteChapter" 
                       class="btn text-sm py-1.5 bg-red-600/20 text-red-400 hover:bg-red-600/30 border border-red-500/30">
                  🗑️ 删除
               </button>
               
               <button @click="closeDetail" class="text-zinc-400 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-lg">
                  ✕
               </button>
            </div>
          </div>
          
          <!-- Editor / Viewer Area -->
          <div class="flex-1 overflow-hidden relative bg-[#09090b]">
             <!-- MODE: EDIT -->
             <MarkdownEditor 
                v-if="isEditing"
                v-model:value="chapterContent"
                mode="split" 
                :readonly="false"
                :uploadImages="handleUploadImages"
                class="h-full"
             />
             
             <!-- MODE: VIEW (Rich Styled) -->
             <div v-else-if="parsedChapter" @click="handleContentClick" class="h-full overflow-y-auto p-8 space-y-8 scrollbar-custom">
               
               <!-- Learning Objectives -->
               <section v-if="parsedChapter.sections['学习目标']" class="bg-indigo-500/5 rounded-xl p-6 border-l-4 border-indigo-500">
                 <h3 class="text-lg font-bold text-indigo-400 mb-4 flex items-center gap-2">
                   <span>🎯</span> 学习目标
                 </h3>
                 <Viewer :value="renderWithLinks(parsedChapter.sections['学习目标'])" :plugins="plugins" />
               </section>
               
               <!-- Core Content -->
               <section v-if="parsedChapter.sections['核心内容']" class="bg-zinc-800/40 rounded-xl p-8 border border-white/5 shadow-sm">
                  <h3 class="text-xl font-bold text-blue-200 mb-6 flex items-center gap-3">
                   <span>📚</span> 核心内容
                 </h3>
                 <Viewer :value="renderWithLinks(parsedChapter.sections['核心内容'])" :plugins="plugins" />
               </section>
               
               <!-- Learning Advice -->
               <section v-if="parsedChapter.sections['学习建议']" class="bg-amber-500/10 rounded-xl p-6 border-l-4 border-amber-500/50">
                 <h3 class="text-lg font-bold text-amber-300 mb-4 flex items-center gap-2">
                   <span>💡</span> 学习建议
                 </h3>
                 <Viewer :value="renderWithLinks(parsedChapter.sections['学习建议'])" :plugins="plugins" />
               </section>
               
               <!-- Other Sections -->
               <template v-for="(body, title) in parsedChapter.sections" :key="title">
                 <section 
                   v-if="!['学习目标', '核心内容', '学习建议'].includes(title)"
                   class="bg-zinc-800/30 rounded-xl p-6 border border-white/5"
                 >
                   <h3 class="text-lg font-bold text-zinc-200 mb-4 flex items-center gap-2">
                     <span>📄</span> {{ title }}
                   </h3>
                   <Viewer :value="renderWithLinks(body)" :plugins="plugins" />
                 </section>
               </template>
               
               <!-- Fallback -->
               <div v-if="Object.keys(parsedChapter.sections).length === 0">
                    <Viewer :value="renderWithLinks(parsedChapter.fullContent)" :plugins="plugins" />
               </div>
             </div>
          </div>
          
          <!-- Footer (Hidden/None) -->
        </div>
      </div>
    </Transition>

    <!-- Create Chapter Modal -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6" @click.self="showCreateModal = false">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="showCreateModal = false"></div>

        <!-- Modal Content -->
        <div class="relative bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
          
          <!-- Header -->
          <div class="flex justify-between items-center p-4 border-b border-zinc-800 bg-zinc-900/50">
            <h3 class="text-lg font-semibold text-white">新增章节</h3>
            <button @click="showCreateModal = false" class="text-zinc-500 hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="p-6 overflow-y-auto space-y-4">
            
            <!-- Subject -->
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">科目</label>
              <select v-model="newChapter.subject" class="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none">
                <option value="math">数学</option>
                <option value="logic">逻辑</option>
                <option value="english">英语</option>
                <option value="soft_exam_senior">软考高级</option>
              </select>
            </div>

            <!-- Title (First, so ID can auto-generate) -->
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">章节标题 <span class="text-red-400">*</span></label>
              <input 
                v-model="newChapter.title" 
                type="text" 
                placeholder="例如：平面几何基础、韦达定理" 
                class="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none"
                autocomplete="off"
              >
            </div>

            <!-- Chapter ID is auto-generated, no input needed -->
            
            <!-- Type -->
             <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">类型</label>
              <select v-model="newChapter.type" class="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none">
                <option value="topic">知识点讲解</option>
                <option value="practice">习题训练</option>
                <option value="writing">英文作文</option>
              </select>
            </div>

            <!-- Description -->
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">简要描述</label>
              <textarea 
                v-model="newChapter.description" 
                rows="3" 
                placeholder="本章主要讲解..." 
                class="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none"
              ></textarea>
            </div>

            <!-- Auto Generate Toggle -->
            <div class="flex items-center gap-3 pt-2">
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" v-model="autoGenerateOnCreate" class="sr-only peer">
                <div class="w-11 h-6 bg-zinc-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
              <span class="text-sm text-zinc-300">🤖 创建后自动使用 AI 生成内容</span>
            </div>

            <!-- Image Paste/Upload Area (only shown when auto-generate is enabled) -->
            <div v-if="autoGenerateOnCreate" class="pt-2">
              <label class="block text-sm font-medium text-zinc-400 mb-2">📷 题目截图（支持多次 Ctrl+V 粘贴多张图片）</label>
              <div 
                @paste="handleNewChapterImagePaste"
                @click="$refs.newChapterImageInput?.click()"
                tabindex="0"
                class="w-full border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors focus:outline-none focus:border-purple-500"
                :class="newChapterImagePreviews.length > 0 ? 'border-purple-500 bg-purple-500/10' : 'border-zinc-700 hover:border-zinc-500 bg-zinc-800/50'"
              >
                <input 
                  ref="newChapterImageInput"
                  type="file" 
                  accept="image/*" 
                  multiple
                  @change="(e) => { 
                    const files = Array.from(e.target.files);
                    files.forEach(file => {
                      newChapterImages.push(file);
                      const reader = new FileReader();
                      reader.onload = (ev) => { newChapterImagePreviews.push(ev.target.result) };
                      reader.readAsDataURL(file);
                    });
                  }" 
                  class="hidden"
                />
                
                <div v-if="newChapterImagePreviews.length === 0" class="text-zinc-500 text-sm">
                  <span class="text-2xl block mb-2">📋</span>
                  点击上传或直接 Ctrl+V 粘贴
                </div>
                
                <div v-else class="flex flex-wrap gap-2 justify-center">
                  <div v-for="(preview, idx) in newChapterImagePreviews" :key="idx" class="relative group">
                    <img :src="preview" class="h-16 w-16 object-cover rounded border border-white/10" />
                    <button 
                      @click.stop="removeNewChapterImage(idx)" 
                      class="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-4 h-4 flex items-center justify-center text-[10px] opacity-0 group-hover:opacity-100 transition-opacity"
                    >✕</button>
                  </div>
                  <div class="h-16 w-16 flex items-center justify-center border-2 border-dashed border-zinc-600 rounded text-zinc-500 hover:border-zinc-400">
                    <span class="text-xl">+</span>
                  </div>
                </div>
              </div>
              <p v-if="newChapterImagePreviews.length > 0" class="text-[10px] text-zinc-500 mt-1 text-center">已添加 {{ newChapterImagePreviews.length }} 张截图，AI 将按顺序分析</p>
            </div>

          </div>

          <!-- Footer -->
          <div class="p-4 border-t border-zinc-800 bg-zinc-900/50 flex justify-end gap-3">
            <button @click="showCreateModal = false" class="px-4 py-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors">取消</button>
            <button 
              @click="createChapter" 
              :disabled="creating || !newChapter.title"
              class="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <span v-if="creating" class="animate-spin h-4 w-4 border-2 border-white/20 border-t-white rounded-full"></span>
              {{ creating ? '创建中...' : '立即创建' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style>
/* Global Prose Styles for Dynamic Content */
.prose-content h3, .prose-content h4 {
  color: #e2e8f0; /* zinc-200 */
  font-weight: 700;
  margin-top: 1.5em;
  margin-bottom: 0.75em;
  font-size: 1.1rem;
}

.prose-content ul, .prose-content ol {
  margin-left: 1.5rem;
  margin-bottom: 1rem;
  list-style-type: disc;
}

.prose-content ol {
  list-style-type: decimal;
}

.prose-content li {
  margin-bottom: 0.5rem;
  color: #d4d4d8; /* zinc-300 */
}

.prose-content p {
  margin-bottom: 1em;
  line-height: 1.7;
}

.prose-content strong {
  color: #fff;
  font-weight: 600;
}

.prose-content blockquote {
  border-left: 4px solid #3b82f6;
  padding-left: 1rem;
  font-style: italic;
  color: #94a3b8;
  margin: 1.5rem 0;
}

/* Clickable Question Links [[id]] */
.question-link {
  color: #60a5fa; /* blue-400 */
  text-decoration: underline;
  cursor: pointer;
  font-weight: 500;
  transition: color 0.15s ease;
}

.question-link:hover {
  color: #93c5fd; /* blue-300 */
}
</style>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.98); }
  to { opacity: 1; transform: scale(1); }
}

/* Custom Scrollbar for Modal */
.scrollbar-custom::-webkit-scrollbar {
  width: 8px;
}
.scrollbar-custom::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
}
.scrollbar-custom::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}
.scrollbar-custom::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
