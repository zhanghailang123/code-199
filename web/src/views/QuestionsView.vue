<script setup>
import { ref, computed, onMounted } from 'vue'

const questions = ref([])
const loading = ref(true)
const error = ref('')
const filter = ref('all')
const searchQuery = ref('')

async function fetchQuestions() {
  loading.value = true
  error.value = ''
  
  try {
    const res = await fetch('http://localhost:8000/api/questions')
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
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <header class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-3xl font-extrabold text-slate-900">📝 全部题目</h1>
        <p class="text-slate-500 mt-1">共 {{ stats.total }} 道题目</p>
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
    <div class="card p-4 mb-6">
      <div class="flex flex-wrap gap-4 items-center">
        <!-- Subject Filter -->
        <div class="flex gap-2">
          <button @click="filter = 'all'" 
                  class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  :class="filter === 'all' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'">
            全部 ({{ stats.total }})
          </button>
          <button @click="filter = 'math'" 
                  class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  :class="filter === 'math' ? 'bg-red-500 text-white' : 'bg-red-50 text-red-600 hover:bg-red-100'">
            数学 ({{ stats.math }})
          </button>
          <button @click="filter = 'logic'" 
                  class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  :class="filter === 'logic' ? 'bg-amber-500 text-white' : 'bg-amber-50 text-amber-600 hover:bg-amber-100'">
            逻辑 ({{ stats.logic }})
          </button>
          <button @click="filter = 'english'" 
                  class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  :class="filter === 'english' ? 'bg-green-500 text-white' : 'bg-green-50 text-green-600 hover:bg-green-100'">
            英语 ({{ stats.english }})
          </button>
        </div>
        
        <!-- Search -->
        <div class="flex-1 min-w-[200px]">
          <input v-model="searchQuery" 
                 type="text" 
                 placeholder="搜索题目ID..."
                 class="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none">
        </div>
      </div>
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-slate-500">
      加载中...
    </div>
    
    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl">
      {{ error }}
    </div>
    
    <!-- Questions Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <router-link v-for="q in filteredQuestions" 
                   :key="q.id" 
                   :to="'/question/' + q.id"
                   class="card p-5 hover:shadow-lg hover:border-blue-300 transition-all group">
        <div class="flex items-start gap-4">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center text-white text-xl flex-shrink-0"
               :class="{
                 'bg-red-500': q.subject === 'math',
                 'bg-amber-500': q.subject === 'logic',
                 'bg-green-500': q.subject === 'english',
                 'bg-slate-400': q.subject === 'unknown'
               }">
            {{ q.subject === 'math' ? '📐' : q.subject === 'logic' ? '🧠' : '📖' }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="font-bold text-slate-900 group-hover:text-blue-600 transition-colors truncate">
              {{ q.id }}
            </div>
            <div class="text-sm text-slate-500 mt-1">
              {{ subjectLabel[q.subject] || q.subject }}
            </div>
          </div>
          <span class="text-slate-300 group-hover:text-blue-500 font-bold text-xl transition-colors">→</span>
        </div>
      </router-link>
      
      <!-- Empty State -->
      <div v-if="filteredQuestions.length === 0" class="col-span-full text-center py-12 text-slate-400">
        {{ searchQuery ? '没有找到匹配的题目' : '暂无题目' }}
      </div>
    </div>
  </div>
</template>
