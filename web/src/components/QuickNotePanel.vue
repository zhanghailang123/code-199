<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { API_BASE } from '../config/api.js'

const props = defineProps({
  isOpen: { type: Boolean, default: false }
})

const emit = defineEmits(['close'])

// State
const memos = ref([])
const newContent = ref('')
const newTags = ref([])
const tagInput = ref('')
const loading = ref(false)
const saving = ref(false)
const editingId = ref(null)
const editingContent = ref('')

// Panel resize state
const panelHeight = ref(320)
const isResizing = ref(false)
const startY = ref(0)
const startHeight = ref(0)

// Panel drag state
const panelPosition = ref({ x: 0, y: 0 })
const isDragging = ref(false)
const dragStartPos = ref({ x: 0, y: 0 })
const dragStartOffset = ref({ x: 0, y: 0 })

function startResize(e) {
  isResizing.value = true
  startY.value = e.clientY
  startHeight.value = panelHeight.value
  document.addEventListener('mousemove', doResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'ns-resize'
  document.body.style.userSelect = 'none'
}

function doResize(e) {
  if (!isResizing.value) return
  const delta = startY.value - e.clientY
  const newHeight = Math.min(Math.max(startHeight.value + delta, 200), window.innerHeight * 0.8)
  panelHeight.value = newHeight
}

function stopResize() {
  isResizing.value = false
  document.removeEventListener('mousemove', doResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// Drag functions
function startDrag(e) {
  isDragging.value = true
  dragStartPos.value = { x: e.clientX, y: e.clientY }
  dragStartOffset.value = { ...panelPosition.value }
  document.addEventListener('mousemove', doDrag)
  document.addEventListener('mouseup', stopDrag)
  document.body.style.cursor = 'move'
  document.body.style.userSelect = 'none'
}

function doDrag(e) {
  if (!isDragging.value) return
  const deltaX = e.clientX - dragStartPos.value.x
  const deltaY = e.clientY - dragStartPos.value.y
  panelPosition.value = {
    x: dragStartOffset.value.x + deltaX,
    y: dragStartOffset.value.y + deltaY
  }
}

function stopDrag() {
  isDragging.value = false
  document.removeEventListener('mousemove', doDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

onUnmounted(() => {
  document.removeEventListener('mousemove', doResize)
  document.removeEventListener('mouseup', stopResize)
  document.removeEventListener('mousemove', doDrag)
  document.removeEventListener('mouseup', stopDrag)
})

// Fetch memos
async function fetchMemos() {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/api/memos`)
    if (res.ok) {
      const data = await res.json()
      memos.value = data.memos || []
    }
  } catch (e) {
    console.error('Failed to fetch memos:', e)
  } finally {
    loading.value = false
  }
}

// Create new memo
async function createMemo() {
  if (!newContent.value.trim()) return
  
  saving.value = true
  try {
    const res = await fetch(`${API_BASE}/api/memos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: newContent.value.trim(),
        tags: newTags.value
      })
    })
    if (res.ok) {
      newContent.value = ''
      newTags.value = []
      await fetchMemos()
    }
  } catch (e) {
    console.error('Failed to create memo:', e)
  } finally {
    saving.value = false
  }
}

