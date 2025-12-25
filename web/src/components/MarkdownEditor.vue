<script setup>
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
</script>

<template>
  <div class="bytemd-wrapper" :class="{ 'is-readonly': readonly }">
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
  height: 100%;
}

.bytemd {
  height: 100% !important;
  border: none !important;
  border-radius: 0 !important;
  background: transparent !important;
}

/* --- Toolbar --- */
.bytemd-toolbar {
  background-color: #09090b !important; /* Zinc 950 */
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
  padding: 0.5rem 1rem !important;
  flex-shrink: 0;
  /* height: auto !important; */ 
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
  background-color: #09090b !important;
  /* Do not force flex overrides, trust bytemd layout, just ensure it fills height */
  height: 100% !important; 
}

/* --- Editor (Left Pane) - Light Mode for Clarity --- */
.bytemd-editor {
  /* Let CodeMirror handle sizing */
  height: 100% !important;
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
  font-size: 15px !important; /* Slightly larger for clarity */
  line-height: 1.7 !important;
  height: 100% !important;
}

.CodeMirror-gutters {
  background-color: #f8fafc !important; /* Slate 50 */
  border-right: 1px solid #e2e8f0 !important;
}

.CodeMirror-linenumber {
  color: #cbd5e1 !important; /* Slate 300 */
}

.CodeMirror-cursor {
  border-left: 2px solid #2563eb !important; /* Blue 600 */
}

.CodeMirror-selected {
  background-color: rgba(37, 99, 235, 0.15) !important;
}

/* --- Preview (Right Pane) --- */
.bytemd-preview {
  height: 100% !important;
  overflow-y: auto !important;
  padding-bottom: 100px !important;
}

.bytemd-split .bytemd-preview {
  border-left: 1px solid rgba(255, 255, 255, 0.05) !important;
  background-color: #0c0c0e !important; 
  padding: 2rem 3rem !important; 
  padding-bottom: 8rem !important; 
}

.markdown-body {
  font-family: 'Inter', sans-serif !important;
  color: #e4e4e7 !important;
  line-height: 1.8 !important;
  font-size: 16px !important;
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
  border-top: 1px solid rgba(255, 255, 255, 0.05) !important;
  background-color: #09090b !important;
  color: #52525b !important;
  font-size: 12px !important;
  padding: 4px 16px !important;
}

/* --- Scrollbars --- */
.bytemd-editor ::-webkit-scrollbar,
.bytemd-preview ::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.bytemd-editor ::-webkit-scrollbar-track,
.bytemd-preview ::-webkit-scrollbar-track {
  background: transparent;
}

.bytemd-editor ::-webkit-scrollbar-thumb,
.bytemd-preview ::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.bytemd-editor ::-webkit-scrollbar-thumb:hover,
.bytemd-preview ::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* --- Frontmatter Container Stylish --- */
.fm-container {
  font-family: 'JetBrains Mono', monospace !important;
  background: rgba(0, 0, 0, 0.3) !important;
  border: 1px dashed rgba(255,255,255,0.1) !important;
  backdrop-filter: blur(4px);
}
</style>
