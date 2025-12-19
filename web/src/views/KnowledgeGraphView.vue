<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import cytoscape from 'cytoscape'

const router = useRouter()
const graphContainer = ref(null)
const loading = ref(true)
const error = ref('')
const stats = ref({ questions: 0, knowledge_points: 0 })
const selectedNode = ref(null)
const activeSubject = ref('comprehensive') // 'all', 'comprehensive' (math+logic), 'english'

// Store raw data
const rawData = ref({ nodes: [], edges: [] })

let cy = null

// 🎨 Neo-Linear Color Palette (Dark Theme Optimized)
const colors = {
  // Vibrant accents on dark backgrounds
  math: { bg: 'rgba(244, 63, 94, 0.1)', border: '#fb7185', text: '#fda4af' },     // Rose
  logic: { bg: 'rgba(245, 158, 11, 0.1)', border: '#fbbf24', text: '#fcd34d' },    // Amber
  english: { bg: 'rgba(16, 185, 129, 0.1)', border: '#34d399', text: '#6ee7b7' },  // Emerald
  knowledge: { bg: 'rgba(99, 102, 241, 0.15)', border: '#818cf8', text: '#a5b4fc' } // Indigo
}

async function loadGraph() {
  loading.value = true
  error.value = ''
  
  try {
    const res = await fetch('http://localhost:8000/api/graph')
    if (!res.ok) throw new Error('无法加载图谱数据')
    
    const data = await res.json()
    rawData.value = data
    stats.value = data.stats
    
    // Initial render
    renderGraph()
    
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function getFilteredData() {
  const { nodes, edges } = rawData.value
  
  if (activeSubject.value === 'all') {
    return { nodes, edges }
  }
  
  // Filter nodes
  const validSubjects = activeSubject.value === 'comprehensive' 
    ? ['math', 'logic'] 
    : ['english']
    
  // 1. Get relevant Question Nodes
  const questionNodes = nodes.filter(n => n.data.type === 'question' && validSubjects.includes(n.data.subject))
  const questionIds = new Set(questionNodes.map(n => n.data.id))
  
  // 2. Get relevant Edges (connected to these questions)
  // Edges are directional usually, but we check both ends
  const validEdges = edges.filter(e => questionIds.has(e.data.source) || questionIds.has(e.data.target))
  
  // 3. Get relevant Knowledge Points (connected by these edges)
  const connectedKpIds = new Set()
  validEdges.forEach(e => {
    if (questionIds.has(e.data.source)) connectedKpIds.add(e.data.target)
    if (questionIds.has(e.data.target)) connectedKpIds.add(e.data.source)
  })
  
  const kpNodes = nodes.filter(n => n.data.type === 'knowledge' && connectedKpIds.has(n.data.id))
  
  return {
    nodes: [...questionNodes, ...kpNodes],
    edges: validEdges
  }
}

function renderGraph() {
  const { nodes, edges } = getFilteredData()
  initCytoscape(nodes, edges)
}

// Watch subject change to re-render
watch(activeSubject, () => {
  renderGraph()
  selectedNode.value = null
})

function initCytoscape(nodes, edges) {
  if (cy) {
    cy.destroy()
  }
  
  cy = cytoscape({
    container: graphContainer.value,
    elements: [...nodes, ...edges],
    
    style: [
      // 📝 Question Nodes - Rounded Rectangle
      {
        selector: 'node[type="question"]',
        style: {
          'shape': 'round-rectangle',
          'width': 'label',
          'height': 32,
          'padding': '8px',
          'background-color': '#09090b', // Zinc 950
          'border-width': 1,
          'border-color': (ele) => colors[ele.data('subject')]?.border || '#52525b',
          'label': 'data(id)', // Use ID for questions
          'color': '#ffffff', 
          'font-size': '12px',
          'font-family': 'Inter, sans-serif',
          'font-weight': 500,
          'text-valign': 'center',
          'text-halign': 'center',
          'z-index': 10
        }
      },
      // 💡 Knowledge Point Nodes - Pill/Capsule with Glow
      {
        selector: 'node[type="knowledge"]',
        style: {
          'shape': 'round-rectangle',
          'width': 'label',
          'height': 36,
          'padding': '12px',
          'background-color': '#18181b', // Zinc 900
          'border-width': 2,
          'border-style': 'solid',
          'border-color': colors.knowledge.border,
          'label': 'data(label)',
          'color': colors.knowledge.text,
          'font-size': '13px',
          'font-weight': 600,
          'text-valign': 'center',
          'text-halign': 'center',
          'z-index': 20
        }
      },
      // 🔗 Edges - Subtle Lines
      {
        selector: 'edge',
        style: {
          'width': 1,
          'line-color': '#3f3f46', // Zinc 700
          'target-arrow-color': '#3f3f46',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'arrow-scale': 0.8,
          'opacity': 0.4
        }
      },
      // ✨ Hover/Selected State
      {
        selector: 'node:selected',
        style: {
          'border-width': 2,
          'border-color': '#fff',
          'background-color': '#27272a', // Zinc 800
          'color': '#fff',
          'z-index': 30,
          'overlay-color': '#ffffff',
          'overlay-padding': '4px',
          'overlay-opacity': 0.2
        }
      },
      {
        selector: 'edge:selected',
        style: {
          'width': 2,
          'line-color': '#fff',
          'target-arrow-color': '#fff',
          'opacity': 1,
          'z-index': 30
        }
      }
    ],
    
    layout: {
      name: 'cose',
      animate: true,
      animationDuration: 800,
      randomize: false,
      componentSpacing: 80,
      nodeRepulsion: 8000,
      nodeOverlap: 20,
      idealEdgeLength: 100,
      edgeElasticity: 100,
      nestingFactor: 5,
      gravity: 0.1, // Low gravity
      numIter: 1000,
      padding: 60
    },
    
    // Interaction
    minZoom: 0.5,
    maxZoom: 2.5,
    wheelSensitivity: 0.2
  })
  
  // Event listeners
  cy.on('tap', 'node', (evt) => {
    selectedNode.value = evt.target.data()
  })

  // Double tap to navigate
  cy.on('dbltap', 'node', (evt) => {
    const data = evt.target.data()
    if (data.type === 'question') {
      router.push('/question/' + data.id)
    } else if (data.type === 'knowledge') {
      router.push('/knowledge/' + data.subject + '/' + data.id)
    }
  })
  
  cy.on('tap', (evt) => {
    if (evt.target === cy) {
      selectedNode.value = null
    }
  })

  // Add nice hover effect for neighbors
  cy.on('mouseover', 'node', (e) => {
    document.body.style.cursor = 'pointer'
    const node = e.target
    node.connectedEdges().animate({
      style: { lineColor: '#fff', width: 2, opacity: 0.8 }
    }, { duration: 200 })
  })

  cy.on('mouseout', 'node', (e) => {
    document.body.style.cursor = 'default'
    const node = e.target
    node.connectedEdges().animate({
      style: { lineColor: '#3f3f46', width: 1, opacity: 0.4 }
    }, { duration: 200 })
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
  
  if (layoutName === 'cose') {
    Object.assign(layoutOptions, {
      idealEdgeLength: 100,
      nodeRepulsion: 8000,
      gravity: 0.1
    })
  } else if (layoutName === 'concentric') {
    Object.assign(layoutOptions, {
      minNodeSpacing: 60,
      concentric: (node) => node.data('type') === 'knowledge' ? 2 : 1,
      levelWidth: () => 1
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
        <h1 class="text-3xl font-extrabold text-white">知识图谱</h1>
        <p class="text-zinc-500 mt-1">可视化题目与知识点的关联关系</p>
      </div>
      
      <!-- 🏷️ Subject Tabs -->
      <div class="flex p-1 bg-zinc-900 rounded-lg border border-white/5">
        <button 
          @click="activeSubject = 'comprehensive'"
          class="px-4 py-1.5 rounded-md text-sm font-medium transition-all"
          :class="activeSubject === 'comprehensive' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'"
        >
          🎓 管综 (数/逻)
        </button>
        <button 
          @click="activeSubject = 'english'"
          class="px-4 py-1.5 rounded-md text-sm font-medium transition-all"
          :class="activeSubject === 'english' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'"
        >
          🔤 英语
        </button>
        <button 
          @click="activeSubject = 'all'"
          class="px-4 py-1.5 rounded-md text-sm font-medium transition-all"
          :class="activeSubject === 'all' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'"
        >
          👁️ 全部
        </button>
      </div>

      <div class="flex gap-3">
        <div class="flex items-center gap-1 pr-4 border-r border-white/10 mr-4">
          <button @click="relayout('cose')" class="btn btn-ghost text-xs px-2">力导向</button>
          <button @click="relayout('circle')" class="btn btn-ghost text-xs px-2">环形</button>
        </div>
        <button @click="resetView" class="btn btn-secondary text-sm">🔍 重置</button>
        <button @click="loadGraph" class="btn btn-primary text-sm" :disabled="loading">🔄 刷新</button>
      </div>
    </header>
    
    <!-- Stats Bar (Simplified) -->
    <div class="flex gap-6 mb-4 px-4 text-xs text-zinc-500 border-b border-white/5 pb-4">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-red-400"></span> 数学
      </div>
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-amber-400"></span> 逻辑
      </div>
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-emerald-400"></span> 英语
      </div>
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full border border-indigo-400 bg-indigo-500/20"></span> 知识点
      </div>
      <div class="ml-auto">
         当前视图: {{ getFilteredData().nodes.length }} 节点
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex gap-6 min-h-0">
      <!-- Graph Container -->
      <div class="flex-1 relative group">
        <!-- Loading -->
        <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-black/80 backdrop-blur-sm z-10 rounded-2xl">
          <div class="text-center">
            <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p class="mt-4 text-zinc-500 text-sm">正在构建图谱...</p>
          </div>
        </div>
        
        <!-- Cytoscape Container -->
        <div ref="graphContainer" class="w-full h-full bg-[#09090b] rounded-2xl border border-white/5 shadow-inner"></div>
        
        <div class="absolute bottom-4 left-4 text-xs text-zinc-600 pointer-events-none">
          💡 提示: 滚动缩放 · 拖拽移动 · 点击选中 · 双击跳转
        </div>
      </div>
      
      <!-- Selected Node Info Panel -->
      <transition name="fade">
        <div v-if="selectedNode" class="w-80 flex-shrink-0">
          <div class="card p-5 sticky top-6 border-zinc-800 bg-zinc-900/50 backdrop-blur-xl">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center text-lg border border-white/10"
                   :class="{
                     'bg-indigo-500/10 text-indigo-400': selectedNode.type === 'knowledge',
                     'bg-red-500/10 text-red-400': selectedNode.subject === 'math' && selectedNode.type === 'question',
                     'bg-amber-500/10 text-amber-400': selectedNode.subject === 'logic' && selectedNode.type === 'question',
                     'bg-green-500/10 text-green-400': selectedNode.subject === 'english' && selectedNode.type === 'question'
                   }">
                {{ selectedNode.type === 'knowledge' ? '💡' : '📝' }}
              </div>
              <div>
                <div class="font-bold text-white text-sm line-clamp-1" :title="selectedNode.label">{{ selectedNode.label }}</div>
                <div class="text-xs text-zinc-500 mt-0.5">{{ selectedNode.type === 'knowledge' ? '知识点' : '题目' }}</div>
              </div>
            </div>
            
            <div class="space-y-3 text-sm border-t border-white/5 pt-4">
              <div class="flex justify-between">
                <span class="text-zinc-500">ID</span>
                <span class="font-mono text-zinc-300 text-xs">{{ selectedNode.id }}</span>
              </div>
              <div class="flex justify-between" v-if="selectedNode.subject">
                <span class="text-zinc-500">科目</span>
                <span class="font-medium text-zinc-300 capitalize">{{ selectedNode.subject }}</span>
              </div>
              <div class="flex justify-between" v-if="selectedNode.difficulty">
                <span class="text-zinc-500">难度</span>
                <span class="text-yellow-500 tracking-widest text-xs">{{ '★'.repeat(selectedNode.difficulty) }}</span>
              </div>
               <div class="flex justify-between" v-if="selectedNode.connections !== undefined">
                <span class="text-zinc-500">关联数</span>
                <span class="font-medium text-zinc-300">{{ selectedNode.connections }}</span>
              </div>
            </div>
            
            <router-link v-if="selectedNode.type === 'question'" 
                         :to="'/question/' + selectedNode.id" 
                         class="btn btn-primary w-full mt-6 text-sm py-2">
              👉 查看题目
            </router-link>
            
            <router-link v-if="selectedNode.type === 'knowledge'" 
                         :to="'/knowledge/' + selectedNode.subject + '/' + selectedNode.id" 
                         class="btn btn-secondary w-full mt-6 text-sm py-2 border-white/10 hover:bg-white/5">
              📚 查看知识点
            </router-link>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
