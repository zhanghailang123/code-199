<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Editor, Viewer } from '@bytemd/vue-next'
import gfm from '@bytemd/plugin-gfm'
import highlight from '@bytemd/plugin-highlight'
import math from '@bytemd/plugin-math'
import gemoji from '@bytemd/plugin-gemoji'
import mermaid from '@bytemd/plugin-mermaid'
import frontmatter from '@bytemd/plugin-frontmatter'
import breaks from '@bytemd/plugin-breaks'
import 'bytemd/dist/index.css'
import 'highlight.js/styles/github-dark.css' // Or another hljs theme
import 'katex/dist/katex.css'

// Custom plugin to render frontmatter as a table
const frontmatterRenderer = () => ({
  viewerEffect({ file }) {
    if (file && file.data && file.data.frontmatter) {
      const fm = file.data.frontmatter;
      const preview = document.querySelector('.bytemd-preview');
      if (preview) {
        let existing = preview.querySelector('.fm-container');
        if (!existing) {
          existing = document.createElement('div');
          existing.className = 'fm-container mb-6 p-4 rounded-lg bg-zinc-900/50 border border-white/10 text-xs font-mono';
          preview.prepend(existing);
        }
        let html = '<table class="w-full text-zinc-400 table-fixed"><tbody>';
        for (const [key, value] of Object.entries(fm)) {
          html += `<tr><td class="font-bold pr-4 py-1 text-zinc-500 w-24 align-top">${key}:</td><td class="py-1 break-words text-zinc-300">${typeof value === 'object' ? JSON.stringify(value) : value}</td></tr>`;
        }
        html += '</tbody></table>';
        existing.innerHTML = html;
      }
    }
  }
});

const plugins = [
  gfm(),
  breaks(),
  frontmatter(),
  highlight(),
  math(),
  gemoji(),
  mermaid(),
  frontmatterRenderer(),
]

