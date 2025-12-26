<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { marked } from 'marked'
import { API_BASE } from '../config/api.js'
import MarkdownEditor from './MarkdownEditor.vue'
import NoteBubble from './NoteBubble.vue'

const props = defineProps({
  item: { type: Object, required: true }
})

const emit = defineEmits(['close'])

const isEditing = ref(false)
const saving = ref(false)
const regenerating = ref(false)
const localItem = ref(null)
const rawContent = ref('')

// Initialize (Load full content)
watch(() => props.item, async (newItem) => {
  if (newItem) {
    try {
      // Fetch full details including Markdown content
      const res = await fetch(`${API_BASE}/api/vocabulary/${newItem.id}`)
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
        related_questions: data.related_questions,
        notes: data.notes || []
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
        const res = await fetch(`${API_BASE}/api/vocabulary/${props.item.id}`, {
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

// Regenerate content using LLM
async function regenerate() {
    if (!localItem.value || regenerating.value) return
    
    regenerating.value = true
    try {
        const res = await fetch(`${API_BASE}/api/vocabulary/${props.item.id}/regenerate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        if (res.ok) {
            const data = await res.json()
            if (data.success && data.content) {
                rawContent.value = data.content
                // Also re-fetch to update localItem
                const refreshRes = await fetch(`${API_BASE}/api/vocabulary/${props.item.id}`)
                if (refreshRes.ok) {
                    localItem.value = await refreshRes.json()
                }
            }
        } else {
            alert('重新生成失败，请稍后重试')
        }
    } catch (e) {
        console.error('重新生成失败:', e)
        alert('重新生成失败')
    } finally {
        regenerating.value = false
    }
}

// Parse markdown for View Mode
const parsedView = computed(() => {
    if (!rawContent.value) return null
    const parts = rawContent.value.split(/---\r?\n/)
    if (parts.length < 3) return { body: marked(rawContent.value) }
    
    const body = parts.slice(2).join('---\n')
    return {
        html: marked(body)
    }
})

// Content ref for DOM manipulation
const contentRef = ref(null)
const activeNoteAnchor = ref(null)
const activeNoteBubblePos = ref({ top: 0, left: 0 })

// Inject note icons into headings after render
function injectNoteIcons() {
    if (!contentRef.value || isEditing.value) return
    
    nextTick(() => {
        const headings = contentRef.value.querySelectorAll('h3')
        headings.forEach((h3) => {
            // Skip if already has icon
            if (h3.querySelector('.note-icon-inline')) return
            
            const anchor = '### ' + h3.textContent.trim()
            const hasNote = getNoteByAnchor(anchor)
            
            // Create wrapper for icon + tooltip
            const wrapper = document.createElement('span')
            wrapper.className = 'note-icon-wrapper'
            wrapper.style.cssText = 'position: relative; display: inline-block; margin-left: 8px; vertical-align: middle;'
            
            // Create icon button
            const iconBtn = document.createElement('button')
            iconBtn.className = 'note-icon-inline'
            iconBtn.innerHTML = hasNote ? '📝' : '➕'
            iconBtn.title = hasNote ? '点击编辑笔记' : '添加笔记'
            iconBtn.style.cssText = 'cursor: pointer; font-size: 14px; opacity: 0.6; transition: opacity 0.2s; background: none; border: none;'
            
            // Create hover tooltip for existing notes
            let tooltip = null
            if (hasNote) {
                tooltip = document.createElement('div')
                tooltip.className = 'note-hover-tooltip'
                tooltip.innerHTML = `<div style="font-size:11px;color:#a1a1aa;margin-bottom:4px;">📝 笔记</div><div style="color:#e4e4e7;font-size:13px;white-space:pre-wrap;">${hasNote.content}</div><div style="font-size:10px;color:#52525b;margin-top:6px;">点击编辑</div>`
                tooltip.style.cssText = 'display:none; position:absolute; top:100%; left:0; margin-top:8px; min-width:200px; max-width:300px; padding:12px; background:#18181b; border:1px solid #3f3f46; border-radius:8px; box-shadow:0 8px 24px rgba(0,0,0,0.5); z-index:1000; pointer-events:none;'
                wrapper.appendChild(tooltip)
            }
            
            iconBtn.onmouseenter = () => {
                iconBtn.style.opacity = '1'
                if (tooltip) tooltip.style.display = 'block'
            }
            iconBtn.onmouseleave = () => {
                iconBtn.style.opacity = '0.6'
                if (tooltip) tooltip.style.display = 'none'
            }
            iconBtn.onclick = (e) => {
                e.stopPropagation()
                if (tooltip) tooltip.style.display = 'none'
                const rect = h3.getBoundingClientRect()
                const existingNote = getNoteByAnchor(anchor)
                editingNoteContent.value = existingNote?.content || ''
                activeNoteBubblePos.value = { top: rect.bottom + 10, left: rect.left }
                activeNoteAnchor.value = anchor
            }
            
            wrapper.appendChild(iconBtn)
            h3.appendChild(wrapper)
        })
    })
}

// Watch for content changes and re-inject icons
watch([parsedView, isEditing], () => {
    if (!isEditing.value) {
        setTimeout(injectNoteIcons, 100)
    }
})

// Editing state for floating popup
const editingNoteContent = ref('')

// Close active note bubble
function closeNoteBubble() {
    activeNoteAnchor.value = null
    editingNoteContent.value = ''
}

// Open note popup and load existing content
function openNotePopup(anchor, rect) {
    const existingNote = getNoteByAnchor(anchor)
    editingNoteContent.value = existingNote?.content || ''
    activeNoteBubblePos.value = { top: rect.bottom + 10, left: rect.left }
    activeNoteAnchor.value = anchor
}

// Save current note from popup
async function saveCurrentNote() {
    if (!activeNoteAnchor.value || !editingNoteContent.value.trim()) return
    
    console.log('[Notes] Saving note:', activeNoteAnchor.value, editingNoteContent.value)
    
    await saveNote({
        anchor: activeNoteAnchor.value,
        content: editingNoteContent.value.trim()
    })
    
    closeNoteBubble()
    // Re-inject to update icons
    setTimeout(() => {
        // Clear existing icons first
        if (contentRef.value) {
            contentRef.value.querySelectorAll('.note-icon-inline').forEach(el => el.remove())
        }
        injectNoteIcons()
    }, 200)
}

// Confirm and delete note
async function confirmDeleteNote() {
    if (!activeNoteAnchor.value) return
    if (!confirm('确定删除这条笔记吗？')) return
    
    await deleteNote(activeNoteAnchor.value)
    closeNoteBubble()
    // Re-inject to update icons
    setTimeout(() => {
        if (contentRef.value) {
            contentRef.value.querySelectorAll('.note-icon-inline').forEach(el => el.remove())
        }
        injectNoteIcons()
    }, 200)
}

// Handle save from floating bubble (legacy, keeping for compatibility)
async function handleNoteSave(data) {
    await saveNote(data)
    closeNoteBubble()
    setTimeout(injectNoteIcons, 100)
}

// Handle delete from floating bubble (legacy)
async function handleNoteDelete(anchor) {
    await deleteNote(anchor)
    closeNoteBubble()
    setTimeout(injectNoteIcons, 100)
}

// Extract section anchors (headings) for notes
const sectionAnchors = computed(() => {
    if (!rawContent.value) return []
    const headingMatch = rawContent.value.match(/^###\s+.+$/gm)
    return headingMatch || []
})

// Get notes from localItem
const notes = computed(() => localItem.value?.notes || [])

// Find note by anchor
function getNoteByAnchor(anchor) {
    return notes.value.find(n => n.anchor === anchor)
}

// Save note
async function saveNote({ anchor, content }) {
    if (!localItem.value) return
    
    if (!localItem.value.notes) {
        localItem.value.notes = []
    }
    
    const existingIdx = localItem.value.notes.findIndex(n => n.anchor === anchor)
    const noteData = {
        id: existingIdx >= 0 ? localItem.value.notes[existingIdx].id : `note-${Date.now()}`,
        anchor,
        content,
        created: existingIdx >= 0 ? localItem.value.notes[existingIdx].created : new Date().toISOString().split('T')[0],
        updated: new Date().toISOString().split('T')[0]
    }
    
    if (existingIdx >= 0) {
        localItem.value.notes[existingIdx] = noteData
    } else {
        localItem.value.notes.push(noteData)
    }
    
    rawContent.value = buildRawFile(localItem.value)
    await autoSaveTags()
}

// Delete note
async function deleteNote(anchor) {
    if (!localItem.value?.notes) return
    
    const idx = localItem.value.notes.findIndex(n => n.anchor === anchor)
    if (idx >= 0) {
        localItem.value.notes.splice(idx, 1)
        rawContent.value = buildRawFile(localItem.value)
        await autoSaveTags()
    }
}

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
        await fetch(`${API_BASE}/api/vocabulary/${props.item.id}`, {
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

// Sync isEditing with layout
watch(isEditing, () => {
    nextTick(() => {
        window.dispatchEvent(new Event('resize'));
    });
})

// Body Scroll Lock & Modal Logic
onMounted(() => {
  document.body.classList.add('is-modal-open')
  document.documentElement.classList.add('is-modal-open')
  
  nextTick(() => {
    window.dispatchEvent(new Event('resize'));
  });
})

onUnmounted(() => {
  document.body.classList.remove('is-modal-open')
  document.documentElement.classList.remove('is-modal-open')
})
</script>

<template>
  <div class="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-hidden" 
       @click.self="$emit('close')"
       @wheel.stop>
    <div class="bg-[#09090b] w-full max-w-6xl h-[90vh] max-h-[90vh] rounded-2xl grid grid-rows-[auto_1fr] border border-zinc-800 shadow-2xl overflow-hidden animate-fade-in relative">
      
      <!-- Header (Row 1) -->
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
            <button 
               @click="regenerate" 
               :disabled="regenerating"
               class="btn text-zinc-400 hover:text-white flex items-center gap-1.5"
               :class="regenerating ? 'opacity-50 cursor-wait' : 'hover:bg-white/5'"
               title="重新生成内容"
            >
               <span v-if="regenerating" class="animate-spin">🔄</span>
               <span v-else>🔄</span>
               <span class="text-sm">{{ regenerating ? '生成中...' : '重新生成' }}</span>
            </button>
            <button @click="isEditing = !isEditing" class="btn btn-ghost text-zinc-400 hover:text-white">
                {{ isEditing ? 'Cancel' : 'Edit' }}
            </button>
            <button v-if="isEditing" @click="save" class="btn btn-primary bg-blue-600 hover:bg-blue-500 text-white px-4 rounded-lg">
                {{ saving ? 'Saving...' : 'Save' }}
            </button>
            <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/10 text-zinc-400">✕</button>
         </div>
      </div>

      <!-- Main Container (Row 2) -->
      <div class="min-h-0 flex flex-col overflow-hidden relative">
         <!-- Definitions (View Mode only) -->
         <div v-if="!isEditing && localItem && localItem.definitions" class="flex-none px-8 py-4 bg-zinc-900/30 border-b border-zinc-800/50 overflow-y-auto max-h-[30%]">
            <div v-for="(def, i) in localItem.definitions" :key="i" class="mb-2">
               <span class="text-blue-400 font-bold italic mr-2 text-lg">{{ def.part }}</span>
               <span class="text-zinc-200 text-lg">{{ def.translation }}</span>
               <div class="text-zinc-500 text-sm ml-8">{{ def.text }}</div>
            </div>
         </div>

         <!-- Editor/Content Area -->
         <div class="flex-1 min-h-0 overflow-hidden bg-[#09090b] relative">
            <!-- Editor -->
            <MarkdownEditor 
               v-if="isEditing" 
               v-model:value="rawContent" 
               mode="split"
               class="absolute inset-0 w-full h-full"
            />

            <!-- Rich View -->
            <div v-else ref="contentRef" class="h-full overflow-y-auto p-8 prose-content scrollbar-custom">
               <div v-if="parsedView" v-html="parsedView.html"></div>
            </div>
            
            <!-- Floating Note Popup (Direct Form) -->
            <Teleport to="body">
               <div 
                  v-if="activeNoteAnchor"
                  class="fixed inset-0 z-[2000] flex items-start justify-center pt-[20vh]"
               >
                  <div class="note-bubble-backdrop" @click="closeNoteBubble"></div>
                  <div class="note-bubble-floating">
                     <div class="note-bubble-header">
                        <span class="text-sm text-zinc-300 font-medium">📝 {{ activeNoteAnchor.replace(/^###\s+/, '') }}</span>
                        <button @click="closeNoteBubble" class="text-zinc-500 hover:text-white text-xl">×</button>
                     </div>
                     <textarea 
                        v-model="editingNoteContent"
                        placeholder="记录你的学习笔记..."
                        rows="4"
                        class="w-full p-3 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 text-sm resize-none focus:outline-none focus:border-blue-500"
                        autofocus
                     ></textarea>
                     <div class="flex justify-between items-center mt-3">
                        <button 
                           v-if="getNoteByAnchor(activeNoteAnchor)"
                           @click="confirmDeleteNote"
                           class="text-red-400 text-sm hover:text-red-300"
                        >🗑️ 删除</button>
                        <span v-else></span>
                        <div class="flex gap-2">
                           <button @click="closeNoteBubble" class="px-4 py-2 text-sm text-zinc-400 hover:text-white">取消</button>
                           <button 
                              @click="saveCurrentNote"
                              :disabled="!editingNoteContent.trim()"
                              class="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-500 disabled:opacity-50"
                           >保存</button>
                        </div>
                     </div>
                  </div>
               </div>
            </Teleport>
         </div>
      </div>

    </div>
  </div>
</template>

<style>
/* Global scroll lock classes - Nuclear Background Freeze */
html.is-modal-open, 
body.is-modal-open {
  overflow: hidden !important;
  height: 100vh !important;
  position: fixed !important;
  width: 100% !important;
  touch-action: none;
  -webkit-overflow-scrolling: none;
}

/* Modal Overlay should allow clicking content but block wheel to background */
.is-modal-open .fixed.inset-0 {
    pointer-events: auto;
}

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

/* Floating Note Bubble Styles */
.note-bubble-floating {
    background: #18181b;
    border: 1px solid #3f3f46;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
    padding: 12px;
    min-width: 300px;
    max-width: 400px;
    position: relative;
    z-index: 2001;
}

.note-bubble-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 8px;
    margin-bottom: 8px;
    border-bottom: 1px solid #27272a;
}

.note-bubble-backdrop {
    position: fixed;
    inset: 0;
    z-index: 1999;
}
</style>
