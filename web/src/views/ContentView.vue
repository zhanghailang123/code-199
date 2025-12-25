<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import MarkdownEditor from '../components/MarkdownEditor.vue'

const route = useRoute()
const loading = ref(true)
const error = ref('')
const rawContent = ref('')
const isEditing = ref(false)
const saving = ref(false)
const localMeta = ref({})

// Helper to extract frontmatter
function parseFrontmatter(text) {
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/)
  if (!match) return { meta: {}, content: text }
  
  const metaText = match[1]
  const content = match[2]
  const meta = {}
  
  metaText.split('\n').forEach(line => {
    const colonIndex = line.indexOf(':')
    if (colonIndex > 0) {
      const key = line.substring(0, colonIndex).trim()
      let value = line.substring(colonIndex + 1).trim()
      // Remove quotes if present
      if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        value = value.substring(1, value.length - 1)
      }
      meta[key] = value
    }
  })
  
  return { meta, content }
}

async function fetchContent() {
  loading.value = true
  error.value = ''
  
  const id = route.params.id
  const category = route.params.category
  const routeName = route.name
  
  try {
    let apiUrl = ''
    if (routeName === 'knowledge' && category) {
      apiUrl = `http://localhost:8000/api/knowledge/${category}/${id}`
    } else {
      apiUrl = `http://localhost:8000/api/questions/${id}`
    }
    
    const res = await fetch(apiUrl)
    if (!res.ok) throw new Error('内容未找到')
    
    const data = await res.json()
    rawContent.value = data.raw || ''
    
    // Parse meta for header display
    const { meta } = parseFrontmatter(rawContent.value)
    localMeta.value = meta
    
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function saveContent() {
  if (!rawContent.value) return
  saving.value = true
  
  const id = route.params.id
  const category = route.params.category
  const routeName = route.name
  
  try {
    let apiUrl = ''
    if (routeName === 'knowledge' && category) {
      apiUrl = `http://localhost:8000/api/knowledge/${category}/${id}/content`
    } else {
      apiUrl = `http://localhost:8000/api/questions/${id}/content`
    }
    
    const res = await fetch(apiUrl, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: rawContent.value })
    })
    
    if (!res.ok) throw new Error('保存失败')
    
    isEditing.value = false
    await fetchContent() // Reload
    
  } catch (e) {
    alert('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}

onMounted(fetchContent)
watch(() => route.params.id, fetchContent)

// View helpers
const difficultyStars = computed(() => {
  const diff = parseInt(localMeta.value.difficulty) || 3
  return '★'.repeat(diff) + '☆'.repeat(5 - diff)
})

const subjectLabel = computed(() => {
  const map = { math: '数学', logic: '逻辑', english: '英语' }
  const sub = localMeta.value.subject || route.params.category || 'unknown'
  return map[sub] || sub
})
</script>

<template>
  <div class="min-h-screen bg-[#09090b] text-zinc-200">
    <!-- Navbar -->
    <nav class="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-40">
      <div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <button @click="$router.back()" class="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors text-sm font-medium">
            <span class="text-lg">←</span> Back
          </button>
          <div class="h-6 w-px bg-zinc-800"></div>
          <h1 class="font-mono font-bold text-zinc-300 truncate max-w-md">{{ localMeta.id || route.params.id }}</h1>
        </div>
        
        <div class="flex items-center gap-3">
           <span v-if="saving" class="text-xs text-zinc-500 animate-pulse">Saving...</span>
           <button @click="isEditing = !isEditing" class="btn btn-ghost text-zinc-400 hover:text-white">
                {{ isEditing ? 'Cancel' : 'Edit' }}
            </button>
            <button v-if="isEditing" @click="saveContent" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-colors shadow-lg shadow-blue-900/20">
                {{ saving ? 'Saving...' : 'Save Changes' }}
            </button>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="h-[calc(100vh-64px)] overflow-hidden flex flex-col">
       <!-- Header Section (Metadata) -->
       <header v-if="!isEditing && !loading" class="bg-[#0c0c0e] border-b border-zinc-800/50 px-8 py-8">
          <div class="max-w-5xl mx-auto">
             <div class="flex flex-wrap items-center gap-4 mb-4">
                <span class="px-3 py-1 rounded-full text-xs font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase tracking-wider">
                  {{ subjectLabel }}
                </span>
                <span v-if="localMeta.type" class="px-3 py-1 rounded-full text-xs font-medium bg-zinc-800 text-zinc-400 border border-zinc-700">
                  {{ localMeta.type }}
                </span>
                <span v-if="localMeta.difficulty" class="text-amber-400 text-sm tracking-widest">
                  {{ difficultyStars }}
                </span>
             </div>
             
             <h1 class="text-3xl md:text-4xl font-extrabold text-white font-serif tracking-tight mb-6 leading-tight">
               {{ localMeta.title || 'Untitled Question' }}
             </h1>
             
             <!-- Meta Grid -->
             <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm font-mono text-zinc-500">
               <div v-if="localMeta.source" class="flex flex-col">
                 <span class="text-xs text-zinc-600 uppercase mb-1">Source</span>
                 <span class="text-zinc-300">{{ localMeta.source }}</span>
               </div>
               <div v-if="localMeta.date" class="flex flex-col">
                 <span class="text-xs text-zinc-600 uppercase mb-1">Date</span>
                 <span class="text-zinc-300">{{ localMeta.date }}</span>
               </div>
               <div v-if="localMeta.tags" class="col-span-2 flex flex-col">
                 <span class="text-xs text-zinc-600 uppercase mb-1">Tags</span>
                 <div class="flex gap-2">
                    <span v-for="tag in (localMeta.tags || '').split(',')" :key="tag" class="text-zinc-400 hover:text-white transition-colors">#{{ tag.trim() }}</span>
                 </div>
               </div>
             </div>
          </div>
       </header>

       <!-- Content Body -->
       <div class="flex-1 overflow-hidden relative">
          <!-- Loading State -->
          <div v-if="loading" class="absolute inset-0 flex items-center justify-center">
             <div class="w-8 h-8 border-2 border-zinc-600 border-t-zinc-200 rounded-full animate-spin"></div>
          </div>
          
          <!-- Editor Mode -->
          <MarkdownEditor 
            v-if="isEditing" 
            v-model:value="rawContent" 
            mode="split"
            class="h-full"
          />
          
          <!-- View Mode -->
          <div v-else class="h-full overflow-y-auto bg-[#09090b]">
             <div class="max-w-5xl mx-auto px-8 py-10">
                <!-- Use the Markdown Viewer -->
                <MarkdownEditor 
                  :value="rawContent" 
                  mode="split" 
                  :readonly="true"
                />
             </div>
          </div>
       </div>
    </main>
  </div>
</template>

<style scoped>
/* Reuse styles from VocabularyDetail if needed, but MarkdownEditor handles most of it */
/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: #27272a;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #3f3f46;
}
</style>
