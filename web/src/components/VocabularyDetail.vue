<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { marked } from 'marked'
import html2canvas from 'html2canvas-pro'
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
const exporting = ref(false)
const localItem = ref(null)
const rawContent = ref('')
const cardRef = ref(null)
const exportCardRef = ref(null)

// Computed property to extract first example sentence from content
const firstExample = computed(() => {
  if (!rawContent.value) return ''
  
  // Extract the markdown body (after frontmatter)
  const parts = rawContent.value.split(/---\r?\n/)
  if (parts.length < 3) return ''
  const body = parts.slice(2).join('---\n')
  
  // Try multiple patterns to find example sentences
  // Pattern 1: Blockquotes with > (most common in your format)
  const blockquoteMatch = body.match(/>\s*>\s*例[：:]?\s*(.+?)(?:\r?\n|$)/m) ||
                          body.match(/>\s*>\s*(.+?)(?:\r?\n|$)/m) ||
                          body.match(/>\s+(.+?)(?:\r?\n|$)/m)
  
  if (blockquoteMatch) {
    return blockquoteMatch[1].trim().replace(/\*\*/g, '')
  }
  
  // Pattern 2: Lines starting with 例: or Example:
  const exampleMatch = body.match(/(?:例|Example)[：:]\s*(.+?)(?:\r?\n|$)/im)
  if (exampleMatch) {
    return exampleMatch[1].trim().replace(/\*\*/g, '')
  }
  
  return ''
})

// Computed property to get primary definition
const primaryDefinition = computed(() => {
  if (!localItem.value?.definitions?.length) return null
  return localItem.value.definitions[0]
})


// Initialize (Load full content)
watch(() => props.item, async (newItem) => {
  if (newItem) {
    try {
      // Fetch full details including Markdown content
      const res = await fetch(`${API_BASE}/api/vocabulary/${newItem.id}`)
      if (res.ok) {
        localItem.value = await res.json()
        // Reconstruct raw content for editor
        rawContent.value = buildRawFile(localItem.value)
      }
    } catch (e) {
      console.error(e)
    }
  }
}, { immediate: true })

// Reactive ref for AI-generated card content
const aiCardContent = ref(null)

const showPreview = ref(false)
const previewImageUrl = ref('')
const selectedStyle = ref('minimalist') // Default to minimalist as requested

const cardStyles = [
  { id: 'gradient', name: '缤纷假日', icon: '🎨' },
  { id: 'minimalist', name: '极简主义', icon: '✒️' },
  { id: 'modern', name: '现代商务', icon: '💼' },
  { id: 'vintage', name: '国潮复古', icon: '🇨🇳' }
]

async function generatePreviewImage() {
    if (!exportCardRef.value) return
    
    // Brief delay to allow DOM to update style class
    await nextTick()
    
    const canvas = await html2canvas(exportCardRef.value, {
      backgroundColor: null, 
      scale: 3, 
      useCORS: true,
      width: 400,
      height: 600
    })
    
    previewImageUrl.value = canvas.toDataURL('image/png')
}

// Watch style change to regenerate preview
watch(selectedStyle, async () => {
    if (showPreview.value) {
        // Show the hidden card momentarily (it's already display:flex but offscreen)
        // actually html2canvas works on offscreen elements if display is not none.
        // We ensure it's displayed in exportImage function.
        exportCardRef.value.style.display = 'flex'
        await generatePreviewImage()
        exportCardRef.value.style.display = 'none'
    }
})

async function exportImage() {

  if (!exportCardRef.value || exporting.value || !localItem.value) return
  
  exporting.value = true
  try {
    // Step 1: Generate AI card content
    const generateRes = await fetch(`${API_BASE}/api/vocabulary/${localItem.value.id}/generate-card`, {
      method: 'POST'
    })
    
    if (!generateRes.ok) {
      throw new Error('Failed to generate card content')
    }
    
    const generateData = await generateRes.json()
    aiCardContent.value = generateData.card_data
    
    
    // Step 2: Show the export card
    exportCardRef.value.style.display = 'flex'
    
    // Step 3: Capture
    await generatePreviewImage()
    
    // Hide the export card again
    exportCardRef.value.style.display = 'none'
    
    // Show Preview
    showPreview.value = true
    
  } catch (e) {
    console.error('Export failed:', e)
    alert('导出图片失败: ' + e.message)
    // Ensure card is hidden on error
    if (exportCardRef.value) exportCardRef.value.style.display = 'none'
  } finally {
    exporting.value = false
    // aiCardContent.value = null // Keep it for a moment potentially? Or clear.
    // Better to keep it until download or close. But logic works either way as canvas is already generated.
  }
}

