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
.bytemd-wrapper {
  height: 100%;
}

.bytemd {
  height: 100% !important; /* Inherit from parent instead of fixed height */
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.bytemd-toolbar {
  background-color: #18181b !important; /* Zinc 900 */
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #e4e4e7 !important;
}

.bytemd-toolbar-icon {
  color: #a1a1aa !important;
}
.bytemd-toolbar-icon:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
}

.bytemd-body {
  background-color: #09090b !important; /* Zinc 950 */
  color: #e4e4e7 !important;
}

.bytemd-editor textarea {
  background-color: #09090b !important;
  color: #e4e4e7 !important;
}

.bytemd-split .bytemd-preview {
  border-left: 1px solid rgba(255, 255, 255, 0.1) !important;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important; /* Slate 800 to Slate 900 - softer than black */
  padding: 1.5rem !important;
}

.markdown-body {
  font-family: 'Inter', sans-serif;
  color: #e4e4e7;
  background-color: transparent !important;
}

/* Typography Overrides for Markdown Body */
.markdown-body h1, .markdown-body h2, .markdown-body h3 {
  color: #fff !important;
  border-bottom-color: rgba(255, 255, 255, 0.1) !important;
}

.markdown-body pre {
  background-color: #1f1f23 !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.markdown-body code {
  color: #a5b4fc !important; /* Indigo 300 */
}

.bytemd-status {
  border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
  background-color: #18181b !important;
  color: #71717a !important;
}

/* Custom Frontmatter Table Styling */
.fm-container table {
  border-collapse: collapse;
}
.fm-container td {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.fm-container tr:last-child td {
  border-bottom: none;
}


/* Fullscreen fix */
.bytemd-fullscreen {
  z-index: 1000;
}
</style>
