<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'

function parseFrontmatter(text) {
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/)
  if (!match) return { meta: {}, content: text }
  
  const metaText = match[1]
  const content = match[2]
  
  const meta = {}
  let currentKey = null
  
  metaText.split('\n').forEach(line => {
    // Handle YAML arrays
    if (line.trim().startsWith('- ')) {
      if (currentKey) {
        if (!Array.isArray(meta[currentKey])) {
          meta[currentKey] = []
        }
        meta[currentKey].push(line.trim().substring(2))
      }
      return
    }
    
    const colonIndex = line.indexOf(':')
    if (colonIndex > 0) {
      const key = line.substring(0, colonIndex).trim()
      const value = line.substring(colonIndex + 1).trim()
      currentKey = key
      if (value) {
        meta[key] = value
      }
    }
  })
  
  return { meta, content }
}

const route = useRoute()
const loading = ref(true)
const error = ref('')
const rawContent = ref('')
const subject = ref('unknown')

async function fetchContent() {
  loading.value = true
  error.value = ''
  
  const id = route.params.id
  const category = route.params.category
  const routeName = route.name
  
  try {
    let apiUrl = ''
    
    // Detect if this is a knowledge route or question route
    if (routeName === 'knowledge' && category) {
      apiUrl = `http://localhost:8000/api/knowledge/${category}/${id}`
    } else {
      apiUrl = `http://localhost:8000/api/questions/${id}`
    }
    
    const res = await fetch(apiUrl)
    if (!res.ok) throw new Error('内容未找到')
    
    const data = await res.json()
    rawContent.value = data.raw || ''
    
    // Determine subject from category or id
    if (category) {
      subject.value = category
    } else if (id.includes('math')) {
      subject.value = 'math'
    } else if (id.includes('logic')) {
      subject.value = 'logic'
    } else if (id.includes('english')) {
      subject.value = 'english'
    }
    
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(fetchContent)
watch(() => route.params.id, fetchContent)

const parsed = computed(() => {
  if (!rawContent.value) return null
  const { meta, content } = parseFrontmatter(rawContent.value)
  
  // Custom markdown rendering with section parsing
  const sections = {}
  const sectionRegex = /## (题目|选项|答案|解析)\n([\s\S]*?)(?=\n## |$)/g
  let match
  while ((match = sectionRegex.exec(content)) !== null) {
    sections[match[1]] = match[2].trim()
  }
  
  return {
    meta,
    sections,
    fullHtml: marked(content)
  }
})

const item = computed(() => ({
  id: route.params.id,
  subject: subject.value
}))

const difficultyStars = computed(() => {
  const diff = parseInt(parsed.value?.meta?.difficulty) || 3
  return '★'.repeat(diff) + '☆'.repeat(5 - diff)
})

const subjectLabel = computed(() => {
  const map = { math: '数学', logic: '逻辑', english: '英语' }
  return map[subject.value] || subject.value
})
</script>

<template>
  <!-- Loading -->
  <div v-if="loading" class="max-w-4xl mx-auto py-20 text-center">
    <div class="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    <p class="mt-4 text-slate-500">加载中...</p>
  </div>
  
  <!-- Error -->
  <div v-else-if="error" class="max-w-md mx-auto text-center py-20">
    <div class="card p-8">
      <div class="text-5xl mb-4">😕</div>
      <h2 class="text-xl font-bold text-slate-800 mb-2">内容未找到</h2>
      <p class="text-slate-500 mb-6">ID: {{ route.params.id }}</p>
      <router-link to="/" class="btn btn-primary">返回首页</router-link>
    </div>
  </div>
  
  <!-- Content -->
  <div class="max-w-4xl mx-auto" v-else-if="parsed">
    <!-- Breadcrumb -->
    <div class="flex items-center gap-2 text-sm text-slate-500 mb-6">
      <button @click="$router.back()" class="font-medium text-slate-600 hover:text-blue-600 transition-colors">
        ← 返回上一页
      </button>
    </div>

    <!-- Main Card -->
    <article class="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
      <!-- Hero Header -->
      <header class="relative bg-gradient-to-br from-slate-800 to-slate-900 text-white px-8 py-10">
        <!-- Subject Badge -->
        <div class="absolute top-6 right-6">
          <span class="px-4 py-2 rounded-full text-sm font-bold"
                :class="{
                  'bg-red-500': subject === 'math',
                  'bg-amber-500': subject === 'logic', 
                  'bg-green-500': subject === 'english'
                }">
            {{ subjectLabel }}
          </span>
        </div>
        
        <h1 class="text-3xl font-extrabold mb-4">{{ parsed.meta.id || item.id }}</h1>
        
        <div class="flex flex-wrap gap-6 text-sm">
          <div>
            <span class="text-slate-400">来源</span>
            <span class="ml-2 font-medium">{{ parsed.meta.source || '管理类联考' }}</span>
          </div>
          <div>
            <span class="text-slate-400">难度</span>
            <span class="ml-2 text-yellow-400">{{ difficultyStars }}</span>
          </div>
          <div>
            <span class="text-slate-400">题型</span>
            <span class="ml-2 font-medium">{{ parsed.meta.type === 'choice' ? '选择题' : parsed.meta.type }}</span>
          </div>
        </div>
        
        <!-- Knowledge Points Pills -->
        <div class="mt-6 flex flex-wrap gap-2" v-if="parsed.meta.knowledge_points">
          <span v-for="kp in (Array.isArray(parsed.meta.knowledge_points) ? parsed.meta.knowledge_points : [])" 
                :key="kp"
                class="px-3 py-1 bg-white/10 rounded-full text-xs font-medium">
            {{ kp }}
          </span>
        </div>
      </header>

      <!-- Content Sections -->
      <div class="p-8 space-y-8">
        <!-- Question Section -->
        <section v-if="parsed.sections['题目']" class="bg-blue-50 rounded-xl p-6 border-l-4 border-blue-500">
          <h2 class="text-lg font-bold text-blue-900 mb-4 flex items-center gap-2">
            <span class="text-2xl">📝</span> 题目
          </h2>
          <div class="text-slate-800 text-lg leading-relaxed whitespace-pre-wrap">{{ parsed.sections['题目'] }}</div>
        </section>

        <!-- Options Section -->
        <section v-if="parsed.sections['选项']" class="bg-slate-50 rounded-xl p-6">
          <h2 class="text-lg font-bold text-slate-700 mb-4 flex items-center gap-2">
            <span class="text-2xl">📋</span> 选项
          </h2>
          <div class="space-y-3">
            <div v-for="(line, i) in parsed.sections['选项'].split('\n').filter(l => l.trim())" 
                 :key="i"
                 class="flex items-start gap-3 p-3 rounded-lg hover:bg-white transition-colors">
              <span class="w-8 h-8 flex items-center justify-center rounded-full bg-slate-200 text-slate-700 font-bold text-sm flex-shrink-0">
                {{ line.charAt(0) }}
              </span>
              <span class="text-slate-700 pt-1">{{ line.substring(2).trim() }}</span>
            </div>
          </div>
        </section>

        <!-- Answer Section -->
        <section v-if="parsed.sections['答案']" class="bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl p-6 text-white">
          <h2 class="text-lg font-bold mb-3 flex items-center gap-2">
            <span class="text-2xl">✅</span> 正确答案
          </h2>
          <div class="text-4xl font-extrabold tracking-wider">{{ parsed.sections['答案'] }}</div>
        </section>

        <!-- Explanation Section -->
        <section v-if="parsed.sections['解析']" class="bg-amber-50 rounded-xl p-6 border-l-4 border-amber-400">
          <h2 class="text-lg font-bold text-amber-900 mb-4 flex items-center gap-2">
            <span class="text-2xl">💡</span> 解析
          </h2>
          <div class="prose-content text-slate-700" v-html="marked(parsed.sections['解析'])"></div>
        </section>
        
        <!-- English-Specific: Vocabulary Section -->
        <section v-if="parsed.meta.vocabulary && subject === 'english'" class="bg-indigo-50 rounded-xl p-6 border-l-4 border-indigo-400">
          <h2 class="text-lg font-bold text-indigo-900 mb-4 flex items-center gap-2">
            <span class="text-2xl">📚</span> 核心词汇
          </h2>
          <div class="space-y-4">
            <div v-for="(vocab, i) in parsed.meta.vocabulary" :key="i" class="bg-white rounded-lg p-4 shadow-sm">
              <div class="flex items-baseline gap-3 mb-2">
                <span class="text-xl font-bold text-indigo-700">{{ vocab.word }}</span>
                <span class="text-sm text-slate-500">{{ vocab.phonetic }}</span>
              </div>
              <div class="text-slate-700 mb-2">{{ vocab.meaning }}</div>
              <div class="text-sm text-slate-500 italic mb-3">{{ vocab.example }}</div>
              
              <!-- Associated Words -->
              <div v-if="vocab.associated_words?.length" class="flex flex-wrap gap-2">
                <span class="text-xs text-indigo-600 font-medium">联想词:</span>
                <span v-for="word in vocab.associated_words" :key="word" 
                      class="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs">
                  {{ word }}
                </span>
              </div>
            </div>
          </div>
        </section>
        
        <!-- English-Specific: Key Sentences Section -->
        <section v-if="parsed.meta.key_sentences && subject === 'english'" class="bg-purple-50 rounded-xl p-6 border-l-4 border-purple-400">
          <h2 class="text-lg font-bold text-purple-900 mb-4 flex items-center gap-2">
            <span class="text-2xl">✍️</span> 长难句分析
          </h2>
          <div class="space-y-6">
            <div v-for="(sentence, i) in parsed.meta.key_sentences" :key="i" class="bg-white rounded-lg p-4 shadow-sm">
              <div class="text-slate-800 font-medium mb-2 leading-relaxed">{{ sentence.original }}</div>
              <div class="text-slate-600 mb-3">📝 {{ sentence.translation }}</div>
              <div class="text-sm text-purple-700 mb-4">
                <span class="font-medium">结构分析:</span> {{ sentence.structure }}
              </div>
              
              <!-- Similar Sentences -->
              <div v-if="sentence.similar_sentences?.length" class="border-t pt-3">
                <div class="text-xs text-purple-600 font-medium mb-2">类似结构句子:</div>
                <div class="space-y-2">
                  <div v-for="(sim, j) in sentence.similar_sentences" :key="j" 
                       class="text-sm text-slate-600 pl-3 border-l-2 border-purple-200">
                    {{ sim }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
        
        <!-- English-Specific: Reading Skills Section -->
        <section v-if="parsed.meta.reading_skills && subject === 'english'" class="bg-teal-50 rounded-xl p-6 border-l-4 border-teal-400">
          <h2 class="text-lg font-bold text-teal-900 mb-4 flex items-center gap-2">
            <span class="text-2xl">🎯</span> 阅读技巧
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="bg-white rounded-lg p-4">
              <div class="text-sm text-teal-600 font-medium mb-1">题型分类</div>
              <div class="text-slate-800">{{ parsed.meta.reading_skills.question_type }}</div>
            </div>
            <div class="bg-white rounded-lg p-4">
              <div class="text-sm text-teal-600 font-medium mb-1">解题策略</div>
              <div class="text-slate-800">{{ parsed.meta.reading_skills.solving_strategy }}</div>
            </div>
            <div class="bg-white rounded-lg p-4">
              <div class="text-sm text-teal-600 font-medium mb-1">干扰项分析</div>
              <div class="text-slate-800">{{ parsed.meta.reading_skills.distractor_analysis }}</div>
            </div>
          </div>
        </section>
      </div>
    </article>
  </div>
</template>

<style scoped>
.prose-content {
  line-height: 1.8;
}

.prose-content :deep(h1),
.prose-content :deep(h2),
.prose-content :deep(h3) {
  font-weight: 700;
  color: #78350f;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.prose-content :deep(p) {
  margin-bottom: 1rem;
}

.prose-content :deep(ol),
.prose-content :deep(ul) {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.prose-content :deep(li) {
  margin-bottom: 0.5rem;
}

.prose-content :deep(strong) {
  color: #92400e;
  font-weight: 600;
}

.prose-content :deep(code) {
  background: #fef3c7;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
