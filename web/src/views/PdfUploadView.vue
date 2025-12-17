<script setup>
import { ref, onMounted, computed } from 'vue'

const loading = ref(false)
const uploading = ref(false)
const analyzing = ref(false)
const error = ref('')
const successMsg = ref('')

const pdfs = ref([])
const selectedPdf = ref(null)
const selectedImages = ref([])
const analysisResults = ref([])
const isBatchImporting = ref(false)

const allQuestionsCount = computed(() => {
  return analysisResults.value.reduce((acc, curr) => acc + (curr.questions?.length || 0), 0)
})

async function batchImportAll() {
  if (allQuestionsCount.value === 0 || isBatchImporting.value) return
  
  // Collect all non-imported questions
  const pendingQuestions = []
  analysisResults.value.forEach(result => {
    if (result.questions) {
      result.questions.forEach(q => {
        if (!q.imported && !q.importing) {
          pendingQuestions.push(q)
        }
      })
    }
  })
  
  if (pendingQuestions.length === 0) {
    alert('所有题目已录入')
    return
  }
  
  isBatchImporting.value = true
  
  try {
    // Optimistic UI update
    pendingQuestions.forEach(q => q.importing = true)
    
    // Call batch API
    const res = await fetch('http://localhost:8000/api/pdf/batch-import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        questions: pendingQuestions.map(q => ({
          number: q.number,
          content: q.content,
          options: q.options,
          subject: q.subject
        }))
      })
    })
    
    if (!res.ok) throw new Error('批量录入请求失败')
    
    const data = await res.json()
    
    // Update status based on results
    data.results.forEach(result => {
      const q = pendingQuestions.find(pq => pq.number === result.number)
      if (q) {
        q.importing = false
        if (result.success) {
          q.imported = true
        } else {
          q.error = result.error || '录入失败'
        }
      }
    })
    
  } catch (e) {
    pendingQuestions.forEach(q => {
      q.importing = false
      q.error = e.message
    })
  } finally {
    isBatchImporting.value = false
  }
}

async function importQuestion(question) {
  if (question.importing || question.imported) return
  
  question.importing = true
  question.error = null
  
  try {
    const prompt = `
题号：${question.number}
题目：
${question.content}

选项：
${(question.options || []).join('\n')}

科目：${question.subject || 'math'}
`
    
    const res = await fetch('http://localhost:8000/api/questions/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        input_text: prompt,
        mode: 'auto'
      })
    })
    
    if (!res.ok) {
      throw new Error('录入失败，请重试')
    }
    
    const data = await res.json()
    if (data.success) {
      question.imported = true
    } else {
      throw new Error(data.message || '录入失败')
    }
    
  } catch (e) {
    question.error = e.message
  } finally {
    question.importing = false
  }
}

// Preview state
const previewImage = ref(null)
const previewLoading = ref(false)
const previewData = ref('')

async function loadPdfs() {
  loading.value = true
  try {
    const res = await fetch('http://localhost:8000/api/pdf/list')
    if (res.ok) {
      const data = await res.json()
      pdfs.value = data.pdfs
    }
  } catch (e) {
    error.value = '无法加载PDF列表'
  } finally {
    loading.value = false
  }
}

async function uploadPdf(event) {
  const file = event.target.files[0]
  if (!file) return
  
  uploading.value = true
  error.value = ''
  successMsg.value = ''
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await fetch('http://localhost:8000/api/pdf/upload', {
      method: 'POST',
      body: formData
    })
    
    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || '上传失败')
    }
    
    const data = await res.json()
    successMsg.value = `上传成功！共 ${data.total_pages} 页`
    
    await loadPdfs()
    selectPdf(data.pdf_name)
    
  } catch (e) {
    error.value = e.message
  } finally {
    uploading.value = false
    event.target.value = ''
  }
}

function selectPdf(pdfName) {
  const pdf = pdfs.value.find(p => p.name === pdfName)
  if (pdf) {
    selectedPdf.value = pdf
    selectedImages.value = []
    analysisResults.value = []
  }
}

function toggleImageSelection(imageName, event) {
  // Prevent selection when double-clicking for preview
  if (event.detail === 2) return
  
  const idx = selectedImages.value.indexOf(imageName)
  if (idx >= 0) {
    selectedImages.value.splice(idx, 1)
  } else {
    selectedImages.value.push(imageName)
  }
}

