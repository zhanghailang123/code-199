<script setup>
import { ref, computed, onMounted } from 'vue'
import { API_BASE } from '../config/api.js'

const questions = ref([])
const loading = ref(true)
const error = ref('')
const filter = ref('all')
const searchQuery = ref('')

async function fetchQuestions() {
  loading.value = true
  error.value = ''
  
  try {
    const res = await fetch(`${API_BASE}/api/questions`)
    if (res.ok) {
      const data = await res.json()
      questions.value = data.questions.map(q => ({
        ...q,
        subject: q.id.includes('math') ? 'math' : 
                 q.id.includes('logic') ? 'logic' : 
                 q.id.includes('english') ? 'english' : 'unknown'
      }))
    }
  } catch (e) {
    error.value = '无法加载题目列表'
  } finally {
    loading.value = false
  }
}

onMounted(fetchQuestions)

const filteredQuestions = computed(() => {
  let result = questions.value
  
  // Filter by subject
  if (filter.value !== 'all') {
    result = result.filter(q => q.subject === filter.value)
  }
  
  // Filter by search query
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(q => q.id.toLowerCase().includes(query))
  }
  
  return result
})

const stats = computed(() => ({
  total: questions.value.length,
  math: questions.value.filter(q => q.subject === 'math').length,
  logic: questions.value.filter(q => q.subject === 'logic').length,
  english: questions.value.filter(q => q.subject === 'english').length
}))

const subjectLabel = {
  math: '数学',
  logic: '逻辑',
  english: '英语'
}
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <header class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-3xl font-extrabold text-white">📝 全部题目</h1>
        <p class="text-zinc-500 mt-1">系统收录共 {{ stats.total }} 道题目</p>
      </div>
      <div class="flex gap-3">
        <router-link to="/smart-entry" class="btn btn-primary">
          🤖 智能录入
        </router-link>
        <router-link to="/pdf-import" class="btn btn-secondary">
          📄 PDF导入
        </router-link>
      </div>
    </header>
    
    <!-- Filter Bar -->
    <div class="card p-4 mb-8 bg-[#09090b] border border-white/10 shadow-xl">
      <div class="flex flex-wrap gap-4 items-center justify-between">
        <!-- Subject Filter -->
        <div class="flex gap-2 p-1 bg-zinc-900/50 rounded-xl border border-white/5">
          <button @click="filter = 'all'" 
                  class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                  :class="filter === 'all' ? 'bg-zinc-800 text-white shadow-sm ring-1 ring-white/10' : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/5'">
            全部 ({{ stats.total }})
          </button>
          <button @click="filter = 'math'" 
                  class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                  :class="filter === 'math' ? 'bg-red-500/10 text-red-400 ring-1 ring-red-500/20 shadow-[0_0_10px_rgba(239,68,68,0.1)]' : 'text-zinc-500 hover:text-red-400 hover:bg-red-500/5'">
            数学 ({{ stats.math }})
          </button>
          <button @click="filter = 'logic'" 
                  class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                  :class="filter === 'logic' ? 'bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20 shadow-[0_0_10px_rgba(245,158,11,0.1)]' : 'text-zinc-500 hover:text-amber-400 hover:bg-amber-500/5'">
            逻辑 ({{ stats.logic }})
          </button>
          <button @click="filter = 'english'" 
                  class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                  :class="filter === 'english' ? 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.1)]' : 'text-zinc-500 hover:text-emerald-400 hover:bg-emerald-500/5'">
            英语 ({{ stats.english }})
          </button>
        </div>
        
        <!-- Search -->
        <div class="flex-1 max-w-md relative group">
           <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500 group-focus-within:text-blue-400 transition-colors">
             🔍
           </div>
           <input v-model="searchQuery" 
                 type="text" 
                 placeholder="搜索题目 ID..."
                 class="w-full pl-10 pr-4 py-2.5 bg-zinc-900/50 border border-white/10 rounded-xl text-zinc-200 placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/50 transition-all">
        </div>
      </div>
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="text-center py-20">
      <div class="inline-block animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mb-4"></div>
      <p class="text-zinc-500 animate-pulse">加载题目数据...</p>
    </div>
    
    <!-- Error -->
    <div v-else-if="error" class="bg-red-500/10 border border-red-500/20 text-red-400 px-6 py-8 rounded-xl text-center">
      <div class="text-2xl mb-2">⚠️</div>
      {{ error }}
      <button @click="fetchQuestions" class="block mx-auto mt-4 text-sm underline hover:text-white">重试</button>
    </div>
    
    <!-- Questions Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <router-link v-for="q in filteredQuestions" 
                   :key="q.id" 
                   :to="'/question/' + q.id"
                   class="card p-0 hover:bg-zinc-900/60 transition-all group border border-white/5 hover:border-blue-500/30 overflow-hidden relative">
        
        <!-- Hover Glow -->
        <div class="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-duration-500 pointer-events-none"></div>

        <div class="p-5 flex items-start gap-4 z-10 relative">
          <!-- Minimal Icon -->
          <div class="w-10 h-10 rounded-lg flex items-center justify-center text-lg shadow-inner border border-white/5 transition-transform group-hover:scale-110 duration-300"
               :class="{
                 'bg-red-500/10 text-red-400': q.subject === 'math',
                 'bg-amber-500/10 text-amber-400': q.subject === 'logic',
                 'bg-emerald-500/10 text-emerald-400': q.subject === 'english',
                 'bg-zinc-800 text-zinc-400': q.subject === 'unknown'
               }">
            {{ q.subject === 'math' ? '📐' : q.subject === 'logic' ? '🧠' : 'A' }}
          </div>
          
          <div class="flex-1 min-w-0">
            <div class="font-mono text-sm text-zinc-500 mb-1 group-hover:text-zinc-400 transition-colors">ID: {{ q.id }}</div>
            <div class="font-bold text-zinc-200 group-hover:text-blue-400 transition-colors truncate">
              {{ subjectLabel[q.subject] || q.subject }} 题目
            </div>
            
            <!-- Tags (Mockup if not available in filtered list, using type) -->
             <div class="mt-3 flex gap-2">
                <span class="text-xs px-1.5 py-0.5 rounded bg-white/5 text-zinc-500 border border-white/5">
                   {{ q.type === 'choice' ? '选择题' : '其他' }}
                </span>
                <span class="text-xs px-1.5 py-0.5 rounded bg-white/5 text-zinc-500 border border-white/5">
                   难度 {{ q.difficulty || 3 }}
                </span>
             </div>
          </div>
          
          <span class="text-zinc-600 group-hover:text-blue-500 transition-transform group-hover:translate-x-1">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </span>
        </div>
      </router-link>
      
      <!-- Empty State -->
      <div v-if="filteredQuestions.length === 0" class="col-span-full py-20 text-center">
        <div class="text-4xl mb-4 grayscale opacity-20">📭</div>
        <p class="text-zinc-500">没有找到匹配的题目</p>
      </div>
    </div>
  </div>
</template>