// Update memo
async function updateMemo(id) {
  if (!editingContent.value.trim()) return
  
  try {
    const res = await fetch(`${API_BASE}/api/memos/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: editingContent.value.trim() })
    })
    if (res.ok) {
      editingId.value = null
      editingContent.value = ''
      await fetchMemos()
    }
  } catch (e) {
    console.error('Failed to update memo:', e)
  }
}

// Delete memo
async function deleteMemo(id) {
  if (!confirm('确定删除这条备忘吗？')) return
  
  try {
    const res = await fetch(`${API_BASE}/api/memos/${id}`, { method: 'DELETE' })
    if (res.ok) {
      await fetchMemos()
    }
  } catch (e) {
    console.error('Failed to delete memo:', e)
  }
}

// Add tag
function addTag() {
  const tag = tagInput.value.trim()
  if (tag && !newTags.value.includes(tag)) {
    newTags.value.push(tag)
  }
  tagInput.value = ''
}

// Remove tag
function removeTag(idx) {
  newTags.value.splice(idx, 1)
}

// Start editing
function startEdit(memo) {
  editingId.value = memo.id
  editingContent.value = memo.content
}

// Cancel editing
function cancelEdit() {
  editingId.value = null
  editingContent.value = ''
}

// Group memos by date
const groupedMemos = computed(() => {
  const groups = {}
  memos.value.forEach(memo => {
    const date = memo.created?.split('T')[0] || 'Unknown'
    if (!groups[date]) groups[date] = []
    groups[date].push(memo)
  })
  return groups
})

// Format date for display
function formatDate(dateStr) {
  const today = new Date().toISOString().split('T')[0]
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]
  
  if (dateStr === today) return '今天'
  if (dateStr === yesterday) return '昨天'
  return dateStr
}

// Format time
function formatTime(isoStr) {
  if (!isoStr) return ''
  const date = new Date(isoStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// Load on open
watch(() => props.isOpen, (open) => {
  if (open) fetchMemos()
})

onMounted(() => {
  if (props.isOpen) fetchMemos()
})
</script>

<template>
  <Transition name="slide">
    <div v-if="isOpen" class="quick-note-panel">
      <div 
        class="panel-content" 
        :style="{ 
          height: panelHeight + 'px',
          transform: `translate(${panelPosition.x}px, ${panelPosition.y}px)`
        }"
      >
        <!-- Resize Handle (top edge) -->
        <div class="resize-handle" @mousedown.prevent="startResize">
          <div class="resize-bar"></div>
        </div>
        
        <!-- Header (draggable) -->
        <div class="panel-header" @mousedown.prevent="startDrag">
          <h2>📝 快速笔记</h2>
          <button @click.stop="emit('close')" class="close-btn">×</button>
        </div>
        
        <!-- Input Area -->
        <div class="input-area">
          <textarea 
            v-model="newContent"
            placeholder="记录你的想法..."
            rows="20"
            class="memo-input"
            @keydown.ctrl.enter="createMemo"
          ></textarea>
          
          <!-- Tags -->
          <div class="tags-row">
            <div class="tags-list">
              <span v-for="(tag, idx) in newTags" :key="tag" class="tag">
                {{ tag }}
                <button @click="removeTag(idx)" class="tag-remove">×</button>
              </span>
              <input 
                v-model="tagInput"
                @keydown.enter.prevent="addTag"
                placeholder="+ 标签"
                class="tag-input"
              >
            </div>
            <button 
              @click="createMemo" 
              :disabled="!newContent.trim() || saving"
              class="save-btn"
            >
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
        
        <!-- Memo List -->
        <div class="memo-list">
          <div v-if="loading" class="loading">加载中...</div>
          <div v-else-if="memos.length === 0" class="empty">还没有备忘录</div>
          <template v-else>
            <div v-for="(groupMemos, date) in groupedMemos" :key="date" class="date-group">
              <div class="date-header">{{ formatDate(date) }}</div>
              <div 
                v-for="memo in groupMemos" 
                :key="memo.id" 
                class="memo-card"
              >
                <!-- Edit Mode -->
                <div v-if="editingId === memo.id" class="edit-mode">
                  <textarea v-model="editingContent" rows="3" class="edit-input"></textarea>
                  <div class="edit-actions">
                    <button @click="cancelEdit" class="btn-cancel">取消</button>
                    <button @click="updateMemo(memo.id)" class="btn-save">保存</button>
                  </div>
                </div>
                
                <!-- View Mode -->
                <template v-else>
                  <div class="memo-content">{{ memo.content }}</div>
                  <div class="memo-footer">
                    <div class="memo-meta">
                      <span v-for="tag in memo.tags" :key="tag" class="memo-tag">#{{ tag }}</span>
                      <span class="memo-time">{{ formatTime(memo.created) }}</span>
                    </div>
                    <div class="memo-actions">
                      <button @click="startEdit(memo)" class="action-btn" title="编辑">✏️</button>
                      <button @click="deleteMemo(memo.id)" class="action-btn" title="删除">🗑️</button>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.quick-note-panel {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  pointer-events: none;
}

.panel-content {
  width: 100%;
  max-width: 900px;
  min-height: 200px;
  margin: 0 auto;
  background: #0a0a0b;
  border-top: 1px solid #3f3f46;
  border-left: 1px solid #3f3f46;
  border-right: 1px solid #3f3f46;
  border-radius: 16px 16px 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  pointer-events: auto;
  box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.4);
}

.resize-handle {
  flex-shrink: 0;
  height: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: ns-resize;
  background: transparent;
}

.resize-handle:hover .resize-bar {
  background: #52525b;
}

.resize-bar {
  width: 40px;
  height: 4px;
  background: #3f3f46;
  border-radius: 2px;
  transition: background 0.2s;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  border-bottom: 1px solid #27272a;
  flex-shrink: 0;
  cursor: move;
  user-select: none;
}

.panel-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: #f4f4f5;
  margin: 0;
}

.close-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #71717a;
  font-size: 18px;
  cursor: pointer;
  border-radius: 6px;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #f4f4f5;
}

.input-area {
  padding: 12px 24px;
  border-bottom: 1px solid #27272a;
  flex-shrink: 0;
}

.memo-input {
  width: 100%;
  padding: 10px 12px;
  background: #18181b;
  border: 1px solid #3f3f46;
  border-radius: 8px;
  color: #f4f4f5;
  font-size: 14px;
  min-height: 100px;
  max-height: 200px;
  resize: vertical;
}

.memo-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.tags-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  gap: 12px;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  flex: 1;
  align-items: center;
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border-radius: 4px;
  font-size: 12px;
}

.tag-remove {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 0;
  font-size: 14px;
  opacity: 0.7;
}

.tag-remove:hover {
  opacity: 1;
}

.tag-input {
  width: 60px;
  padding: 4px 8px;
  background: transparent;
  border: 1px dashed #3f3f46;
  border-radius: 4px;
  color: #71717a;
  font-size: 12px;
}

.tag-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.save-btn {
  padding: 8px 20px;
  background: #3b82f6;
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}

.save-btn:hover:not(:disabled) {
  background: #2563eb;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.memo-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: auto;
  padding: 12px 24px;
  display: flex;
  gap: 12px;
  min-height: 120px;
}

.loading, .empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #71717a;
  width: 100%;
  min-height: 100px;
}

.date-group {
  display: flex;
  flex-direction: column;
  min-width: 280px;
  flex-shrink: 0;
}

.date-header {
  font-size: 11px;
  font-weight: 600;
  color: #71717a;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.memo-card {
  background: #18181b;
  border: 1px solid #27272a;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
}

.memo-content {
  color: #e4e4e7;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 60px;
  overflow: hidden;
}

.memo-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #27272a;
}

.memo-meta {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.memo-tag {
  color: #60a5fa;
  font-size: 11px;
}

.memo-time {
  color: #52525b;
  font-size: 10px;
}

.memo-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}

.memo-card:hover .memo-actions {
  opacity: 1;
}

.action-btn {
  padding: 3px 5px;
  background: transparent;
  border: none;
  cursor: pointer;
  border-radius: 4px;
  font-size: 11px;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.edit-mode {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.edit-input {
  width: 100%;
  padding: 8px;
  background: #09090b;
  border: 1px solid #3f3f46;
  border-radius: 6px;
  color: #f4f4f5;
  font-size: 13px;
  resize: none;
}

.edit-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}

.btn-cancel, .btn-save {
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.btn-cancel {
  background: transparent;
  border: 1px solid #3f3f46;
  color: #a1a1aa;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.05);
}

.btn-save {
  background: #3b82f6;
  border: none;
  color: white;
}

.btn-save:hover {
  background: #2563eb;
}

/* Slide transition - from bottom */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
}

.slide-enter-from .panel-content,
.slide-leave-to .panel-content {
  transform: translateY(100%);
}
</style>
