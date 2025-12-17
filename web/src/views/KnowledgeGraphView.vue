<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import cytoscape from 'cytoscape'

const graphContainer = ref(null)
const loading = ref(true)
const error = ref('')
const stats = ref({ questions: 0, knowledge_points: 0 })
const selectedNode = ref(null)

let cy = null

// Color schemes for subjects
const colors = {
  math: { bg: '#ef4444', border: '#b91c1c', light: '#fecaca' },
  logic: { bg: '#f59e0b', border: '#b45309', light: '#fde68a' },
  english: { bg: '#22c55e', border: '#15803d', light: '#bbf7d0' },
  knowledge: { bg: '#8b5cf6', border: '#6d28d9', light: '#ddd6fe' }
}

async function loadGraph() {
  loading.value = true
  error.value = ''
  
  try {
    const res = await fetch('http://localhost:8000/api/graph')
    if (!res.ok) throw new Error('无法加载图谱数据')
    
    const data = await res.json()
    stats.value = data.stats
    
    initCytoscape(data.nodes, data.edges)
    
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function initCytoscape(nodes, edges) {
  if (cy) {
    cy.destroy()
  }
  
  cy = cytoscape({
    container: graphContainer.value,
    elements: [...nodes, ...edges],
    
    style: [
      // Question nodes
      {
        selector: 'node[type="question"]',
        style: {
          'shape': 'round-rectangle',
          'width': 60,
          'height': 36,
          'background-color': (ele) => colors[ele.data('subject')]?.bg || '#6b7280',
          'border-width': 3,
          'border-color': (ele) => colors[ele.data('subject')]?.border || '#374151',
          'label': 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
          'color': '#ffffff',
          'font-size': '11px',
          'font-weight': 'bold',
          'text-outline-width': 0,
          'overlay-padding': '6px',
          'z-index': 10
        }
      },
      // Knowledge point nodes
      {
        selector: 'node[type="knowledge"]',
        style: {
          'shape': 'ellipse',
          'width': (ele) => Math.max(ele.data('label').length * 12, 80),
          'height': 44,
          'background-color': colors.knowledge.bg,
          'border-width': 3,
          'border-color': colors.knowledge.border,
          'label': 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
          'color': '#ffffff',
          'font-size': '12px',
          'font-weight': 'bold',
          'text-wrap': 'wrap',
          'text-max-width': '120px',
          'z-index': 20
        }
      },
      // Edges
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': '#cbd5e1',
          'target-arrow-color': '#94a3b8',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'opacity': 0.6
        }
      },
      // Hover effects
      {
        selector: 'node:selected',
        style: {
          'border-width': 4,
          'border-color': '#3b82f6',
          'box-shadow': '0 0 0 4px rgba(59, 130, 246, 0.3)'
        }
      },
      {
        selector: 'edge:selected',
        style: {
          'width': 3,
          'line-color': '#3b82f6',
          'opacity': 1
        }
      }
    ],
    
    layout: {
      name: 'cose',
      animate: true,
      animationDuration: 1000,
      nodeDimensionsIncludeLabels: true,
      idealEdgeLength: 150,
      nodeRepulsion: 8000,
      gravity: 0.3,
      padding: 50
    },
    
    // Interaction
    minZoom: 0.3,
    maxZoom: 3,
    wheelSensitivity: 0.3
  })
  
  // Event handlers
  cy.on('tap', 'node', (evt) => {
    const node = evt.target
    selectedNode.value = {
      id: node.data('id'),
      label: node.data('label'),
      type: node.data('type'),
      subject: node.data('subject'),
      difficulty: node.data('difficulty'),
      connections: cy.edges().filter(e => 
        e.data('source') === node.data('id') || e.data('target') === node.data('id')
      ).length
    }
  })
  
  cy.on('tap', (evt) => {
    if (evt.target === cy) {
      selectedNode.value = null
    }
  })
}

function resetView() {
  if (cy) {
    cy.fit(50)
    cy.center()
  }
}

function relayout(layoutName) {
  if (!cy) return
  
  const layoutOptions = {
    name: layoutName,
    animate: true,
    animationDuration: 800,
    fit: true,
    padding: 60,
    nodeDimensionsIncludeLabels: true
  }
  
  // Add specific options for each layout
  if (layoutName === 'cose') {
    Object.assign(layoutOptions, {
      idealEdgeLength: 120,
      nodeRepulsion: 6000,
      gravity: 0.5,
      numIter: 1000
    })
  } else if (layoutName === 'concentric') {
    Object.assign(layoutOptions, {
      minNodeSpacing: 60,
      concentric: (node) => node.data('type') === 'knowledge' ? 2 : 1,
      levelWidth: () => 1
    })
  } else if (layoutName === 'circle') {
    Object.assign(layoutOptions, {
      spacingFactor: 1.5
    })
  }
  
  cy.layout(layoutOptions).run()
}

