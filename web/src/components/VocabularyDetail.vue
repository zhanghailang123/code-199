<script setup>
import { ref, computed, watch } from 'vue'
import { marked } from 'marked'
import MarkdownEditor from './MarkdownEditor.vue'

const props = defineProps({
  item: { type: Object, required: true }
})

const emit = defineEmits(['close'])

const isEditing = ref(false)
const saving = ref(false)
const localItem = ref(null)
const rawContent = ref('')

// Initialize (Load full content)
watch(() => props.item, async (newItem) => {
  if (newItem) {
    try {
      // Fetch full details including Markdown content
      const res = await fetch(`http://localhost:8000/api/vocabulary/${newItem.id}`)
      if (res.ok) {
        localItem.value = await res.json()
        // Reconstruct raw content for editor
        // We need to rebuild frontmatter + content if the API separates them
        // API returns { ...frontmatter, content: "markdown body" }
        // We need to reconstruct the file content for the editor
        rawContent.value = buildRawFile(localItem.value)
      }
    } catch (e) {
      console.error(e)
    }
  }
}, { immediate: true })

function buildRawFile(data) {
    const fm = {
        id: data.id,
        word: data.word,
        phonetic: data.phonetic,
        tags: data.tags,
        status: data.status,
        definitions: data.definitions,
        related_questions: data.related_questions
    }
    // Simple YAML stringify
    let yamlStr = '---\n'
    for (const [k, v] of Object.entries(fm)) {
        if (v === undefined) continue
        yamlStr += `${k}: ${JSON.stringify(v)}\n`
    }
    yamlStr += '---\n\n'
    return yamlStr + (data.content || '')
}

async function save() {
    saving.value = true
    try {
        const res = await fetch(`http://localhost:8000/api/vocabulary/${props.item.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: rawContent.value })
        })
        if (res.ok) {
            isEditing.value = false
            emit('close') // or refresh
        }
    } catch(e) {
        alert('Save failed')
    } finally {
        saving.value = false
    }
}

// Parse markdown for View Mode
const parsedView = computed(() => {
    if (!rawContent.value) return null
    // Reuse log similar to Curriculum but simpler
    const parts = rawContent.value.split(/---\r?\n/)
    if (parts.length < 3) return { body: marked(rawContent.value) }
    
    const body = parts.slice(2).join('---\n')
    return {
        html: marked(body)
    }
})

// Tag Editor
const newTagInput = ref('')

async function addTag() {
    const tag = newTagInput.value.trim()
    if (!tag || !localItem.value) return
    
    if (!localItem.value.tags) {
        localItem.value.tags = []
    }
    
    if (!localItem.value.tags.includes(tag)) {
        localItem.value.tags.push(tag)
        // Sync rawContent and auto-save
        rawContent.value = buildRawFile(localItem.value)
        await autoSaveTags()
    }
    
    newTagInput.value = ''
}

async function removeTag(idx) {
    if (!localItem.value || !localItem.value.tags) return
    
    localItem.value.tags.splice(idx, 1)
    // Sync rawContent and auto-save
    rawContent.value = buildRawFile(localItem.value)
    await autoSaveTags()
}

async function autoSaveTags() {
    try {
        await fetch(`http://localhost:8000/api/vocabulary/${props.item.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: rawContent.value })
        })
    } catch (e) {
        console.error('Auto-save failed', e)
    }
}