const props = defineProps({
  value: {
    type: String,
    default: ''
  },
  mode: {
    type: String,
    default: 'split', // 'split' | 'tab' | 'auto'
    validator: v => ['split', 'tab', 'auto'].includes(v)
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:value', 'change'])

const handleChange = (v) => {
  emit('update:value', v)
  emit('change', v)
}

// Custom localized text
const locale = {
//   toc: '目录',
//   h1: '一级标题',
  // ... can add more chinese localization
}

const editorWrapper = ref(null)
let resizeObserver = null

// Robust Layout Refresher using ResizeObserver
function updateHeights() {
  if (!editorWrapper.value) return
  
  const wrapper = editorWrapper.value
  const toolbar = wrapper.querySelector('.bytemd-toolbar')
  const status = wrapper.querySelector('.bytemd-status')
  const body = wrapper.querySelector('.bytemd-body')
  const codeMirror = wrapper.querySelector('.CodeMirror')
  const scroller = wrapper.querySelector('.CodeMirror-scroll')
  const preview = wrapper.querySelector('.bytemd-preview')
  
  if (!body) return

  const totalHeight = wrapper.offsetHeight
  const toolbarHeight = toolbar ? toolbar.offsetHeight : 0
  const statusHeight = status ? status.offsetHeight : 0
  const availableHeight = totalHeight - toolbarHeight - statusHeight

  if (availableHeight > 0) {
    body.style.setProperty('height', `${availableHeight}px`, 'important')
    if (codeMirror) codeMirror.style.setProperty('height', `${availableHeight}px`, 'important')
    if (scroller) scroller.style.setProperty('height', `${availableHeight}px`, 'important')
    if (preview) preview.style.setProperty('height', `${availableHeight}px`, 'important')
    
    // Refresh CodeMirror instance
    const cmElement = wrapper.querySelector('.CodeMirror')
    if (cmElement && cmElement.CodeMirror) {
      cmElement.CodeMirror.refresh()
    }
  }
}

onMounted(() => {
  nextTick(() => {
    // Initial refresh and layout calculation
    updateHeights()
    window.dispatchEvent(new Event('resize'))
    
    // Set up observer to handle all future layout changes (animations, resizes)
    if (window.ResizeObserver && editorWrapper.value) {
      resizeObserver = new ResizeObserver(() => {
        updateHeights()
      })
      resizeObserver.observe(editorWrapper.value)
    }
    
    // Fallback pulse for the first 2 seconds to handle library initialization
    const pulse = setInterval(updateHeights, 200)
    setTimeout(() => clearInterval(pulse), 2000)
  })
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})

watch(() => props.value, () => {
  nextTick(updateHeights)
})
</script>

<template>
  <div ref="editorWrapper" class="bytemd-wrapper" :class="{ 'is-readonly': readonly }">
    <Viewer 
      v-if="readonly"
      :value="value" 
      :plugins="plugins"
    />
    <Editor 
      v-else
      :value="value" 
      :plugins="plugins" 
      :locale="locale"
      :mode="mode"
      @change="handleChange" 
    />
  </div>
</template>

<style>
/* Override ByteMD styles for Dark Theme */
/* Next-Gen ByteMD Theme Overrides */
.bytemd-wrapper {
  position: relative;
  height: 100% !important;
  width: 100% !important;
  max-height: 100vh !important;
}

/* Main container - Filled by parent grid/flex */
.bytemd {
  position: absolute !important;
  inset: 0 !important;
  height: 100% !important;
  width: 100% !important;
  border: none !important;
  border-radius: 0 !important;
  background: transparent !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
  box-sizing: border-box !important;
  pointer-events: auto !important; /* Ensure capture */
  min-height: 400px; /* Safety minimum */
}

/* --- Toolbar --- */
.bytemd-toolbar {
  flex: 0 0 auto !important;
  background-color: #09090b !important; /* Zinc 950 */
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
  padding: 0.5rem 1rem !important;
  width: 100%;
  position: relative;
  z-index: 20;
}

.bytemd-toolbar-icon {
  color: #71717a !important; /* Zinc 500 */
  border-radius: 6px !important;
  padding: 6px !important;
  transition: all 0.2s ease;
  width: 32px !important;
  height: 32px !important;
}

.bytemd-toolbar-icon:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: #e4e4e7 !important; /* Zinc 200 */
  transform: translateY(-1px);
}

.bytemd-toolbar-icon.bytemd-toolbar-icon-active {
  background-color: rgba(59, 130, 246, 0.2) !important;
  color: #60a5fa !important;
}

/* --- Body (Container) --- */
.bytemd-body {
  flex: 1 1 0% !important;
  min-height: 0 !important;
  background-color: #09090b !important;
  position: relative !important; /* Context for absolute children */
  display: flex !important;
  flex-direction: row !important;
  align-items: stretch !important;
  overflow: hidden !important;
}

/* --- Editor (Left Pane) --- */
.bytemd-editor {
  flex: 1 1 50% !important; 
  min-width: 0 !important;
  min-height: 0 !important;
  position: relative !important;
  height: 100% !important;
  overflow: hidden !important;
  pointer-events: auto !important;
}

/* Fallback & CM Styling */
.bytemd-editor textarea {
  background-color: #ffffff !important;
  color: #334155 !important; /* Slate 700 */
  font-family: 'JetBrains Mono', monospace !important;
}

.CodeMirror {
  background-color: #ffffff !important;
  color: #0f172a !important; /* Slate 900 - High Contrast */
  font-family: 'JetBrains Mono', Consolas, Monaco, 'Andale Mono', monospace !important;
  font-size: 15px !important;
  line-height: 1.7 !important;
  height: 100% !important; /* Managed by JS Pulse/Observer */
  width: 100% !important;
}

/* RECURSIVE HEIGHT FORCE - Base for Observer */
.bytemd-editor, .bytemd-editor > div, .bytemd-editor .CodeMirror {
  height: 100% !important;
  min-height: 0 !important;
}

/* CRITICAL: Force CodeMirror internal scrollbar visibility */
.CodeMirror-vscrollbar {
  display: block !important;
  width: 12px !important;
  z-index: 100 !important;
  opacity: 1 !important;
  visibility: visible !important;
}

.CodeMirror-scroll {
  height: 100% !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  margin-bottom: 0 !important;
  margin-right: 0 !important;
  padding-bottom: 0 !important;
}

.CodeMirror-sizer {
  min-height: 100% !important;
  padding-bottom: 100px !important; /* Buffer for scrolling */
  box-sizing: border-box !important;
}

/* --- Preview (Right Pane) --- */
.bytemd-preview {
  flex: 1 1 50% !important;
  min-width: 0 !important;
  min-height: 0 !important;
  position: relative !important;
  height: 100% !important;
  overflow-y: auto !important;
  padding-bottom: 100px !important;
  background-color: #0c0c0e !important;
}

.bytemd-split .bytemd-preview {
  border-left: 1px solid rgba(255, 255, 255, 0.05) !important;
  background-color: #0c0c0e !important; 
  padding: 1.5rem !important; 
  padding-bottom: 8rem !important; 
  pointer-events: auto !important;
}

.markdown-body {
  font-family: 'Inter', sans-serif !important;
  color: #e4e4e7 !important;
  line-height: 1.8 !important;
  font-size: 16px !important;
  max-width: none !important; /* Allow full width */
}

/* Typography matching VocabularyDetail */
.markdown-body h1 {
  border-bottom: 1px solid rgba(255,255,255,0.1) !important;
  padding-bottom: 0.5rem !important;
  line-height: 2.0 !important; /* Looser leading */
  font-size: 17px !important; /* Larger text */
}

/* Typography Overrides for Markdown Body */
.markdown-body h1, .markdown-body h2, .markdown-body h3 {
  color: #fff !important;
  border-bottom-color: rgba(255, 255, 255, 0.1) !important;
  margin-top: 2.5rem !important; /* More space before headers */
  margin-bottom: 1.5rem !important;
  font-weight: 700 !important;
}

.markdown-body h1 { font-size: 2rem !important; }
.markdown-body h2 { font-size: 1.5rem !important; color: #60a5fa !important; /* Blue highlight for sections */ }
.markdown-body h3 { font-size: 1.25rem !important; color: #a5b4fc !important; }

.markdown-body p {
  margin-bottom: 1.5rem !important; /* Breathing room between paragraphs */
}

.markdown-body ul, .markdown-body ol {
  padding-left: 1.5rem !important;
  margin-bottom: 1.5rem !important;
}

.markdown-body li {
  margin-bottom: 0.75rem !important; /* Space between list items */
}

.markdown-body blockquote {
  border-left: 4px solid #3b82f6 !important;
  background: rgba(59, 130, 246, 0.05) !important;
  color: #94a3b8 !important;
  padding: 1rem 1.5rem !important;
  border-radius: 0 8px 8px 0;
}

.markdown-body pre {
  background-color: #1f1f23 !important;
  border: 1px solid rgba(255, 255, 255, 0.05) !important;
  border-radius: 8px !important;
  padding: 1.25rem !important;
  margin: 2rem 0 !important;
}

.markdown-body code {
  background-color: rgba(255,255,255,0.1) !important;
  color: #a5b4fc !important; /* Indigo 300 */
  border-radius: 4px;
  padding: 0.2em 0.4em !important;
}

/* --- Status Bar --- */
.bytemd-status {
  grid-row: 3;
  border-top: 1px solid rgba(255, 255, 255, 0.05) !important;
  background-color: #09090b !important;
  color: #52525b !important;
  font-size: 12px !important;
  padding: 4px 16px !important;
  width: 100%;
}

/* --- Scrollbars - Make them VISIBLE --- */
/* --- Scrollbars - Make them VISIBLE --- */
/* Chrome/Webkit/Edgium */
.bytemd-editor ::-webkit-scrollbar,
.bytemd-preview ::-webkit-scrollbar,
.CodeMirror-vscrollbar ::-webkit-scrollbar {
  width: 12px !important;
  height: 12px !important;
  display: block !important;
}

.bytemd-editor ::-webkit-scrollbar-track,
.bytemd-preview ::-webkit-scrollbar-track,
.CodeMirror-vscrollbar ::-webkit-scrollbar-track {
  background: #27272a !important; /* Dark track */
}

.bytemd-editor ::-webkit-scrollbar-thumb,
.bytemd-preview ::-webkit-scrollbar-thumb,
.CodeMirror-vscrollbar ::-webkit-scrollbar-thumb {
  background: #3b82f6 !important; /* Brighter Blue for visibility testing */
  border-radius: 6px !important;
  border: 2px solid #27272a !important;
}

.bytemd-editor ::-webkit-scrollbar-thumb:hover,
.bytemd-preview ::-webkit-scrollbar-thumb:hover,
.CodeMirror-vscrollbar ::-webkit-scrollbar-thumb:hover {
  background: #a1a1aa !important; /* Zinc 400 */
}

/* Forcing CodeMirror native scrollbars to look alike if they exist as DOM nodes */
.CodeMirror-vscrollbar, .CodeMirror-hscrollbar {
  display: block !important;
  z-index: 10 !important; 
}

/* Fullscreen Override - Fix Sidebar Overlap */
.bytemd-fullscreen {
  z-index: 9999 !important; /* Above everything */
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
}

/* --- Frontmatter Container Stylish --- */
.fm-container {
  font-family: 'JetBrains Mono', monospace !important;
  background: rgba(0, 0, 0, 0.3) !important;
  border: 1px dashed rgba(255,255,255,0.1) !important;
  backdrop-filter: blur(4px);
}
</style>
