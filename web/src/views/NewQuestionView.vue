<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'

const router = useRouter()

// Form data
const form = ref({
  id: '',
  source: '2024年管理类联考',
  subject: 'math',
  type: 'choice',
  difficulty: 3,
  knowledge_points: '',
  tags: '',
  content: '',
  options: 'A. \nB. \nC. \nD. \nE. ',
  answer: '',
  explanation: ''
})

const isSubmitting = ref(false)
const error = ref('')
const success = ref('')

// Generate ID suggestion
const suggestedId = computed(() => {
  const year = form.value.source.match(/\d{4}/)?.[0] || '2024'
  return `${year}-${form.value.subject}-q`
})

// Live markdown preview
const previewHtml = computed(() => {
  const md = `## 题目\n${form.value.content}\n\n## 选项\n${form.value.options}\n\n## 答案\n${form.value.answer}\n\n## 解析\n${form.value.explanation}`
  return marked(md)
})

// Submit form
async function submitForm() {
  if (!form.value.id) {
    error.value = '请填写题目ID'
    return
  }
  if (!form.value.content) {
    error.value = '请填写题目内容'
    return
  }
  
  isSubmitting.value = true
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
    setTimeout(() => {
      router.push('/')
    }, 1500)
  } catch (e) {
    error.value = e.message || '保存失败，请检查后端是否启动'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <header class="mb-8">
      <router-link to="/" class="text-slate-500 hover:text-slate-700 text-sm font-medium">← 返回仪表盘</router-link>
      <h1 class="text-3xl font-extrabold text-slate-900 mt-2">新增题目</h1>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Form -->
      <div class="card p-6">
        <form @submit.prevent="submitForm" class="space-y-6">
          <!-- Error/Success Messages -->
          <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {{ error }}
          </div>
          <div v-if="success" class="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
            {{ success }}
          </div>

          <!-- Row: ID + Source -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">题目 ID *</label>
              <input v-model="form.id" type="text" :placeholder="suggestedId + '01'"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">来源</label>
              <input v-model="form.source" type="text"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
            </div>
          </div>

          <!-- Row: Subject + Type + Difficulty -->
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">科目 *</label>
              <select v-model="form.subject"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                <option value="math">数学</option>
                <option value="logic">逻辑</option>
                <option value="english">英语</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">题型</label>
              <select v-model="form.type"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                <option value="choice">选择题</option>
                <option value="fill">填空题</option>
                <option value="essay">论述题</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">难度</label>
              <select v-model="form.difficulty"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500">
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
            <label class="block text-sm font-semibold text-slate-700 mb-1">题目内容 *</label>
            <textarea v-model="form.content" rows="4" placeholder="请输入题目内容..."
              class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"></textarea>
          </div>

          <!-- Options -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1">选项</label>
            <textarea v-model="form.options" rows="5"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"></textarea>
          </div>

          <!-- Answer -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1">答案</label>
            <input v-model="form.answer" type="text" placeholder="C"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>

          <!-- Explanation -->
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1">解析</label>
            <textarea v-model="form.explanation" rows="6" placeholder="解题步骤和技巧..."
              class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"></textarea>
          </div>

          <!-- Tags -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">知识点 (逗号分隔)</label>
              <input v-model="form.knowledge_points" type="text" placeholder="工程问题, 方程"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-1">标签 (逗号分隔)</label>
              <input v-model="form.tags" type="text" placeholder="高频, 易错"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          <!-- Submit -->
          <button type="submit" :disabled="isSubmitting"
            class="w-full btn btn-primary py-3 text-base disabled:opacity-50">
            {{ isSubmitting ? '保存中...' : '保存题目' }}
          </button>
        </form>
      </div>

      <!-- Preview -->
      <div class="card p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4 pb-3 border-b border-slate-100">实时预览</h2>
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
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.prose-content :deep(p) {
  margin-bottom: 0.75rem;
}
</style>
