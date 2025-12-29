<script setup>
import { ref } from 'vue'
import QuickNotePanel from './QuickNotePanel.vue'

const isPanelOpen = ref(false)

function togglePanel() {
  isPanelOpen.value = !isPanelOpen.value
}
</script>

<template>
  <!-- Floating Action Button -->
  <button 
    @click="togglePanel"
    class="quick-note-fab"
    :class="{ 'is-open': isPanelOpen }"
    title="快速笔记"
  >
    <span class="fab-icon">{{ isPanelOpen ? '×' : '📝' }}</span>
  </button>
  
  <!-- Panel -->
  <QuickNotePanel :isOpen="isPanelOpen" @close="isPanelOpen = false" />
</template>

<style scoped>
.quick-note-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border: none;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
  cursor: pointer;
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.quick-note-fab:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 28px rgba(59, 130, 246, 0.5);
}

.quick-note-fab.is-open {
  background: #27272a;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.fab-icon {
  font-size: 24px;
  line-height: 1;
}
</style>
