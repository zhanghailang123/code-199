<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { API_BASE } from '../config/api.js'
import VocabularyDetail from '../components/VocabularyDetail.vue'

const router = useRouter()
const loading = ref(true)
const isCreating = ref(false) // New state for button-level loading
const items = ref([])
const searchQuery = ref('')
const selectedItem = ref(null)
const selectedTag = ref('all')

// Load vocabulary
async function loadVocabulary(silent = false) {
  if (!silent) loading.value = true
  try {
    const res = await fetch(`${API_BASE}/api/vocabulary`)
    const data = await res.json()
    items.value = data.items
  } catch (e) {
    console.error('Failed to load vocabulary', e)
  } finally {
    loading.value = false
  }
}

// Extract all unique tags
const allTags = computed(() => {
    const tags = new Set()
    items.value.forEach(item => {
        if (Array.isArray(item.tags)) {
            item.tags.forEach(t => tags.add(t))
        }
    })
    return Array.from(tags).sort()
})

// Filter items
const filteredItems = computed(() => {
  let result = items.value
  
  // Tag Filter
  if (selectedTag.value !== 'all') {
      result = result.filter(item => Array.isArray(item.tags) && item.tags.includes(selectedTag.value))
  }

  // Search Filter
  if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      result = result.filter(item => {
        const wordMatch = (item.word || '').toLowerCase().includes(q)
        const defMatch = Array.isArray(item.definitions) && item.definitions.some(d => (d.translation || '').includes(q))
        return wordMatch || defMatch
      })
  }
  
  // Sort alphabetically
  result = [...result].sort((a, b) => (a.word || '').localeCompare(b.word || ''))
  
  return result
})

// Group items by first letter
const groupedItems = computed(() => {
    const groups = {}
    filteredItems.value.forEach(item => {
        const letter = (item.word || '?')[0].toUpperCase()
        if (!groups[letter]) groups[letter] = []
        groups[letter].push(item)
    })
    // Return sorted letters
    return Object.keys(groups).sort().map(letter => ({
        letter,
        items: groups[letter]
    }))
})

// All letters that have items
const activeLetters = computed(() => {
    return new Set(groupedItems.value.map(g => g.letter))
})

// Scroll to letter section
function scrollToLetter(letter) {
    const el = document.getElementById(`letter-${letter}`)
    if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
}

// Custom Modal Logic
const showAddModal = ref(false)
const newWordInput = ref('')
const isAutoGenerate = ref(true)
const wordInputRef = ref(null)

// Focus input when modal opens
import { watch, nextTick } from 'vue'
watch(showAddModal, (newVal) => {
    if (newVal) {
        nextTick(() => {
            wordInputRef.value?.focus()
        })
    }
})