function downloadImage() {
    if (!previewImageUrl.value) return
    const link = document.createElement('a')
    link.download = `vocab-${localItem.value?.word || 'card'}-${selectedStyle.value}.png`
    link.href = previewImageUrl.value
    link.click()
    showPreview.value = false
}


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

// ESTIMATE SYLLABLES for Modern Card
function getSyllables(word) {
    if (!word) return ''
    if (word.length <= 3) return word
    return word.replace(/[^aeiouy]*[aeiouy]+(?:[^aeiouy]*$|[^aeiouy](?=[^aeiouy]))?/gi, "$&·").replace(/·$/, "")
}
</script>

<template>
  <div class="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-hidden" 
       @click.self="$emit('close')"
       @wheel.stop>
    <div ref="cardRef" class="bg-[#09090b] w-full max-w-6xl h-[90vh] max-h-[90vh] rounded-2xl grid grid-rows-[auto_1fr] border border-zinc-800 shadow-2xl overflow-hidden animate-fade-in relative">
      
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
               @click="exportImage" 
               :disabled="exporting"
               class="btn text-zinc-400 hover:text-white flex items-center gap-1.5 hover:bg-white/5"
               title="导出为图片"
            >
               <span class="text-xl">📸</span>
               <span class="text-sm hidden sm:inline">{{ exporting ? '导出中...' : '保存卡片' }}</span>
            </button>
            <button 
               @click="regenerate" 
               :disabled="regenerating"
               class="btn text-zinc-400 hover:text-white flex items-center gap-1.5"
               :class="regenerating ? 'opacity-50 cursor-wait' : 'hover:bg-white/5'"
               title="重新生成内容"
            >
               <span v-if="regenerating" class="animate-spin">🔄</span>
               <span v-else>🔄</span>
               <span class="text-sm hidden sm:inline">{{ regenerating ? '生成中...' : '重新生成' }}</span>
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

       <!-- Image Preview Modal -->
       <Teleport to="body">
          <div 
             v-if="showPreview"
             class="fixed inset-0 z-[2000] flex items-center justify-center p-4 bg-black/90 backdrop-blur-md"
             @click="showPreview = false"
          >
             <div class="flex flex-col items-center gap-6" @click.stop>
                <div class="flex items-center gap-3 bg-zinc-900/80 p-1.5 rounded-full border border-white/10 backdrop-blur-md">
                   <button 
                      v-for="style in cardStyles" 
                      :key="style.id"
                      @click="selectedStyle = style.id"
                      class="px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2"
                      :class="selectedStyle === style.id ? 'bg-white text-black shadow-lg' : 'text-zinc-400 hover:text-white hover:bg-white/10'"
                   >
                      <span>{{ style.icon }}</span>
                      {{ style.name }}
                   </button>
                </div>
                
                <img :src="previewImageUrl" class="rounded-[24px] shadow-2xl max-h-[65vh] w-auto border border-white/10" alt="Card Preview" />
                <div class="flex gap-4">
                   <button 
                      @click="showPreview = false"
                      class="px-6 py-2.5 rounded-full bg-zinc-800 text-zinc-300 hover:bg-zinc-700 font-medium transition-colors"
                   >
                      取消
                   </button>
                   <button 
                      @click="downloadImage"
                      class="px-6 py-2.5 rounded-full bg-blue-600 text-white hover:bg-blue-500 font-medium shadow-lg shadow-blue-500/20 transition-all flex items-center gap-2"
                   >
                      <span>📥</span> 下载图片
                   </button>
                </div>
             </div>
          </div>
       </Teleport>
     </div>
   </div>
  
  <!-- Hidden Export Card Template (Beautiful Design) -->
  <div 
    ref="exportCardRef" 
    class="export-card-base"
    :class="{
        'style-gradient': selectedStyle === 'gradient',
        'style-minimalist': selectedStyle === 'minimalist',
        'style-modern': selectedStyle === 'modern',
        'style-vintage': selectedStyle === 'vintage'
    }"
    style="display: none; position: fixed; top: -9999px; left: -9999px;"
  >
    <div class="export-card-inner">
      <!-- Decorative top area -->
      <div v-if="selectedStyle !== 'minimalist' && selectedStyle !== 'vintage'" class="export-card-header">
        <span class="export-card-icon">📚</span>
      </div>
      


      <!-- Modern Business Header (Custom DOM) -->
      <div v-if="selectedStyle === 'modern'" class="w-full h-full flex flex-col bg-[#f8fafc] relative overflow-hidden font-sans">
         <!-- Decor: Abstract geometric shape -->
         <div class="absolute top-0 right-0 w-[300px] h-[300px] bg-gradient-to-bl from-blue-100/50 to-transparent rounded-bl-full pointer-events-none"></div>
         
         <!-- 1. Header Area: Professional Dark Block -->
         <!-- Slightly reduced spacing (pb-20) to save vertical space -->
         <div class="w-full bg-[#0f172a] text-white p-7 pb-20 relative overflow-hidden shrink-0">
             <!-- Subtle grid pattern -->
             <div class="absolute inset-0 opacity-10" style="background-image: radial-gradient(#64748b 1px, transparent 1px); background-size: 20px 20px;"></div>
             
             <div class="relative z-10 flex justify-between items-start">
                 <div class="flex flex-col max-w-[70%]">
                     <div class="flex items-baseline gap-3">
                         <h1 class="text-5xl font-black tracking-tight leading-none text-white font-sans break-words">
                             {{ aiCardContent?.word || localItem.word }}
                         </h1>
                     </div>
                     <span class="text-slate-400 text-lg font-mono mt-2 tracking-wide pl-1">
                         {{ aiCardContent?.phonetic || localItem.phonetic || '' }}
                     </span>
                 </div>
                 <!-- Series No. -->
                 <div class="flex flex-col items-end shrink-0">
                     <span class="text-[10px] font-bold tracking-[0.2em] text-blue-500 uppercase">Series</span>
                     <span class="text-xl font-black text-slate-600 font-mono">#{{ Math.floor(Math.random() * 888) + 100 }}</span>
                 </div>
             </div>
         </div>
         
         <!-- 2. Main Content Card (Overlapping) -->
         <div class="flex-1 w-full flex flex-col items-center px-5 pb-4 -mt-10 relative z-20 min-h-0">
             
             <!-- Floating Info Cards Row: Functional Widgets -->
             <div class="w-full flex gap-3 mb-3 shrink-0">
                 <!-- Syllables Widget -->
                 <div class="flex-1 bg-white shadow-lg shadow-slate-900/10 rounded-lg p-2.5 flex flex-col items-center justify-center border-l-4 border-purple-500 h-[72px]">
                     <span class="text-[9px] text-slate-400 tracking-wider font-bold uppercase mb-0.5">Syllables</span>
                     <span class="text-purple-600 font-black font-mono text-lg tracking-wide leading-none mt-1">
                        {{ getSyllables(localItem.word) }}
                     </span>
                 </div>
                 <!-- Common Phrases Widget -->
                 <div class="flex-1 bg-white shadow-lg shadow-slate-900/10 rounded-lg p-2.5 flex flex-col items-center justify-center border-l-4 border-teal-500 h-[72px]">
                     <span class="text-[9px] text-slate-400 tracking-wider font-bold uppercase mb-0.5">Phrases</span>
                     <div class="flex flex-col items-center leading-tight mt-0.5 w-full overflow-hidden">
                        <span v-if="aiCardContent?.common_phrases" class="text-teal-700 font-bold text-[11px] whitespace-nowrap overflow-hidden text-ellipsis w-full text-center">
                            {{ aiCardContent.common_phrases.split('|')[0] }}
                        </span>
                        <span v-if="aiCardContent?.common_phrases?.includes('|')" class="text-teal-600 font-bold text-[11px] whitespace-nowrap overflow-hidden text-ellipsis w-full text-center">
                            {{ aiCardContent.common_phrases.split('|')[1] }}
                        </span>
                        <span v-else-if="!aiCardContent?.common_phrases" class="text-slate-300 text-[10px] italic">
                            Generate to see phrases
                        </span>
                     </div>
                 </div>
             </div>
             
             <!-- Definition Block (The "Main Widget") -->
             <div class="w-full bg-white rounded-xl shadow-xl shadow-slate-200/60 p-5 border border-slate-100 flex flex-col justify-start flex-1 min-h-0 overflow-hidden">
                 <!-- POS Badge -->
                 <div class="w-full flex justify-start mb-3 shrink-0">
                    <span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[10px] font-black tracking-widest uppercase border border-slate-200">Definition</span>
                 </div>
                 
                 <!-- Definition Text -->
                 <div class="text-2xl font-bold text-slate-800 leading-snug w-full mb-auto overflow-y-auto pr-1">
                    <div class="w-full" v-html="(aiCardContent?.definition || localItem.definitions?.[0]?.meaning || '').replace(/[；;]\s*(?=[a-z]+\.)/gi, '<br><span class=\'h-2 block\'></span>').split(/([nviadjprep]+\.)/).map(part => part.match(/^[nviadjprep]+\.$/) ? `<span class='text-blue-600 text-lg font-black uppercase mr-1.5'>${part}</span>` : part).join('')"></div>
                 </div>
                 
                 <!-- Memory Tip (If exists) - Compact Version -->
                 <div v-if="aiCardContent?.memory_tip" class="w-full mt-3 bg-amber-50 rounded-lg p-3 border border-amber-100 flex items-start gap-2 shrink-0">
                     <span class="text-amber-500 text-sm mt-0.5">💡</span>
                     <div class="text-amber-800 text-xs font-medium leading-relaxed">
                         {{ aiCardContent.memory_tip }}
                     </div>
                 </div>
             </div>
         </div>
         
         <!-- 3. Footer Area (Example) -->
         <div class="w-full bg-slate-50 border-t border-slate-200 p-5 pt-4 shrink-0 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.02)] z-10">
             <div class="w-full mx-auto">
                 <div class="flex items-start gap-3">
                     <div class="w-1 self-stretch bg-blue-600 rounded-full my-1"></div>
                     <div class="flex-1 min-w-0">
                         <p class="text-slate-800 text-[15px] font-medium italic mb-1 break-words leading-normal line-clamp-3">
                             "{{ (aiCardContent?.example || '').includes('|') ? aiCardContent.example.split('|')[0] : (aiCardContent?.example || "No example available") }}"
                         </p>
                         <p class="text-slate-500 text-[11px] font-medium truncate mt-0.5">
                             {{ (aiCardContent?.example || '').includes('|') ? aiCardContent.example.split('|')[1] : (aiCardContent?.example_translation || "") }}
                         </p>
                     </div>
                 </div>
             </div>
         </div>
      </div>

      <!-- Vintage Header (Chinese Retro) - Now uses aiCardContent -->
      <div v-if="selectedStyle === 'vintage'" class="w-full h-full flex flex-col items-center">
        <!-- 1. Top Banner (With Organic Friction Texture) -->
        <div class="w-full text-[#f3e9d2] py-5 text-center border-b-4 border-[#f3e9d2] relative flex flex-col justify-center items-center h-[150px] px-4"
             style="background: 
                linear-gradient(182deg, transparent 0%, transparent 18%, rgba(255,255,255,0.15) 19%, rgba(255,255,255,0.12) 21%, transparent 22%, transparent 100%),
                linear-gradient(176deg, transparent 0%, transparent 55%, rgba(255,255,255,0.1) 56%, rgba(255,255,255,0.08) 58%, transparent 59%, transparent 100%),
                radial-gradient(ellipse 45px 15px at 12% 28%, rgba(255,255,255,0.22) 0%, transparent 70%),
                radial-gradient(ellipse 55px 12px at 78% 65%, rgba(255,255,255,0.18) 0%, transparent 70%),
                radial-gradient(ellipse 35px 18px at 45% 42%, rgba(255,255,255,0.12) 0%, transparent 70%),
                radial-gradient(ellipse 40px 10px at 65% 85%, rgba(255,255,255,0.15) 0%, transparent 70%),
                radial-gradient(ellipse 30px 14px at 25% 75%, rgba(255,255,255,0.1) 0%, transparent 70%),
                #1e3a8a;">
             <h1 class="font-black tracking-normal font-serif leading-tight whitespace-nowrap overflow-visible w-full pb-2" 
                 :class="(aiCardContent?.word || localItem.word).length > 10 ? 'text-4xl' : 'text-5xl'"
                 style="text-shadow: 2px 2px 0px rgba(0,0,0,0.3);">
                 {{ aiCardContent?.word || localItem.word }}
             </h1>
             <div class="text-lg font-mono opacity-80 bg-[#f3e9d2]/20 px-3 py-0.5 rounded-full">
                {{ aiCardContent?.phonetic || localItem.phonetic || '' }}
             </div>
             <div class="absolute top-2 right-2 text-xs opacity-50 border border-[#f3e9d2] px-1 rounded font-mono">No. {{ Math.floor(Math.random() * 8888) + 1000 }}</div>
        </div>
        
        <!-- 2. Date Bar -->
        <div class="w-[90%] -mt-5 bg-[#f3e9d2] border-2 border-[#155e75] rounded-lg p-2 flex justify-between items-center text-[#155e75] font-bold shadow-[4px_4px_0_#155e75] z-10 relative">
             <div class="flex flex-col items-start leading-tight ml-2">
                 <span class="text-lg">{{ new Date().getFullYear() }}年{{ new Date().getMonth()+1 }}月{{ new Date().getDate() }}日</span>
             </div>
             <div class="bg-[#155e75] text-[#f3e9d2] px-3 py-1 rounded text-sm font-bold">
                宜：背单词
             </div>
        </div>
        
        <!-- 3. Memory Tip (if available) -->
        <div v-if="aiCardContent?.memory_tip" class="w-[90%] mt-6 bg-[#155e75] text-white p-3 rounded-lg text-sm font-medium">
            💡 {{ aiCardContent.memory_tip }}
        </div>
        
        <!-- 4. Definition Area -->
        <div class="w-full px-4 flex-1 flex flex-col justify-start items-center text-center pt-6 pb-4 overflow-hidden">
             <!-- Meaning Title -->
             <div class="text-[#b91c1c] text-2xl font-black mb-4 leading-tight w-full break-words" 
                  v-html="(aiCardContent?.definition || localItem.definitions?.[0]?.meaning || '').replace(/[；;]\s*(?=[a-z]+\.)/gi, '<br>')">
             </div>
        </div>
        
        <!-- 5. Footer (Example Block - With Organic Friction Texture) -->
        <div class="w-full text-[#fef2f2] px-2 py-5 relative border-t-8 border-[#f3e9d2] min-h-[140px] flex flex-col justify-center items-center"
             style="background: 
                linear-gradient(178deg, transparent 0%, transparent 25%, rgba(255,255,255,0.12) 26%, rgba(255,255,255,0.1) 28%, transparent 29%, transparent 100%),
                linear-gradient(184deg, transparent 0%, transparent 65%, rgba(255,255,255,0.08) 66%, rgba(255,255,255,0.06) 68%, transparent 69%, transparent 100%),
                radial-gradient(ellipse 50px 14px at 20% 35%, rgba(255,255,255,0.2) 0%, transparent 70%),
                radial-gradient(ellipse 40px 16px at 75% 50%, rgba(255,255,255,0.15) 0%, transparent 70%),
                radial-gradient(ellipse 45px 12px at 55% 78%, rgba(255,255,255,0.12) 0%, transparent 70%),
                radial-gradient(ellipse 35px 10px at 88% 25%, rgba(255,255,255,0.18) 0%, transparent 70%),
                radial-gradient(ellipse 38px 15px at 8% 70%, rgba(255,255,255,0.1) 0%, transparent 70%),
                #b91c1c;">
            <!-- Badge -->
            <div class="absolute -top-5 left-1/2 transform -translate-x-1/2 bg-[#f3e9d2] text-[#b91c1c] px-6 py-1 text-sm font-black rounded-full border-2 border-[#b91c1c] shadow-sm z-20">
                今日例句
            </div>
            
            <!-- Example English -->
            <div class="text-center font-serif text-lg leading-snug italic opacity-95 w-full break-words px-1 mb-1">
                {{ (aiCardContent?.example || '').includes('|') ? aiCardContent.example.split('|')[0] : (aiCardContent?.example || "No example available") }}
            </div>
            <!-- Example Chinese (separate line) -->
            <div class="text-center text-sm mt-1 opacity-90 w-full px-1">
                {{ (aiCardContent?.example || '').includes('|') ? aiCardContent.example.split('|')[1] : (aiCardContent?.example_translation || "") }}
            </div>
        </div>
      </div>

      <div v-if="selectedStyle === 'minimalist'" class="w-full flex justify-between items-start mb-8 text-black/40">
        <span class="text-xs tracking-[0.2em] font-medium">VOCABULARY</span>
        <span class="text-xs font-serif italic">No. {{ Math.floor(Math.random() * 1000) }}</span>
      </div>
      
      <!-- Main word -->
      <h1 class="export-card-word">{{ localItem?.word || '' }}</h1>
      
      <!-- Phonetic -->
      <p class="export-card-phonetic">{{ localItem?.phonetic || '' }}</p>
      
      <!-- Divider -->
      <div class="export-card-divider"></div>
      
      <!-- Memory Tip (AI Generated) -->
      <div v-if="aiCardContent?.memory_tip" class="export-card-tip">
        <span class="tip-icon">💡</span>
        <span class="tip-text">{{ aiCardContent.memory_tip }}</span>
      </div>
      
      <!-- Definition (AI Generated) -->
      <div v-if="aiCardContent?.definition" class="export-card-definition">
        <span class="def-meaning">{{ aiCardContent.definition }}</span>
      </div>
      
      <!-- Example (AI Generated, bilingual) -->
      <p v-if="aiCardContent?.example" class="export-card-example">
        {{ aiCardContent.example.split('|')[0] }}<br>
        <span class="example-translation">{{ aiCardContent.example.split('|')[1] || '' }}</span>
      </p>
      
      <!-- Branding -->
      <div class="export-card-footer">
        <span>MEM Study</span>
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