async function openPreview(imageName) {
  previewImage.value = imageName
  previewLoading.value = true
  previewData.value = ''
  
  try {
    const res = await fetch(`http://localhost:8000/api/pdf/${selectedPdf.value.name}/image/${imageName}`)
    if (res.ok) {
      const data = await res.json()
      previewData.value = data.image
    }
  } catch (e) {
    error.value = '加载预览失败'
  } finally {
    previewLoading.value = false
  }
}

function closePreview() {
  previewImage.value = null
  previewData.value = ''
}

function selectAll() {
  if (selectedPdf.value) {
    selectedImages.value = [...selectedPdf.value.images]
  }
}

function clearSelection() {
  selectedImages.value = []
}

async function analyzeSelected() {
  if (!selectedPdf.value || selectedImages.value.length === 0) return
  
  analyzing.value = true
  error.value = ''
  analysisResults.value = []
  
  for (const imageName of selectedImages.value) {
    try {
      const res = await fetch('http://localhost:8000/api/pdf/analyze-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pdf_name: selectedPdf.value.name,
          image_name: imageName
        })
      })
      
      if (res.ok) {
        const data = await res.json()
        analysisResults.value.push({
          image: imageName,
          ...data
        })
      } else {
        analysisResults.value.push({
          image: imageName,
          error: '分析失败'
        })
      }
    } catch (e) {
      analysisResults.value.push({
        image: imageName,
        error: e.message
      })
    }
  }
  
  analyzing.value = false
}

onMounted(loadPdfs)
</script>

