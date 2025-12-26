<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  anchor: { type: String, required: true },
  note: { type: Object, default: null },
  position: { type: Object, default: () => ({ top: 0, left: 0 }) }
})

const emit = defineEmits(['save', 'delete', 'close'])

const isHovering = ref(false)
const isEditing = ref(false)
const editContent = ref('')
const bubbleRef = ref(null)

// Initialize edit content when entering edit mode
function startEdit() {
  editContent.value = props.note?.content || ''
  isEditing.value = true
}

function cancelEdit() {
  isEditing.value = false
  editContent.value = ''
}

function saveNote() {
  if (editContent.value.trim()) {
    emit('save', {
      anchor: props.anchor,
      content: editContent.value.trim()
    })
  }
  isEditing.value = false
}

function deleteNote() {
  if (confirm('确定删除这条笔记吗？')) {
    emit('delete', props.anchor)
  }
}

// Handle click outside to close
function handleClickOutside(e) {
  if (bubbleRef.value && !bubbleRef.value.contains(e.target)) {
    if (isEditing.value) {
      cancelEdit()
    }
    isHovering.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="note-bubble-wrapper" ref="bubbleRef">
    <!-- Trigger Icon -->
    <button 
      @mouseenter="isHovering = true"
      @click.stop="isHovering = true"
      class="note-icon"
      :class="{ 'has-note': note, 'no-note': !note }"
      :title="note ? '查看笔记' : '添加笔记'"
    >
      {{ note ? '📝' : '➕' }}
    </button>

    <!-- Bubble Popover -->
    <Transition name="bubble">
      <div 
        v-if="isHovering"
        class="note-bubble"
        @click.stop
      >
        <!-- View Mode -->
        <div v-if="!isEditing && note" class="note-content">
          <div class="note-header">
            <span class="note-label">📝 我的笔记</span>
            <div class="note-actions">
              <button @click="startEdit" class="action-btn edit" title="编辑">✏️</button>
              <button @click="deleteNote" class="action-btn delete" title="删除">🗑️</button>
            </div>
          </div>
          <p class="note-text">{{ note.content }}</p>
          <div class="note-meta">
            {{ note.updated || note.created }}
          </div>
        </div>

        <!-- Empty State / Add Mode -->
        <div v-else-if="!isEditing && !note" class="note-empty">
          <p>还没有笔记</p>
          <button @click="startEdit" class="add-btn">
            ➕ 添加笔记
          </button>
        </div>

        <!-- Edit Mode -->
        <div v-if="isEditing" class="note-edit">
          <div class="note-header">
            <span class="note-label">{{ note ? '编辑笔记' : '添加笔记' }}</span>
          </div>
          <textarea 
            v-model="editContent"
            placeholder="记录你的想法..."
            rows="4"
            class="note-textarea"
            autofocus
          ></textarea>
          <div class="edit-actions">
            <button @click="cancelEdit" class="cancel-btn">取消</button>
            <button @click="saveNote" class="save-btn" :disabled="!editContent.trim()">保存</button>
          </div>
        </div>

        <!-- Close Button -->
        <button @click="isHovering = false" class="close-btn">×</button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.note-bubble-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
  margin-left: 8px;
}

.note-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  font-size: 14px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
}

.note-icon.has-note {
  background: rgba(59, 130, 246, 0.2);
}

.note-icon.no-note {
  background: rgba(113, 113, 122, 0.2);
  opacity: 0.5;
}

.note-icon:hover {
  transform: scale(1.1);
  opacity: 1;
}

.note-bubble {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  min-width: 280px;
  max-width: 360px;
  background: #18181b;
  border: 1px solid #3f3f46;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  z-index: 1000;
  padding: 16px;
}

.note-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #27272a;
}

.note-label {
  font-size: 12px;
  font-weight: 600;
  color: #a1a1aa;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.note-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  padding: 4px 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.action-btn.delete:hover {
  background: rgba(239, 68, 68, 0.2);
}

.note-text {
  color: #e4e4e7;
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
}

.note-meta {
  margin-top: 12px;
  font-size: 11px;
  color: #71717a;
}

.note-empty {
  text-align: center;
  padding: 8px 0;
}

.note-empty p {
  color: #71717a;
  margin-bottom: 12px;
}

.add-btn {
  padding: 8px 16px;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #60a5fa;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.add-btn:hover {
  background: rgba(59, 130, 246, 0.3);
}

.note-textarea {
  width: 100%;
  padding: 12px;
  background: #09090b;
  border: 1px solid #3f3f46;
  border-radius: 8px;
  color: #e4e4e7;
  font-size: 14px;
  resize: vertical;
  min-height: 80px;
}

.note-textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

.cancel-btn, .save-btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background: transparent;
  border: 1px solid #3f3f46;
  color: #a1a1aa;
}

.cancel-btn:hover {
  background: rgba(255, 255, 255, 0.05);
}

.save-btn {
  background: #3b82f6;
  border: none;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #2563eb;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.close-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #71717a;
  cursor: pointer;
  font-size: 16px;
  border-radius: 4px;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #e4e4e7;
}

/* Transition */
.bubble-enter-active,
.bubble-leave-active {
  transition: all 0.2s ease;
}

.bubble-enter-from,
.bubble-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
