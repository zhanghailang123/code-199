<script setup>
import { ref, onErrorCaptured } from 'vue'

// Global error state to show user-friendly error UI
const globalError = ref(null)

// Capture errors from child components to prevent app freeze
onErrorCaptured((error, instance, info) => {
  console.error('Vue Error Captured:', error, info)
  globalError.value = {
    message: error.message || '页面发生错误',
    info: info
  }
  // Return false to stop error propagation (prevents app freeze)
  return false
})

function clearError() {
  globalError.value = null
}
</script>

<template>
  <div class="flex min-h-screen">
    <!-- Sidebar - Glass Dark Style -->
    <aside class="w-64 sidebar-glass border-r border-white/5 flex flex-col fixed h-screen z-10">
      <div class="p-6 flex items-center gap-3 border-b border-white/5">
        <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-xl flex items-center justify-center font-bold text-lg shadow-lg shadow-blue-500/20">M</div>
        <span class="font-bold text-xl text-white tracking-wide">MEM Study</span>
      </div>
      
      <nav class="flex-1 p-4 overflow-y-auto">
        <router-link to="/" class="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 font-medium hover:bg-white/5 hover:text-white transition-all" active-class="!bg-blue-600/20 !text-blue-100 !border !border-blue-500/20 shadow-sm shadow-blue-500/10">
          <span>📊</span>
          仪表盘
        </router-link>
        
        <div class="mt-6">
          <span class="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2 px-4">题库</span>
          <router-link to="/new/question" class="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 font-medium hover:bg-white/5 hover:text-white transition-all" active-class="!bg-blue-600/20 !text-blue-100 !border !border-blue-500/20 shadow-sm shadow-blue-500/10">
            <span>➕</span> 新增题目
          </router-link>
          <router-link to="/smart-entry" class="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 font-medium hover:bg-white/5 hover:text-white transition-all" active-class="!bg-blue-600/20 !text-blue-100 !border !border-blue-500/20 shadow-sm shadow-blue-500/10">
            <span>🤖</span> 智能录入
          </router-link>
          <router-link to="/pdf-import" class="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 font-medium hover:bg-white/5 hover:text-white transition-all" active-class="!bg-blue-600/20 !text-blue-100 !border !border-blue-500/20 shadow-sm shadow-blue-500/10">
            <span>📄</span> PDF导入
          </router-link>
          <router-link to="/questions" class="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 font-medium hover:bg-white/5 hover:text-white transition-all" active-class="!bg-blue-600/20 !text-blue-100 !border !border-blue-500/20 shadow-sm shadow-blue-500/10">
            <span>📝</span> 全部题目
          </router-link>
        </div>
        
        <div class="mt-6">
          <span class="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2 px-4">知识体系</span>
          <router-link to="/graph" class="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 font-medium hover:bg-white/5 hover:text-white transition-all" active-class="!bg-blue-600/20 !text-blue-100 !border !border-blue-500/20 shadow-sm shadow-blue-500/10">
            <span>🧠</span> 知识图谱
          </router-link>
          <router-link to="/curriculum" class="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 font-medium hover:bg-white/5 hover:text-white transition-all" active-class="!bg-blue-600/20 !text-blue-100 !border !border-blue-500/20 shadow-sm shadow-blue-500/10">
            <span>📚</span> 学习路径
          </router-link>
          <router-link to="/vocabulary" class="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 font-medium hover:bg-white/5 hover:text-white transition-all" active-class="!bg-blue-600/20 !text-blue-100 !border !border-blue-500/20 shadow-sm shadow-blue-500/10">
            <span>🔤</span> 单词本
          </router-link>
        </div>
      </nav>

      <div class="p-4 border-t border-white/5 flex items-center gap-3">
        <div class="w-10 h-10 bg-gradient-to-br from-slate-700 to-slate-800 rounded-full flex items-center justify-center text-lg shadow-inner border border-white/5">👨‍💻</div>
        <div>
          <div class="font-semibold text-sm text-slate-200">Developer</div>
          <div class="text-xs text-slate-500">Backend Eng.</div>
        </div>
      </div>
    </aside>

    <!-- Main Content - Transparent to show gradient background -->
    <main class="flex-1 ml-64 p-8 min-h-screen">
      <!-- Global Error Toast -->
      <div v-if="globalError" 
           class="fixed top-4 right-4 z-50 bg-red-500 text-white px-6 py-4 rounded-xl shadow-lg max-w-md">
        <div class="flex items-start gap-3">
          <span class="text-2xl">⚠️</span>
          <div class="flex-1">
            <div class="font-bold">页面发生错误</div>
            <div class="text-sm opacity-90 mt-1">{{ globalError.message }}</div>
          </div>
          <button @click="clearError" class="text-2xl hover:opacity-70">×</button>
        </div>
      </div>
      
      <!-- Router View with Error Recovery -->
      <router-view v-slot="{ Component }" :key="$route.fullPath">
        <transition name="fade" mode="out-in">
          <component :is="Component" @vue:error="clearError" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