// Create new word (Modal Confirmation)
async function confirmCreateWord() {
  const word = newWordInput.value.trim()
  if (!word) return
  
  // Close modal immediately so user can continue
  showAddModal.value = false
  newWordInput.value = ''
  
  const id = 'vocab-' + word.toLowerCase().replace(/[^a-z0-9]/g, '-')
  const autoGen = isAutoGenerate.value // Capture value before reset
  
  isCreating.value = true
  
  try {
    const res = await fetch(`${API_BASE}/api/vocabulary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
          id, 
          word, 
          category: 'english',
          auto_generate: autoGen
      })
    })
    
    if (res.ok) {
        await loadVocabulary(true) // Silent refresh
        // Find the new item and open it (optional, maybe distracting if user moved on? kept for now)
        const newItem = items.value.find(i => i.id === id)
        if (newItem) selectedItem.value = newItem
    } else {
        alert('创建失败，可能单词已存在')
    }
  } catch (e) {
    alert('创建失败: ' + e.message)
  } finally {
    isCreating.value = false
  }
}

// Fallback for FAB click (just triggers modal, logic is now in confirmCreateWord)
function createWord() {
    showAddModal.value = true
    newWordInput.value = ''
    isAutoGenerate.value = true
}

// Copy functionality
const copiedId = ref(null)
async function copyToClipboard(text, id, e) {
  e.stopPropagation() // Prevent opening modal
  try {
    await navigator.clipboard.writeText(text)
    copiedId.value = id
    setTimeout(() => {
      copiedId.value = null
    }, 1500)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

// Delete word
async function deleteWord(item, e) {
  e.stopPropagation() // Prevent card click
  if (!confirm(`确定要删除单词 "${item.word}" 吗？\n此操作不可恢复。`)) return
  
  try {
    const res = await fetch(`${API_BASE}/api/vocabulary/${item.id}`, {
      method: 'DELETE'
    })
    
    if (res.ok) {
      // Remove from local list
      items.value = items.value.filter(i => i.id !== item.id)
      // Close detail if open
      if (selectedItem.value && selectedItem.value.id === item.id) {
        selectedItem.value = null
      }
    } else {
      alert('删除失败')
    }
  } catch (e) {
    alert('删除失败: ' + e.message)
  }
}

onMounted(() => {
  loadVocabulary()
})
</script>

<template>
  <div class="max-w-7xl mx-auto p-4 md:p-8">
    <!-- Header -->
    <header class="flex flex-col gap-6 mb-8">
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 class="text-3xl font-extrabold text-white tracking-tight">🔤 单词本</h1>
          <p class="text-zinc-500 mt-1">积累词汇，积少成多</p>
        </div>
        
        <div class="flex items-center gap-3 w-full md:w-auto">
          <div class="relative flex-1 md:w-64">
             <input 
               v-model="searchQuery"
               type="text" 
               placeholder="搜索单词..." 
               class="w-full bg-zinc-900 border border-zinc-700 rounded-xl py-2.5 pr-4 text-zinc-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder:text-zinc-600 shadow-inner"
               style="padding-left: 3rem;"
             >
             <span class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none">🔍</span>
          </div>
          <!-- Button moved to FAB -->
        </div>
      </div>

      <!-- Tag Filters -->
      <div class="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
        <button 
            @click="selectedTag = 'all'"
            class="px-3 py-1.5 rounded-full text-sm font-medium transition-all whitespace-nowrap border"
            :class="selectedTag === 'all' 
                ? 'bg-white text-black border-white' 
                : 'bg-zinc-900 text-zinc-400 border-zinc-800 hover:border-zinc-700 hover:text-zinc-200'"
        >
            全部
        </button>
        <button 
            v-for="tag in allTags" 
            :key="tag"
            @click="selectedTag = tag"
            class="px-3 py-1.5 rounded-full text-sm font-medium transition-all whitespace-nowrap border"
            :class="selectedTag === tag 
                ? 'bg-blue-500/20 text-blue-300 border-blue-500/50' 
                : 'bg-zinc-900 text-zinc-400 border-zinc-800 hover:border-zinc-700 hover:text-zinc-200'"
        >
            {{ tag }}
        </button>
      </div>
    </header>
    
    <!-- Grid Layout -->
    <div v-if="loading" class="flex justify-center py-20">
       <div class="animate-spin w-8 h-8 border-2 border-zinc-600 border-t-zinc-200 rounded-full"></div>
    </div>
    
    <div v-else-if="filteredItems.length === 0" class="text-center py-20 text-zinc-500">
       {{ searchQuery || selectedTag !== 'all' ? '未找到匹配的单词' : '还没有单词，快去添加吧！' }}
    </div>

    <!-- Main Content Area with Sidebar -->
    <div v-else class="flex gap-6">
      <!-- Cards Grid (Grouped by Letter) -->
      <div class="flex-1 space-y-8">
        <div v-for="group in groupedItems" :key="group.letter" :id="`letter-${group.letter}`">
          <!-- Letter Header -->
          <div class="flex items-center gap-3 mb-4 sticky top-0 z-10 bg-[#09090b]/90 backdrop-blur-sm py-2">
            <span class="text-3xl font-black text-blue-500/80">{{ group.letter }}</span>
            <div class="flex-1 h-px bg-gradient-to-r from-blue-500/30 to-transparent"></div>
            <span class="text-xs text-zinc-600">{{ group.items.length }} 词</span>
          </div>
          
          <!-- Cards for this letter -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div 
              v-for="item in group.items" 
              :key="item.id"
              @click="selectedItem = item"
              class="bg-gradient-to-br from-zinc-900 to-zinc-900/80 border border-zinc-800 rounded-xl p-5 hover:border-blue-500/30 hover:shadow-lg hover:shadow-blue-500/5 hover:-translate-y-1 transition-all duration-300 cursor-pointer group relative overflow-hidden"
            >
              <!-- Left Accent Bar -->
              <div class="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-500 to-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity rounded-l-xl"></div>
              
              <!-- Top Glow -->
              <div class="absolute top-0 left-0 right-0 h-16 bg-gradient-to-b from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
              
              <div class="relative">
                <div class="flex justify-between items-start mb-2">
                   <div class="flex items-center gap-2">
                       <h3 class="text-xl font-bold text-white tracking-tight font-serif group-hover:text-blue-100 transition-colors">{{ item.word }}</h3>
                       <button 
                         @click="(e) => copyToClipboard(item.word, item.id, e)"
                         class="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-white/10 rounded flex items-center justify-center text-zinc-500 hover:text-white"
                         :class="{ '!opacity-100 text-green-400': copiedId === item.id }"
                         title="复制单词"
                       >
                         <span v-if="copiedId === item.id" class="text-xs">✓</span>
                         <span v-else class="text-xs">📋</span>
                       </button>
                       <button 
                         @click="(e) => deleteWord(item, e)"
                         class="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-500/10 rounded flex items-center justify-center text-zinc-500 hover:text-red-400"
                         title="删除单词"
                       >
                         <span class="text-xs">🗑️</span>
                       </button>
                   </div>
                   <div class="flex items-center gap-2">
                     <span v-if="item.status === 'mastered'" class="w-2.5 h-2.5 rounded-full bg-green-500 shadow-lg shadow-green-500/50"></span>
                     <span v-else-if="item.status === 'learning'" class="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-lg shadow-amber-500/50"></span>
                   </div>
                </div>
                
                <div class="text-xs font-mono text-zinc-500 mb-2">{{ item.phonetic || '/.../' }}</div>
                
                <div class="space-y-1 mb-3">
                  <div v-for="(def, idx) in (item.definitions || []).slice(0, 1)" :key="idx" class="text-zinc-400 text-sm leading-snug line-clamp-2">
                    <span class="text-blue-400/70 italic mr-1 font-medium">{{ def.part }}</span>
                    <span class="text-zinc-300">{{ def.translation }}</span>
                  </div>
                </div>

                <!-- Tags -->
                <div class="flex flex-wrap gap-1 pt-2 border-t border-zinc-800/50">
                   <span v-if="!item.tags || item.tags.length === 0" class="text-[10px] text-zinc-600 italic">无标签</span>
                   <span v-for="tag in (item.tags || []).slice(0,2)" :key="tag" 
                         class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                     {{ tag }}
                   </span>
                   <span v-if="(item.tags?.length || 0) > 2" class="text-[9px] text-zinc-500">+{{ item.tags.length - 2 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- A-Z Sidebar -->
      <div class="hidden lg:flex flex-col items-center gap-1 sticky top-4 h-fit py-2 px-1 bg-zinc-900/50 rounded-xl border border-zinc-800">
        <button 
          v-for="letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')" 
          :key="letter"
          @click="scrollToLetter(letter)"
          class="w-6 h-6 flex items-center justify-center text-xs font-bold rounded transition-all"
          :class="activeLetters.has(letter) 
            ? 'text-blue-400 hover:bg-blue-500/20 cursor-pointer' 
            : 'text-zinc-700 cursor-default'"
        >
          {{ letter }}
        </button>
      </div>
    </div>

    <!-- Detail Modal -->
    <VocabularyDetail 
       v-if="selectedItem" 
       :item="selectedItem" 
       @close="selectedItem = null; loadVocabulary(true)" 
    />

    <!-- Floating Action Button (Add Word) -->
    <button 
      @click="showAddModal = true; isAutoGenerate = true; newWordInput = ''"
      :disabled="isCreating"
      class="fixed top-1/2 right-6 -translate-y-1/2 z-40 w-14 h-14 bg-blue-600 hover:bg-blue-500 rounded-full shadow-lg shadow-blue-600/30 flex items-center justify-center transition-all hover:scale-105 active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed group select-none"
      title="添加新单词"
    >
        <div v-if="isCreating" class="animate-spin w-6 h-6 border-2 border-white/30 border-t-white rounded-full"></div>
        <span v-else class="text-4xl text-white font-light leading-none -mt-1 group-hover:rotate-90 transition-transform duration-300 pointer-events-none">+</span>
    </button>

    <!-- Custom Add Word Modal -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="showAddModal = false"></div>
        
        <!-- Modal Card -->
        <div class="relative bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-sm shadow-2xl p-6 overflow-hidden">
            <!-- Header -->
            <div class="mb-6 text-center">
                <h3 class="text-xl font-bold text-white mb-1">添加新单词</h3>
                <p class="text-zinc-500 text-sm">Add a new word to your collection</p>
            </div>

            <!-- Input -->
            <div class="mb-6">
                <input 
                  v-model="newWordInput"
                  ref="wordInputRef"
                  type="text" 
                  placeholder="Type word here..." 
                  class="w-full bg-zinc-950 border border-zinc-700 rounded-xl px-4 py-3 text-lg text-white placeholder:text-zinc-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-center"
                  @keyup.enter="confirmCreateWord"
                  autofocus
                >
            </div>

            <!-- AI Toggle -->
            <div class="mb-8 flex items-center justify-center gap-3 cursor-pointer select-none" @click="isAutoGenerate = !isAutoGenerate">
                <div class="w-10 h-6 rounded-full relative transition-colors duration-200" 
                     :class="isAutoGenerate ? 'bg-blue-600' : 'bg-zinc-700'">
                    <div class="absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform duration-200"
                         :class="isAutoGenerate ? 'translate-x-4' : 'translate-x-0'"></div>
                </div>
                <span class="text-sm font-medium" :class="isAutoGenerate ? 'text-blue-100' : 'text-zinc-400'">
                    {{ isAutoGenerate ? 'AI 自动生成笔记' : '仅创建单词' }}
                </span>
            </div>

            <!-- Actions -->
            <div class="flex gap-3">
                <button 
                  @click="showAddModal = false"
                  class="flex-1 px-4 py-2.5 rounded-xl border border-zinc-700 text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors text-sm font-medium"
                >
                  取消
                </button>
                <button 
                  @click="confirmCreateWord"
                  :disabled="!newWordInput.trim() || isCreating"
                  class="flex-1 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm font-bold flex items-center justify-center gap-2"
                >
                  <div v-if="isCreating" class="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></div>
                  {{ isCreating ? '生成中...' : '确认添加' }}
                </button>
            </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* Masonry fallback using columns */
</style>