<template>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <header class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-3xl font-extrabold text-slate-900">📄 PDF真题导入</h1>
        <p class="text-slate-500 mt-1">上传PDF → 转换图片 → AI识别题目</p>
      </div>
      <label class="btn btn-primary cursor-pointer" :class="{ 'opacity-50': uploading }">
        <span v-if="uploading">上传中...</span>
        <span v-else>📤 上传PDF</span>
        <input type="file" accept=".pdf" class="hidden" @change="uploadPdf" :disabled="uploading">
      </label>
    </header>
    
    <!-- Messages -->
    <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-6">
      {{ error }}
    </div>
    <div v-if="successMsg" class="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-xl mb-6">
      {{ successMsg }}
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- PDF List -->
      <div class="lg:col-span-1">
        <div class="card p-6">
          <h2 class="font-bold text-slate-800 mb-4">已上传PDF</h2>
          
          <div v-if="loading" class="text-center py-8 text-slate-500">加载中...</div>
          
          <div v-else-if="pdfs.length === 0" class="text-center py-8 text-slate-400">
            暂无PDF，请上传
          </div>
          
          <div v-else class="space-y-2">
            <div v-for="pdf in pdfs" :key="pdf.name"
                 @click="selectPdf(pdf.name)"
                 class="p-4 rounded-lg cursor-pointer transition-all"
                 :class="selectedPdf?.name === pdf.name ? 'bg-blue-50 border-2 border-blue-400' : 'bg-slate-50 hover:bg-slate-100'">
              <div class="font-medium text-slate-900">{{ pdf.name }}.pdf</div>
              <div class="text-sm text-slate-500">{{ pdf.total }} 页</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Image Grid -->
      <div class="lg:col-span-2">
        <div v-if="!selectedPdf" class="card p-12 text-center text-slate-400">
          请选择左侧PDF查看页面
        </div>
        
        <div v-else class="card p-6">
          <div class="flex justify-between items-center mb-4">
            <div>
              <h2 class="font-bold text-slate-800">{{ selectedPdf.name }} - {{ selectedPdf.total }}页</h2>
              <p class="text-xs text-slate-400 mt-1">单击选择 · 双击预览</p>
            </div>
            <div class="flex gap-2">
              <button @click="selectAll" class="btn btn-ghost text-sm">全选</button>
              <button @click="clearSelection" class="btn btn-ghost text-sm">清空</button>
              
              <!-- Batch Import Button -->
              <button @click="batchImportAll" 
                      class="btn bg-green-500 hover:bg-green-600 text-sm text-white border-none"
                      v-if="analysisResults.length > 0"
                      :disabled="isBatchImporting">
                 <span v-if="isBatchImporting">⚡ 批量录入中...</span>
                 <span v-else>⚡ 批量录入本页 ({{ allQuestionsCount }})</span>
              </button>

              <button @click="analyzeSelected" 
                      class="btn btn-primary text-sm"
                      :disabled="selectedImages.length === 0 || analyzing">
                <span v-if="analyzing">分析中...</span>
                <span v-else>🤖 分析选中 ({{ selectedImages.length }})</span>
              </button>
            </div>
          </div>
          
          <!-- Image Thumbnails -->
          <div class="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-3 max-h-96 overflow-y-auto p-2">
            <div v-for="img in selectedPdf.images" :key="img"
                 @click="toggleImageSelection(img, $event)"
                 @dblclick="openPreview(img)"
                 class="relative cursor-pointer rounded-lg overflow-hidden border-2 transition-all hover:shadow-lg group"
                 :class="selectedImages.includes(img) ? 'border-blue-500 ring-2 ring-blue-200' : 'border-slate-200'">
              <div class="aspect-[3/4] bg-slate-100 flex items-center justify-center">
                <span class="text-2xl font-bold text-slate-400">{{ img.replace('page_', '').replace('.png', '') }}</span>
              </div>
              <!-- Preview hint on hover -->
              <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <span class="text-white text-2xl">🔍</span>
              </div>
              <!-- Selection badge -->
              <div class="absolute top-1 right-1">
                <span v-if="selectedImages.includes(img)" class="w-5 h-5 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs">✓</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Analysis Results -->
        <div v-if="analysisResults.length > 0" class="card p-6 mt-6">
          <h2 class="font-bold text-slate-800 mb-4">🤖 AI识别结果</h2>
          
          <div class="space-y-6">
            <div v-for="result in analysisResults" :key="result.image" class="border border-slate-200 rounded-xl p-4">
              <div class="flex items-center gap-2 mb-3">
                <span class="px-2 py-1 bg-slate-100 rounded text-sm font-medium">{{ result.image }}</span>
                <span v-if="result.error" class="text-red-500 text-sm">{{ result.error }}</span>
                <span v-else-if="result.questions?.length" class="text-green-600 text-sm">
                  发现 {{ result.questions.length }} 道题
                </span>
                <span v-else class="text-slate-400 text-sm">
                  {{ result.page_type === 'other' ? '封面/目录' : result.page_type || '无题目' }}
                </span>
              </div>
              
              <!-- Questions -->
              <div v-if="result.questions?.length" class="space-y-3">
                <div v-for="(q, i) in result.questions" :key="i" class="bg-slate-50 rounded-lg p-3">
                  <div class="flex justify-between items-start mb-2">
                    <div class="font-medium text-slate-900">第 {{ q.number }} 题</div>
                    
                    <button 
                      @click="importQuestion(q)" 
                      class="btn btn-sm text-xs px-3 py-1"
                      :class="q.imported ? 'bg-green-100 text-green-700 cursor-default' : 'btn-outline-primary'"
                      :disabled="q.importing || q.imported">
                      <span v-if="q.importing">⏳ 录入中...</span>
                      <span v-else-if="q.imported">✅ 已录入</span>
                      <span v-else>🔥 一键录入</span>
                    </button>
                  </div>
                  
                  <div class="text-sm text-slate-700 whitespace-pre-wrap">{{ q.content }}</div>
                  <div v-if="q.options?.length" class="text-xs text-slate-500 mt-2 space-y-1">
                    <div v-for="opt in q.options" :key="opt">{{ opt }}</div>
                  </div>
                  
                  <div v-if="q.error" class="text-xs text-red-500 mt-2">
                    {{ q.error }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Image Preview Modal -->
    <div v-if="previewImage" 
         class="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-8"
         @click.self="closePreview">
      <div class="relative max-w-5xl max-h-[90vh] overflow-auto bg-white rounded-2xl shadow-2xl">
        <!-- Header -->
        <div class="sticky top-0 bg-white/90 backdrop-blur px-6 py-4 border-b flex justify-between items-center z-10">
          <div class="font-bold text-slate-900">{{ previewImage }}</div>
          <div class="flex gap-2">
            <button 
              @click="selectedImages.includes(previewImage) ? null : selectedImages.push(previewImage); closePreview()"
              class="btn btn-primary text-sm"
              :disabled="selectedImages.includes(previewImage)">
              {{ selectedImages.includes(previewImage) ? '✓ 已选中' : '+ 选择此页' }}
            </button>
            <button @click="closePreview" class="w-10 h-10 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-xl">
              ✕
            </button>
          </div>
        </div>
        
        <!-- Content -->
        <div class="p-6">
          <div v-if="previewLoading" class="text-center py-20 text-slate-500">
            加载中...
          </div>
          <img v-else-if="previewData" 
               :src="'data:image/png;base64,' + previewData" 
               class="w-full rounded-lg shadow-lg"
               alt="PDF页面预览">
        </div>
      </div>
    </div>
  </div>
</template>
