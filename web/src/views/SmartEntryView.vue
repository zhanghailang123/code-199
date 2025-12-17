<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'

const router = useRouter()

// State
const rawText = ref('')
const analyzing = ref(false)
const error = ref('')
const success = ref('')
const analyzed = ref(null)
const saving = ref(false)

// Form data (filled after analysis)
const form = ref({
  id: '',
  source: '2024年管理类联考',
  subject: 'math',
  type: 'choice',
  difficulty: 3,
  knowledge_points: '',
  tags: '',
  content: '',
  options: '',
  answer: '',
  explanation: ''
})

// Preview of analyzed content
const previewHtml = computed(() => {
  if (!form.value.content) return '<p class="text-slate-400">分析结果将显示在这里...</p>'
  
  const md = `## 题目\n${form.value.content}\n\n## 选项\n${form.value.options}\n\n## 答案\n${form.value.answer}\n\n## 解析\n${form.value.explanation}`
  return marked(md)
})

// Analyze with LLM
async function analyze() {
  if (!rawText.value.trim()) {
    error.value = '请粘贴题目内容'
    return
  }
  
  analyzing.value = true
  error.value = ''
  analyzed.value = null
  
  try {
    const response = await fetch('http://localhost:8000/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question_text: rawText.value })
    })
    
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || '分析失败')
    }
    
    const result = await response.json()
    
    if (result.success && result.data) {
      analyzed.value = result.data
      
      // Fill form with analyzed data
      const d = result.data
      form.value = {
        id: generateId(d.subject),
        source: '2024年管理类联考',
        subject: d.subject || 'math',
        type: d.type || 'choice',
        difficulty: d.difficulty || 3,
        knowledge_points: (d.knowledge_points || []).join(', '),
        tags: (d.tags || []).join(', '),
        content: d.content || '',
        options: d.options || '',
        answer: d.answer || '',
        explanation: d.explanation || ''
      }
      
      success.value = 'AI分析完成！请检查并保存'
    } else {
      throw new Error('分析返回格式错误')
    }
    
  } catch (e) {
    error.value = e.message || '分析失败，请检查API Key配置'
  } finally {
    analyzing.value = false
  }
}

// Generate question ID
function generateId(subject) {
  const year = '2024'
  const subj = subject || 'math'
  const random = Math.floor(Math.random() * 100).toString().padStart(2, '0')
  return `${year}-${subj}-q${random}`
}

// Save the question
async function saveQuestion() {
  if (!form.value.id) {
    error.value = '请填写题目ID'
    return
  }
  
  saving.value = true
  error.value = ''
  
  try {
    const payload = {
      ...form.value,
      knowledge_points: form.value.knowledge_points.split(',').map(s => s.trim()).filter(Boolean),
      tags: form.value.tags.split(',').map(s => s.trim()).filter(Boolean)
    }
    
    const response = await fetch('http://localhost:8000/api/questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || '保存失败')
    }
    
    success.value = '题目保存成功！'
    setTimeout(() => router.push('/'), 1500)
    
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <header class="mb-8">
      <router-link to="/" class="text-slate-500 hover:text-slate-700 text-sm font-medium">← 返回仪表盘</router-link>
      <h1 class="text-3xl font-extrabold text-slate-900 mt-2">智能录入</h1>
      <p class="text-slate-500 mt-1">粘贴原题 → AI自动分析 → 一键保存</p>
    </header>

    <!-- Step 1: Paste raw text -->
    <div class="card p-6 mb-8" v-if="!analyzed">
      <h2 class="text-lg font-bold text-slate-800 mb-4">第一步：粘贴题目原文</h2>
      
      <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
        {{ error }}
      </div>
      
      <textarea 
        v-model="rawText" 
        rows="10" 
        placeholder="直接粘贴题目完整内容，包括选项、答案（如有）...

例如：
甲、乙两人分别从 A、B 两地同时出发，相向而行。甲的速度是乙的 1.5 倍...
A. 1.2  B. 1.5  C. 1.8  D. 2.0  E. 2.5"
        class="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
      ></textarea>
      
      <button 
        @click="analyze" 
        :disabled="analyzing || !rawText.trim()"
        class="mt-4 btn btn-primary py-3 px-6 text-base disabled:opacity-50"
      >
        <span v-if="analyzing">🔄 AI 分析中...</span>
        <span v-else>🤖 开始AI分析</span>
      </button>
    </div>

    <!-- Step 2: Review & Edit -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Form -->
      <div class="card p-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-bold text-slate-800">第二步：检查并编辑</h2>
          <button @click="analyzed = null" class="btn btn-ghost text-sm">← 重新分析</button>
        </div>
        
        <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {{ error }}
        </div>
        <div v-if="success" class="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4">
          {{ success }}
        </div>

        <form @submit.prevent="saveQuestion" class="space-y-4">
          <!-- ID + Subject -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">题目 ID</label>
              <input v-model="form.id" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">科目</label>
              <select v-model="form.subject" class="w-full px-3 py-2 border border-slate-300 rounded-lg">
                <option value="math">数学</option>
                <option value="logic">逻辑</option>
                <option value="english">英语</option>
              </select>
            </div>
          </div>

          <!-- Type + Difficulty -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">题型</label>
              <select v-model="form.type" class="w-full px-3 py-2 border border-slate-300 rounded-lg">
                <option value="choice">选择题</option>
                <option value="fill">填空题</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">难度</label>
              <select v-model="form.difficulty" class="w-full px-3 py-2 border border-slate-300 rounded-lg">
                <option :value="1">1 - 简单</option>
                <option :value="2">2</option>
                <option :value="3">3 - 中等</option>
                <option :value="4">4</option>
                <option :value="5">5 - 困难</option>
              </select>
            </div>
          </div>

          <!-- Content -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1">题目内容</label>
            <textarea v-model="form.content" rows="3" class="w-full px-3 py-2 border border-slate-300 rounded-lg font-mono text-sm"></textarea>
          </div>

          <!-- Options -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1">选项</label>
            <textarea v-model="form.options" rows="4" class="w-full px-3 py-2 border border-slate-300 rounded-lg font-mono text-sm"></textarea>
          </div>

          <!-- Answer -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1">答案</label>
            <input v-model="form.answer" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg" />
          </div>

          <!-- Explanation -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1">解析 (AI生成)</label>
            <textarea v-model="form.explanation" rows="6" class="w-full px-3 py-2 border border-slate-300 rounded-lg font-mono text-sm"></textarea>
          </div>

          <!-- Knowledge Points & Tags -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">知识点</label>
              <input v-model="form.knowledge_points" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">标签</label>
              <input v-model="form.tags" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg" />
            </div>
          </div>

          <button type="submit" :disabled="saving" class="w-full btn btn-primary py-3 text-base disabled:opacity-50">
            {{ saving ? '保存中...' : '💾 保存题目' }}
          </button>
        </form>
      </div>

      <!-- Preview -->
      <div class="card p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4 pb-3 border-b border-slate-100">预览</h2>
        <div class="prose-content" v-html="previewHtml"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.prose-content {
  color: #334155;
  line-height: 1.75;
}

.prose-content :deep(h2) {
  font-size: 1.1rem;
  font-weight: 700;
  color: #0f172a;
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
}

.prose-content :deep(p) {
  margin-bottom: 0.75rem;
}
</style>
