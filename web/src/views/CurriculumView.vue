<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import MarkdownEditor from '../components/MarkdownEditor.vue'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const chapters = ref([])
const bySubject = ref({})
const selectedChapter = ref(null)
const chapterContent = ref(null) // This will now hold raw markdown
const activeSubject = ref('all')
const isEditing = ref(false)
const saving = ref(false)

const filteredChapters = computed(() => {
  if (activeSubject.value === 'all') return chapters.value
  return chapters.value.filter(c => c.subject === activeSubject.value)
})

const statusLabels = {
  not_started: { text: '未开始', color: 'bg-zinc-800 text-zinc-400 border-zinc-700' },
  in_progress: { text: '进行中', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  completed: { text: '已完成', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' }
}

const subjectLabels = {
  math: { text: '数学', color: 'text-red-400 bg-red-500/10 border-red-500/20' },
  logic: { text: '逻辑', color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' },
  english: { text: '英语', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' }
}

async function loadCurriculum() {
  loading.value = true
  error.value = ''
  
  try {
    const res = await fetch('http://localhost:8000/api/curriculum')
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
  chapterContent.value = null // Reset
  isEditing.value = false // Default to view mode
  
  try {
    const res = await fetch(`http://localhost:8000/api/curriculum/${chapter.id}`)
    if (!res.ok) throw new Error('无法加载章节')
    
    const data = await res.json()
    
    // Store FULL raw content including frontmatter for editing
    chapterContent.value = data.raw
  } catch (e) {
    error.value = e.message
  }
}

async function saveChapter() {
  if (!selectedChapter.value || !chapterContent.value) return
  
  saving.value = true
  try {
    // We need to parse the ID from the content or use the selectedChapter.id
    // Here we assume ID matches selectedChapter.id for the path
    
    // NOTE: In a real app we might want to validate frontmatter structure
    
    // Currently api.py update_knowledge_point expects KnowledgePointCreate model structure in body
    // BUT we are editing a CHAPTER (which are essentially just files in hierarchy).
    // The current API structure for "curriculum" update is only for *status*.
    // I need to add a generic file update for curriculum or reuse knowledge/question endpoints?
    // Actually, looking at previous step, I implemented `update_knowledge_point` and `update_question`.
    // Curriculum chapters are NOT questions or knowledge points in the strict sense of those directories.
    // They are in `content/curriculum/...`.
    
    // Wait, the user asked for "show/edit for ALL frontend displayed questions/knowledge points".
    // AND "curriculum" chapters.
    // I need an endpoint for curriculum update too! 
    // Implementing a quick fix endpoint on client side logic won't work without backend support.
    
    // Checking api.py... I didn't add `update_curriculum_chapter`!
    // I added `update_question` and `update_knowledge_point`.
    // This view is `CurriculumView.vue`.
    
    // Let's assume for this step I will only View/Preview.
    // BUT the task says "Implement Markdown Editor".
    // I should stop and fix API first? 
    // "Questions and Knowledge Points" was the request. This is Curriculum.
    // User: "对于所有前端展示的题目 知识点 能否实现md的编辑和预览"
    
    // The user's request specifically mentioned "Questions and Knowledge Points", 
    // but the conversation context was about the Curriculum page layout.
    // It is highly likely they want to edit THESE pages too.
    
    // I will add a fallback "Not Implemented" alert for save if not supported,
    // OR I can quickly add the endpoint. 
    // Let's add the endpoint in the next turn if needed, or assume I can use a generic one?
    // No, let's just implement the UI for now and I will add the backend endpoint in a parallel step or next tool.
    
    // Just implemented View Mode logic mostly for now?
    // NO, I must deliver editing.
    // PROPOSAL: I will use the `replace_file_content` equivalent via API?
    // I'll assume I need to add the endpoint.
    
    // I'll stick to view only for a second in this file update? No that's waste.
    
    // Okay, I will optimistically write the fetch call to `PUT /api/curriculum/{id}/content` 
    // and then go implement it in API.
    
    const res = await fetch(`http://localhost:8000/api/curriculum/${selectedChapter.value.id}/content`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: chapterContent.value })
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

// Handle Custom Link Clicks (Delegate)
function handleEditorClick(e) {
  // ByteMD renders markdown. We need to handle internal links if possible.
  // But ByteMD's viewer captures clicks.
  // We can try to attach a global listener or just let standard links work?
  // Our `[[id]]` syntax needs a plugin or manual replacement.
  // ByteMD doesn't support custom regex replacement out of the box easily without a plugin.
  // For now, I will display Raw Markdown in "view" mode?
  // No, `MarkdownEditor` has a viewer.
  
  // Custom Plugin for [[id]]?
  // Creating a full Remark plugin is complex for this step.
  // I will leave the `[[id]]` as text for now in the editor,
  // Or I can post-process the HTML?
  // ByteMD allows `sanitize` customization or viewer DOM manipulation?
  
  // Workaround: We use the Viewer but we can't easily inject the "Clickable Span" logic 
  // without a proper Remark/Rehype plugin.
  // 
  // Strategy: For the "Preview" / "View" mode, I might still use `marked` + my custom replacement 
  // IF I want to keep the custom badge links active.
  // The Editor "Preview" pane might show them as text.
  // 
  // Compromise: Use ByteMD for EDITING. Use my custom `marked` renderer for VIEWING (Read-only).
  // When Editing, you see raw markdown.
}

// Render markdown with [[id]] links converted to clickable spans
function renderWithLinks(mdContent) {
  // First convert markdown to HTML
  let html = marked(mdContent)
  
  // Then convert [[id]] syntax to clickable spans
  // Pattern: [[some-question-id]]
  html = html.replace(/\[\[([^\]]+)\]\]/g, (match, id) => {
    return `<span class="question-link" data-question-id="${id}">${id}</span>`
  })
  
  return html
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
  
  // Split into Main Sections by H2 headers using a more robust method
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
  
  // Fallback: full HTML if no sections matched
  const fullHtml = marked(content)
  
  return {
    sections,
    fullHtml
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
      <button @click="loadCurriculum" class="btn btn-primary" :disabled="loading">🔄 刷新</button>
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
               'bg-gradient-to-r from-emerald-500/5 via-transparent to-transparent': chapter.subject === 'english'
             }"></div>

        <div class="relative flex items-center gap-4">
          <!-- Subject Icon -->
          <div class="w-12 h-12 rounded-xl flex items-center justify-center text-xl border border-white/5 shadow-inner"
               :class="{
                 'bg-zinc-900 text-red-500': chapter.subject === 'math',
                 'bg-zinc-900 text-amber-500': chapter.subject === 'logic',
                 'bg-zinc-900 text-emerald-500': chapter.subject === 'english'
               }">
            {{ chapter.subject === 'math' ? '📐' : chapter.subject === 'logic' ? '🧠' : '🔤' }}
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
          </div>
        </div>
      </div>
    </div>

    <!-- Chapter Detail Modal -->
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
            <h2 class="text-xl font-bold text-white">{{ selectedChapter.title }}</h2>
          </div>
          
          <div class="flex items-center gap-3">
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
             
             <div class="w-px h-6 bg-white/10 mx-2"></div>
             
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
              class="h-full"
           />
           
           <!-- MODE: VIEW (Rich Styled) -->
           <div v-else-if="parsedChapter" @click="handleContentClick" class="h-full overflow-y-auto p-8 space-y-8 scrollbar-custom">
             
             <!-- Learning Objectives (Using known section name '学习目标') -->
             <section v-if="parsedChapter.sections['学习目标']" class="bg-indigo-500/5 rounded-xl p-6 border-l-4 border-indigo-500">
               <h3 class="text-lg font-bold text-indigo-400 mb-4 flex items-center gap-2">
                 <span class="text-2xl">🎯</span> 学习目标
               </h3>
               <div class="prose-content text-zinc-300 leading-relaxed" v-html="marked(parsedChapter.sections['学习目标'])"></div>
             </section>
             
             <!-- Core Content (Using known section name '核心内容') -->
             <section v-if="parsedChapter.sections['核心内容']" class="bg-zinc-800/40 rounded-xl p-8 border border-white/5 shadow-sm">
                <h3 class="text-xl font-bold text-blue-200 mb-6 flex items-center gap-3">
                 <span class="text-2xl">📚</span> 核心内容
               </h3>
               <div class="prose-content text-zinc-200 leading-relaxed" v-html="marked(parsedChapter.sections['核心内容'])"></div>
             </section>
             
             <!-- Learning Advice (Using known section name '学习建议') -->
             <section v-if="parsedChapter.sections['学习建议']" class="bg-amber-500/10 rounded-xl p-6 border-l-4 border-amber-500/50">
               <h3 class="text-lg font-bold text-amber-300 mb-4 flex items-center gap-2">
                 <span class="text-2xl">💡</span> 学习建议
               </h3>
               <div class="prose-content text-zinc-300" v-html="marked(parsedChapter.sections['学习建议'])"></div>
             </section>
             
             <!-- Other Sections (Dynamic rendering for non-hardcoded sections) -->
             <template v-for="(body, title) in parsedChapter.sections" :key="title">
               <section 
                 v-if="!['学习目标', '核心内容', '学习建议'].includes(title)"
                 class="bg-zinc-800/30 rounded-xl p-6 border border-white/5"
               >
                 <h3 class="text-lg font-bold text-zinc-200 mb-4 flex items-center gap-2">
                   <span class="text-2xl">📄</span> {{ title }}
                 </h3>
                 <div class="prose-content text-zinc-300" v-html="renderWithLinks(body)"></div>
               </section>
             </template>
             
             <!-- Fallback: Just show full HTML if no specific sections matched -->
             <div v-if="Object.keys(parsedChapter.sections).length === 0" 
                  class="prose-content text-zinc-300" 
                  v-html="parsedChapter.fullHtml">
             </div>
           </div>
        </div>
        
        <!-- Footer (Hidden/None) -->
      </div>
    </div>
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