/* Export Card Base Structure */
.export-card-base {
    width: 400px;
    height: 600px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 32px;
    box-sizing: border-box;
    overflow: hidden;
}

/* 1. Gradient Style (Original) */
.style-gradient {
    background: linear-gradient(135deg, #FF6B6B 0%, #FFA07A 50%, #FFD93D 100%);
    border-radius: 24px;
    font-family: 'Georgia', 'Times New Roman', serif;
    color: #1a1a2e;
}

.style-gradient .export-card-word {
    font-size: 48px;
    font-weight: 900;
    color: #1a1a2e;
    margin: 0;
    line-height: 1.2;
    text-shadow: 2px 2px 0px rgba(255,255,255,0.2);
}

.style-gradient .export-card-phonetic {
    font-family: 'Courier New', monospace;
    font-size: 18px;
    color: rgba(26, 26, 46, 0.6);
    margin: 8px 0 24px 0;
}

.style-gradient .export-card-divider {
    width: 60%;
    height: 2px;
    background: rgba(26, 26, 46, 0.1);
    margin-bottom: 24px;
    border-radius: 2px;
}

.style-gradient .export-card-tip {
    background: rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(8px);
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    border: 1px solid rgba(255, 255, 255, 0.4);
}

.style-gradient .tip-icon { font-size: 20px; }
.style-gradient .tip-text { font-size: 14px; font-weight: 500; color: #2d2d42; text-align: left; }

.style-gradient .export-card-definition { margin-bottom: 24px; text-align: center; }
.style-gradient .def-pos { 
    display: block; 
    font-size: 18px; 
    font-weight: bold; 
    margin-bottom: 4px; 
    opacity: 0.8; 
}
.style-gradient .def-meaning { font-size: 22px; font-weight: bold; }

.style-gradient .export-card-example {
    font-style: italic;
    color: #3d3d5c;
    background: rgba(255,255,255,0.15);
    padding: 16px;
    border-radius: 8px;
    width: 100%;
    text-align: left;
}
.style-gradient .example-translation {
    display: block; 
    margin-top: 8px; 
    font-size: 0.9em; 
    opacity: 0.8; 
    font-style: normal;
}

.style-gradient .export-card-footer {
    margin-top: auto;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 2px;
    opacity: 0.4;
    font-weight: bold;
}

/* 2. Minimalist Style (Elegant Editorial/Magazine) */
.style-minimalist {
    background: #fbfbfb; /* Ivory/Paper white */
    border-radius: 12px;
    font-family: 'Georgia', 'Playfair Display', serif;
    color: #1a1a1a;
    position: relative;
    border: 1px solid #eee;
    padding: 48px 32px;
}

/* Subtle corner accents removed for cleaner look */
.style-minimalist::before {
    content: none;
}
.style-minimalist::after {
    content: none;
}

.style-minimalist .export-card-word {
    font-size: 64px;
    font-weight: 800; /* Bold serif */
    letter-spacing: -3px;
    color: #000;
    margin: 0 0 -4px 0;
}

.style-minimalist .export-card-phonetic {
    font-family: 'Times New Roman', serif;
    font-style: italic;
    font-size: 18px;
    color: #3b82f6; /* Klein Blue accent */
    margin-bottom: 40px;
}

.style-minimalist .export-card-divider {
    display: none; /* Removed separator line */
}

.style-minimalist .export-card-tip {
    background: rgba(0,0,0,0.03);
    border-left: 2px solid #3b82f6;
    padding: 12px 16px;
    margin-bottom: 32px;
    width: 100%;
    border-radius: 0 8px 8px 0;
}
.style-minimalist .tip-icon { display: none; }
.style-minimalist .tip-text { 
    font-size: 12px; 
    color: #666; 
    line-height: 1.6;
    font-family: 'Inter', sans-serif;
}

.style-minimalist .export-card-definition { margin-bottom: 32px; text-align: left; width: 100%; }
.style-minimalist .def-pos { 
    font-size: 10px; 
    text-transform: uppercase; 
    letter-spacing: 2px; 
    background: #000;
    color: #fff;
    padding: 2px 6px;
    margin-bottom: 8px;
    display: table; /* Auto width */
}
.style-minimalist .def-meaning { 
    font-size: 22px; 
    font-weight: 700; 
    border-bottom: 1.5px solid #000;
}

.style-minimalist .export-card-example {
    width: 100%;
    text-align: left;
    font-size: 16px;
    line-height: 1.7;
    color: #333;
    font-style: italic;
    border-top: 1px solid #f0f0f0;
    padding-top: 24px;
}
.style-minimalist .example-translation {
    display: block;
    margin-top: 12px;
    font-size: 14px;
    color: #888;
    font-style: normal;
    font-family: 'Microsoft YaHei', sans-serif;
}

.style-minimalist .export-card-footer {
    margin-top: auto;
    width: 100%;
    display: flex;
    justify-content: center;
    font-size: 10px;
    color: #ccc;
    text-transform: uppercase;
    letter-spacing: 3px;
    font-family: sans-serif;
}

/* 3. Modern Style (Professional Business) - Custom DOM Controlled */
.style-modern {
    background: #f8fafc;
    padding: 0; /* Full bleed for custom DOM */
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    color: #0f172a;
    display: flex;
    flex-direction: column;
}

/* Hide default elements since we constructed custom ones in template */
.style-modern .export-card-inner {
    display: block; width: 100%; height: 100%;
}
.style-modern .export-card-header,
.style-modern .export-card-word,
.style-modern .export-card-phonetic,
.style-modern .export-card-divider,
.style-modern .export-card-tip,
.style-modern .export-card-definition,
.style-modern .export-card-example,
.style-modern .export-card-footer {
    display: none;
}

/* 4. Vintage Style (Chinese Retro / Guochao) */
.style-vintage {
    background-color: #f8f1e5; /* Old paper beige */
    padding: 0; /* Reset padding for full-width blocks */
    display: flex;
    flex-direction: column;
    border: 8px solid #1e3a8a; /* thick navy border */
    position: relative;
    box-shadow: 0 0 0 4px #f8f1e5 inset; /* inner beige spacing */
}

/* Hide default elements since we constructed custom ones in template */
.style-vintage .export-card-inner {
    display: block; width: 100%; height: 100%;
}
.style-vintage .export-card-header,
.style-vintage .export-card-word,
.style-vintage .export-card-phonetic,
.style-vintage .export-card-divider,
.style-vintage .export-card-tip,
.style-vintage .export-card-definition,
.style-vintage .export-card-example,
.style-vintage .export-card-footer {
    display: none; /* We use the custom HTML structure above */
}

/* Noise/Grain Texture for Vintage Effect */
.style-vintage > div > div:first-child::after {
    /* Blue header noise overlay */
    content: '';
    position: absolute;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
    opacity: 0.08;
    mix-blend-mode: overlay;
    pointer-events: none;
}

/* Red footer noise overlay */
.style-vintage > div > div:last-child::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
    opacity: 0.1;
    mix-blend-mode: soft-light;
    pointer-events: none;
    z-index: 1;
}
</style>
