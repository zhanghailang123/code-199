<script setup>
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'

const loading = ref(true)
const error = ref('')
const chapters = ref([])
const bySubject = ref({})
const selectedChapter = ref(null)
const chapterContent = ref(null)
const activeSubject = ref('all')

const statusLabels = {
  not_started: { text: '未开始', color: 'bg-slate-200 text-slate-600' },
  in_progress: { text: '进行中', color: 'bg-blue-100 text-blue-700' },
  completed: { text: '已完成', color: 'bg-green-100 text-green-700' }
}

const subjectLabels = {
  math: { text: '数学', color: 'bg-red-500' },
  logic: { text: '逻辑', color: 'bg-amber-500' },
  english: { text: '英语', color: 'bg-green-500' }
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
  chapterContent.value = null
  
  try {
    const res = await fetch(`http://localhost:8000/api/curriculum/${chapter.id}`)
    if (!res.ok) throw new Error('无法加载章节')
    
    const data = await res.json()
    
    // Parse markdown content (remove frontmatter)
    const content = data.raw.replace(/^---[\s\S]*?---\n/, '')
    chapterContent.value = marked(content)
  } catch (e) {
    error.value = e.message
  }
}

async function updateStatus(chapter, newStatus) {
  try {
    await fetch(`http://localhost:8000/api/curriculum/${chapter.id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    })
    
    chapter.status = newStatus
  } catch (e) {
    console.error('Failed to update status:', e)
  }
}

const filteredChapters = computed(() => {
  if (activeSubject.value === 'all') return chapters.value
  return chapters.value.filter(c => c.subject === activeSubject.value)
})

const progress = computed(() => {
  const total = chapters.value.length
  if (total === 0) return 0
  const completed = chapters.value.filter(c => c.status === 'completed').length
  return Math.round((completed / total) * 100)
})

function closeDetail() {
  selectedChapter.value = null
  chapterContent.value = null
}

onMounted(loadCurriculum)
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <header class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-3xl font-extrabold text-slate-900">📚 学习路径</h1>
        <p class="text-slate-500 mt-1">系统化学习，逐章突破</p>
      </div>
      <button @click="loadCurriculum" class="btn btn-primary" :disabled="loading">🔄 刷新</button>
    </header>

    <!-- Progress Bar -->
    <div class="card p-6 mb-8">
      <div class="flex justify-between items-center mb-3">
        <span class="font-semibold text-slate-700">总体进度</span>
        <span class="text-sm text-slate-500">{{ progress }}%</span>
      </div>
      <div class="h-3 bg-slate-100 rounded-full overflow-hidden">
        <div class="h-full bg-gradient-to-r from-blue-500 to-green-500 transition-all duration-500"
             :style="{ width: progress + '%' }"></div>
      </div>
      <div class="flex gap-4 mt-4 text-sm">
        <span class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-red-500"></span>
          数学 {{ bySubject.math || 0 }}章
        </span>
        <span class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-amber-500"></span>
          逻辑 {{ bySubject.logic || 0 }}章
        </span>
        <span class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-green-500"></span>
          英语 {{ bySubject.english || 0 }}章
        </span>
      </div>
    </div>

    <!-- Filter Tabs -->
    <div class="flex gap-2 mb-6">
      <button @click="activeSubject = 'all'" 
              class="px-4 py-2 rounded-lg font-medium transition-colors"
              :class="activeSubject === 'all' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'">
        全部
      </button>
      <button @click="activeSubject = 'math'" 
              class="px-4 py-2 rounded-lg font-medium transition-colors"
              :class="activeSubject === 'math' ? 'bg-red-500 text-white' : 'bg-red-50 text-red-600 hover:bg-red-100'">
        数学
      </button>
      <button @click="activeSubject = 'logic'" 
              class="px-4 py-2 rounded-lg font-medium transition-colors"
              :class="activeSubject === 'logic' ? 'bg-amber-500 text-white' : 'bg-amber-50 text-amber-600 hover:bg-amber-100'">
        逻辑
      </button>
      <button @click="activeSubject = 'english'" 
              class="px-4 py-2 rounded-lg font-medium transition-colors"
              :class="activeSubject === 'english' ? 'bg-green-500 text-white' : 'bg-green-50 text-green-600 hover:bg-green-100'">
        英语
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-slate-500">加载中...</div>
    
    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl">
      {{ error }}
    </div>

    <!-- Chapter Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="chapter in filteredChapters" :key="chapter.id"
           @click="loadChapter(chapter)"
           class="card p-6 cursor-pointer hover:shadow-lg hover:-translate-y-1 transition-all">
        <!-- Subject Badge -->
        <div class="flex justify-between items-start mb-4">
          <span class="px-3 py-1 rounded-full text-xs font-bold text-white"
                :class="subjectLabels[chapter.subject]?.color">
            {{ subjectLabels[chapter.subject]?.text }}
          </span>
          <span class="px-2 py-1 rounded text-xs font-medium"
                :class="statusLabels[chapter.status]?.color">
            {{ statusLabels[chapter.status]?.text }}
          </span>
        </div>
        
        <h3 class="text-lg font-bold text-slate-900 mb-2">{{ chapter.title }}</h3>
        
        <div class="flex gap-4 text-sm text-slate-500 mb-4">
          <span>⏱ {{ chapter.estimated_hours }}小时</span>
          <span>📝 {{ chapter.related_questions?.length || 0 }}道题</span>
        </div>
        
        <!-- Knowledge Points -->
        <div class="flex flex-wrap gap-1">
          <span v-for="kp in (chapter.knowledge_points || []).slice(0, 3)" :key="kp"
                class="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">
            {{ kp }}
          </span>
          <span v-if="(chapter.knowledge_points?.length || 0) > 3"
                class="px-2 py-0.5 bg-slate-100 text-slate-500 rounded text-xs">
            +{{ chapter.knowledge_points.length - 3 }}
          </span>
        </div>
      </div>
      
      <div v-if="filteredChapters.length === 0" class="col-span-full text-center py-12 text-slate-400">
        暂无章节
      </div>
    </div>

    <!-- Chapter Detail Modal -->
    <div v-if="selectedChapter" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-8"
         @click.self="closeDetail">
      <div class="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Modal Header -->
        <div class="px-8 py-6 border-b border-slate-100 flex justify-between items-center">
          <div>
            <span class="px-3 py-1 rounded-full text-xs font-bold text-white mb-2 inline-block"
                  :class="subjectLabels[selectedChapter.subject]?.color">
              {{ subjectLabels[selectedChapter.subject]?.text }}
            </span>
            <h2 class="text-2xl font-bold text-slate-900">{{ selectedChapter.title }}</h2>
          </div>
          <button @click="closeDetail" class="w-10 h-10 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-xl">
            ✕
          </button>
        </div>
        
        <!-- Modal Content -->
        <div class="flex-1 overflow-y-auto p-8">
          <div v-if="!chapterContent" class="text-center py-12 text-slate-500">加载中...</div>
          <div v-else class="prose-content" v-html="chapterContent"></div>
        </div>
        
        <!-- Modal Footer -->
        <div class="px-8 py-4 border-t border-slate-100 flex justify-between items-center">
          <div class="flex gap-2">
            <button @click="updateStatus(selectedChapter, 'not_started')"
                    class="px-4 py-2 rounded-lg text-sm font-medium"
                    :class="selectedChapter.status === 'not_started' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'">
              未开始
            </button>
            <button @click="updateStatus(selectedChapter, 'in_progress')"
                    class="px-4 py-2 rounded-lg text-sm font-medium"
                    :class="selectedChapter.status === 'in_progress' ? 'bg-blue-500 text-white' : 'bg-blue-50 text-blue-600'">
              进行中
            </button>
            <button @click="updateStatus(selectedChapter, 'completed')"
                    class="px-4 py-2 rounded-lg text-sm font-medium"
                    :class="selectedChapter.status === 'completed' ? 'bg-green-500 text-white' : 'bg-green-50 text-green-600'">
              已完成
            </button>
          </div>
          <button @click="closeDetail" class="btn btn-primary">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.prose-content {
  color: #334155;
  line-height: 1.8;
}

.prose-content :deep(h2) {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin-top: 2rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.prose-content :deep(h3) {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b;
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
}

.prose-content :deep(p) {
  margin-bottom: 1rem;
}

.prose-content :deep(ul), .prose-content :deep(ol) {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.prose-content :deep(li) {
  margin-bottom: 0.5rem;
}

.prose-content :deep(table) {
  width: 100%;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.prose-content :deep(th) {
  background: #f8fafc;
  padding: 0.5rem;
  text-align: left;
  border: 1px solid #e2e8f0;
}

.prose-content :deep(td) {
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
}

.prose-content :deep(blockquote) {
  border-left: 4px solid #3b82f6;
  background: #eff6ff;
  padding: 0.75rem 1rem;
  border-radius: 0 0.5rem 0.5rem 0;
  margin-bottom: 1rem;
}

.prose-content :deep(code) {
  background: #f1f5f9;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.prose-content :deep(hr) {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 2rem 0;
}
</style>