onMounted(() => {
  loadGraph()
})

onUnmounted(() => {
  if (cy) {
    cy.destroy()
  }
})
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <header class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-3xl font-extrabold text-slate-900">知识图谱</h1>
        <p class="text-slate-500 mt-1">可视化题目与知识点的关联关系</p>
      </div>
      <div class="flex gap-3">
        <button @click="relayout('cose')" class="btn btn-ghost text-sm">力导向</button>
        <button @click="relayout('circle')" class="btn btn-ghost text-sm">环形</button>
        <button @click="relayout('concentric')" class="btn btn-ghost text-sm">同心圆</button>
        <button @click="resetView" class="btn btn-secondary">🔍 重置视图</button>
        <button @click="loadGraph" class="btn btn-primary" :disabled="loading">🔄 刷新</button>
      </div>
    </header>
    
    <!-- Stats Bar -->
    <div class="flex gap-6 mb-6">
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 rounded bg-red-500"></span>
        <span class="text-sm text-slate-600">数学题目</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 rounded bg-amber-500"></span>
        <span class="text-sm text-slate-600">逻辑题目</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 rounded bg-green-500"></span>
        <span class="text-sm text-slate-600">英语题目</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 rounded-full bg-purple-500"></span>
        <span class="text-sm text-slate-600">知识点</span>
      </div>
      <div class="ml-auto text-sm text-slate-500">
        {{ stats.questions }} 道题目 · {{ stats.knowledge_points }} 个知识点
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex gap-6 min-h-0">
      <!-- Graph Container -->
      <div class="flex-1 relative">
        <!-- Loading -->
        <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
          <div class="text-center">
            <div class="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p class="mt-4 text-slate-500">加载图谱中...</p>
          </div>
        </div>
        
        <!-- Error -->
        <div v-if="error" class="absolute inset-0 flex items-center justify-center bg-red-50 z-10">
          <div class="text-center">
            <p class="text-red-600 mb-4">{{ error }}</p>
            <button @click="loadGraph" class="btn btn-primary">重试</button>
          </div>
        </div>
        
        <!-- Cytoscape Container -->
        <div ref="graphContainer" class="w-full h-full bg-slate-50 rounded-2xl border border-slate-200 shadow-inner"></div>
      </div>
      
      <!-- Selected Node Info Panel -->
      <div v-if="selectedNode" class="w-80 flex-shrink-0">
        <div class="card p-6 sticky top-6">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-full flex items-center justify-center text-white text-lg"
                 :class="{
                   'bg-purple-500': selectedNode.type === 'knowledge',
                   'bg-red-500': selectedNode.subject === 'math' && selectedNode.type === 'question',
                   'bg-amber-500': selectedNode.subject === 'logic' && selectedNode.type === 'question',
                   'bg-green-500': selectedNode.subject === 'english' && selectedNode.type === 'question'
                 }">
              {{ selectedNode.type === 'knowledge' ? '💡' : '📝' }}
            </div>
            <div>
              <div class="font-bold text-slate-900">{{ selectedNode.label }}</div>
              <div class="text-sm text-slate-500">{{ selectedNode.type === 'knowledge' ? '知识点' : '题目' }}</div>
            </div>
          </div>
          
          <div class="space-y-3 text-sm">
            <div class="flex justify-between">
              <span class="text-slate-500">ID</span>
              <span class="font-medium text-slate-700">{{ selectedNode.id }}</span>
            </div>
            <div class="flex justify-between" v-if="selectedNode.subject">
              <span class="text-slate-500">科目</span>
              <span class="font-medium text-slate-700">
                {{ selectedNode.subject === 'math' ? '数学' : selectedNode.subject === 'logic' ? '逻辑' : '英语' }}
              </span>
            </div>
            <div class="flex justify-between" v-if="selectedNode.difficulty">
              <span class="text-slate-500">难度</span>
              <span class="text-yellow-500">{{ '★'.repeat(selectedNode.difficulty) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">关联数</span>
              <span class="font-medium text-slate-700">{{ selectedNode.connections }}</span>
            </div>
          </div>
          
          <router-link v-if="selectedNode.type === 'question'" 
                       :to="'/question/' + selectedNode.id" 
                       class="btn btn-primary w-full mt-6">
            查看题目详情
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes spin {
  to { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