// Status Toggle
async function cycleStatus() {
    if (!localItem.value) return
    
    const statusOrder = ['not_started', 'learning', 'mastered']
    const currentIdx = statusOrder.indexOf(localItem.value.status || 'not_started')
    const nextIdx = (currentIdx + 1) % statusOrder.length
    localItem.value.status = statusOrder[nextIdx]
    
    // Sync and auto-save
    rawContent.value = buildRawFile(localItem.value)
    await autoSaveTags()
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="bg-[#09090b] w-full max-w-4xl h-[90vh] rounded-2xl flex flex-col border border-zinc-800 shadow-2xl overflow-hidden animate-fade-in relative">
      
      <!-- Header -->
      <div class="p-6 border-b border-zinc-800 bg-zinc-900/50 flex justify-between items-start">
         <div v-if="localItem" class="flex-1">
            <h2 class="text-4xl font-extrabold text-white font-serif tracking-tight mb-1">{{ localItem.word }}</h2>
            <div class="flex items-center gap-3 text-zinc-400 font-mono text-lg mb-3">
                <span>{{ localItem.phonetic }}</span>
                <!-- Clickable Status Toggle -->
                <button 
                   @click="cycleStatus" 
                   class="px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer flex items-center gap-1.5"
                   :class="{
                     'bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30': localItem.status === 'learning',
                     'bg-green-500/20 text-green-300 border border-green-500/30 hover:bg-green-500/30': localItem.status === 'mastered',
                     'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:bg-zinc-700': localItem.status === 'not_started' || !localItem.status
                   }"
                >
                   <span v-if="localItem.status === 'learning'" class="w-2 h-2 rounded-full bg-amber-400"></span>
                   <span v-else-if="localItem.status === 'mastered'" class="w-2 h-2 rounded-full bg-green-400"></span>
                   <span v-else class="w-2 h-2 rounded-full bg-zinc-500"></span>
                   {{ localItem.status === 'learning' ? '学习中' : localItem.status === 'mastered' ? '已掌握' : '未开始' }}
                </button>
            </div>
            
            <!-- Tags Editor -->
            <div class="flex flex-wrap items-center gap-2">
               <span 
                  v-for="(tag, idx) in (localItem.tags || [])" 
                  :key="tag" 
                  class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-300 border border-blue-500/30"
               >
                  {{ tag }}
                  <button @click="removeTag(idx)" class="hover:text-red-400 ml-1 opacity-70 hover:opacity-100">×</button>
               </span>
               <div class="relative">
                  <input 
                     v-model="newTagInput"
                     @keydown.enter.prevent="addTag"
                     type="text" 
                     placeholder="+ 添加标签"
                     class="w-28 bg-transparent border border-dashed border-zinc-700 rounded-full px-3 py-1 text-xs text-zinc-400 focus:outline-none focus:border-blue-500 placeholder:text-zinc-600"
                  >
               </div>
            </div>
         </div>
         <div class="flex gap-2">
            <button @click="isEditing = !isEditing" class="btn btn-ghost text-zinc-400 hover:text-white">
                {{ isEditing ? 'Cancel' : 'Edit' }}
            </button>
            <button v-if="isEditing" @click="save" class="btn btn-primary bg-blue-600 hover:bg-blue-500 text-white px-4 rounded-lg">
                {{ saving ? 'Saving...' : 'Save' }}
            </button>
            <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/10 text-zinc-400">✕</button>
         </div>
      </div>

      <!-- Definitions (View Mode only) -->
      <div v-if="!isEditing && localItem && localItem.definitions" class="px-8 py-6 bg-zinc-900/30 border-b border-zinc-800/50">
         <div v-for="(def, i) in localItem.definitions" :key="i" class="mb-2">
            <span class="text-blue-400 font-bold italic mr-2 text-lg">{{ def.part }}</span>
            <span class="text-zinc-200 text-lg">{{ def.translation }}</span>
            <div class="text-zinc-500 text-sm ml-8">{{ def.text }}</div>
         </div>
      </div>

      <!-- Main Content Area -->
      <div class="flex-1 overflow-hidden bg-[#09090b]">
         <!-- Editor -->
         <MarkdownEditor 
            v-if="isEditing" 
            v-model:value="rawContent" 
            mode="split"
            class="h-full"
         />

         <!-- Rich View -->
         <div v-else class="h-full overflow-y-auto p-8 prose-content scrollbar-custom">
            <div v-if="parsedView" v-html="parsedView.html"></div>
         </div>
      </div>

    </div>
  </div>
</template>

<style>
/* Comprehensive Prose Styling for Vocabulary Detail */
.prose-content {
    color: #d4d4d8;
    line-height: 1.8;
    font-size: 1.05rem;
}

/* Headings */
.prose-content h1 {
    font-size: 1.75rem;
    font-weight: 800;
    color: #fff;
    margin-top: 2rem;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.prose-content h2 {
    font-size: 1.4rem;
    font-weight: 700;
    color: #e2e8f0;
    margin-top: 2rem;
    margin-bottom: 0.75rem;
}

.prose-content h3 {
    font-size: 1.15rem;
    font-weight: 600;
    color: #cbd5e1;
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
}

/* Paragraphs */
.prose-content p {
    margin-bottom: 1.25rem;
}

/* Lists */
.prose-content ul, .prose-content ol {
    margin-left: 1.5rem;
    margin-bottom: 1.25rem;
    padding-left: 0.5rem;
}

.prose-content ul {
    list-style-type: disc;
}

.prose-content ol {
    list-style-type: decimal;
}

.prose-content li {
    margin-bottom: 0.5rem;
    color: #d4d4d8;
}

.prose-content li::marker {
    color: #60a5fa;
}

/* Strong / Bold */
.prose-content strong {
    color: #fff;
    font-weight: 600;
}

/* Italic / Emphasis */
.prose-content em {
    color: #fbbf24;
    font-style: italic;
}

/* Blockquotes */
.prose-content blockquote {
    border-left: 4px solid #3b82f6;
    padding-left: 1rem;
    margin: 1.5rem 0;
    font-style: italic;
    color: #94a3b8;
    background: rgba(59, 130, 246, 0.05);
    padding: 1rem 1.5rem;
    border-radius: 0 8px 8px 0;
}

/* Inline Code */
.prose-content code {
    background-color: rgba(255,255,255,0.1);
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    font-size: 0.9em;
    color: #a5b4fc;
    font-family: 'Fira Code', 'JetBrains Mono', monospace;
}

/* Code Blocks */
.prose-content pre {
    background-color: #1f1f23;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 1rem;
    overflow-x: auto;
    margin: 1.5rem 0;
}

.prose-content pre code {
    background: transparent;
    padding: 0;
}

/* Tables */
.prose-content table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5rem 0;
}

.prose-content th, .prose-content td {
    border: 1px solid rgba(255,255,255,0.1);
    padding: 0.75rem 1rem;
    text-align: left;
}

.prose-content th {
    background-color: rgba(255,255,255,0.05);
    font-weight: 600;
    color: #e2e8f0;
}

/* Horizontal Rules */
.prose-content hr {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.1);
    margin: 2rem 0;
}

/* Links */
.prose-content a {
    color: #60a5fa;
    text-decoration: underline;
}

.prose-content a:hover {
    color: #93c5fd;
}
</style>
