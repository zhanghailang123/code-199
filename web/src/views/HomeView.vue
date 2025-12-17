<script setup>
import { ref, computed, onMounted } from 'vue'

// Reactive state for content
const questions = ref([])
const knowledgePoints = ref([])
const loading = ref(true)
const error = ref('')

// Fetch content from API
async function fetchContent() {
  loading.value = true
  error.value = ''
  
  try {
    // Fetch questions
    const qRes = await fetch('http://localhost:8000/api/questions')
    if (qRes.ok) {
      const qData = await qRes.json()
      questions.value = qData.questions.map(q => ({
        ...q,
        subject: q.id.includes('math') ? 'math' : 
                 q.id.includes('logic') ? 'logic' : 
                 q.id.includes('english') ? 'english' : 'unknown'
      }))
    }
    
    // Fetch knowledge points
    const kpRes = await fetch('http://localhost:8000/api/knowledge')
    if (kpRes.ok) {
      const kpData = await kpRes.json()
      knowledgePoints.value = kpData.knowledge_points.map(kp => ({
        ...kp,
        subject: kp.category
      }))
    }
  } catch (e) {
    error.value = '无法连接到后端API，请确保API服务已启动 (端口8000)'
    console.error('API Error:', e)
  } finally {
    loading.value = false
  }
}

// Load on mount
onMounted(() => {
  fetchContent()
})

const stats = computed(() => ({
  totalQuestions: questions.value.length,
  totalKnowledge: knowledgePoints.value.length
}))
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <header class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-3xl font-extrabold text-slate-900">学习仪表盘</h1>
        <p class="text-slate-500 mt-1">欢迎回来，保持今天的学习节奏！</p>
      </div>
      <div class="flex gap-3">
        <button @click="fetchContent" class="btn btn-secondary" :disabled="loading">
          🔄 刷新
        </button>
        <router-link to="/smart-entry" class="btn btn-primary">
          🤖 智能录入
        </router-link>
      </div>
    </header>
    
    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12 text-slate-500">
      加载中...
    </div>
    
    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl mb-8">
      {{ error }}
    </div>
    
    <template v-else>
      <!-- Stats Row -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div class="card p-6 flex items-center gap-5">
          <div class="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center text-2xl">📝</div>
          <div>
            <h3 class="text-sm uppercase tracking-wide text-slate-500 font-semibold">总题目</h3>
            <div class="text-3xl font-bold text-slate-900">{{ stats.totalQuestions }}</div>
          </div>
        </div>
        <div class="card p-6 flex items-center gap-5">
          <div class="w-12 h-12 bg-green-100 text-green-600 rounded-xl flex items-center justify-center text-2xl">🧠</div>
          <div>
            <h3 class="text-sm uppercase tracking-wide text-slate-500 font-semibold">知识点</h3>
            <div class="text-3xl font-bold text-slate-900">{{ stats.totalKnowledge }}</div>
          </div>
        </div>
        <div class="card p-6 flex items-center gap-5">
          <div class="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center text-2xl">🔥</div>
          <div>
            <h3 class="text-sm uppercase tracking-wide text-slate-500 font-semibold">连续打卡</h3>
            <div class="text-3xl font-bold text-slate-900">3 天</div>
          </div>
        </div>
      </div>

      <!-- Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Recent Questions -->
        <section class="card overflow-hidden">
          <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
            <h2 class="font-semibold text-slate-800">题目列表</h2>
            <span class="text-sm text-slate-400">{{ questions.length }} 题</span>
          </div>
          <div class="divide-y divide-slate-100 max-h-96 overflow-y-auto">
            <router-link 
              v-for="item in questions" 
              :key="item.id"
              :to="'/question/' + item.id"
              class="flex items-center gap-4 px-6 py-4 hover:bg-slate-50 transition-colors"
            >
              <div class="w-9 h-9 bg-slate-100 rounded-lg flex items-center justify-center">📄</div>
              <div class="flex-1">
                <div class="font-medium text-slate-900">{{ item.id }}</div>
                <span class="tag" :class="'tag-' + item.subject">{{ item.subject }}</span>
              </div>
              <span class="text-slate-300 font-bold">→</span>
            </router-link>
            <div v-if="questions.length === 0" class="p-12 text-center text-slate-400">
              暂无题目，快去添加吧！
            </div>
          </div>
        </section>
        
        <!-- Knowledge Points -->
        <section class="card overflow-hidden">
          <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
            <h2 class="font-semibold text-slate-800">知识点列表</h2>
            <span class="text-sm text-slate-400">{{ knowledgePoints.length }} 个</span>
          </div>
          <div class="divide-y divide-slate-100 max-h-96 overflow-y-auto">
            <router-link 
              v-for="item in knowledgePoints" 
              :key="item.id"
              :to="'/knowledge/' + item.category + '/' + item.id"
              class="flex items-center gap-4 px-6 py-4 hover:bg-slate-50 transition-colors"
            >
              <div class="w-9 h-9 bg-slate-100 rounded-lg flex items-center justify-center">💡</div>
              <div class="flex-1">
                <div class="font-medium text-slate-900">{{ item.id }}</div>
                <span class="tag" :class="'tag-' + item.subject">{{ item.subject }}</span>
              </div>
              <span class="text-slate-300 font-bold">→</span>
            </router-link>
            <div v-if="knowledgePoints.length === 0" class="p-12 text-center text-slate-400">
              暂无知识点
            </div>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>
