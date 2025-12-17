<script setup>
</script>

<template>
  <div class="flex min-h-screen">
    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r border-slate-200 flex flex-col fixed h-screen z-10">
      <div class="p-6 flex items-center gap-3 border-b border-slate-200">
        <div class="w-8 h-8 bg-primary-600 text-white rounded-lg flex items-center justify-center font-bold">M</div>
        <span class="font-bold text-lg text-slate-900">MEM Study</span>
      </div>
      
      <nav class="flex-1 p-4 overflow-y-auto">
        <router-link to="/" class="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-600 font-medium hover:bg-slate-50 hover:text-slate-900 transition-colors" active-class="!bg-primary-50 !text-primary-700">
          <span>📊</span>
          仪表盘
        </router-link>
        
        <div class="mt-6">
          <span class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 px-4">题库</span>
          <router-link to="/new/question" class="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-600 font-medium hover:bg-slate-50 hover:text-slate-900 transition-colors" active-class="!bg-primary-50 !text-primary-700">
            <span>➕</span> 新增题目
          </router-link>
          <router-link to="/smart-entry" class="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-600 font-medium hover:bg-slate-50 hover:text-slate-900 transition-colors" active-class="!bg-primary-50 !text-primary-700">
            <span>🤖</span> 智能录入
          </router-link>
          <router-link to="/pdf-import" class="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-600 font-medium hover:bg-slate-50 hover:text-slate-900 transition-colors" active-class="!bg-primary-50 !text-primary-700">
            <span>📄</span> PDF导入
          </router-link>
          <router-link to="/questions" class="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-600 font-medium hover:bg-slate-50 hover:text-slate-900 transition-colors" active-class="!bg-primary-50 !text-primary-700">
            <span>📝</span> 全部题目
          </router-link>
        </div>
        
        <div class="mt-6">
          <span class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 px-4">知识体系</span>
          <router-link to="/graph" class="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-600 font-medium hover:bg-slate-50 hover:text-slate-900 transition-colors" active-class="!bg-primary-50 !text-primary-700">
            <span>🧠</span> 知识图谱
          </router-link>
          <router-link to="/curriculum" class="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-600 font-medium hover:bg-slate-50 hover:text-slate-900 transition-colors" active-class="!bg-primary-50 !text-primary-700">
            <span>📚</span> 学习路径
          </router-link>
        </div>
      </nav>

      <div class="p-4 border-t border-slate-200 flex items-center gap-3">
        <div class="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center text-lg">👨‍💻</div>
        <div>
          <div class="font-semibold text-sm text-slate-900">Developer</div>
          <div class="text-xs text-slate-500">Backend Eng.</div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 ml-64 bg-slate-50 p-8 min-h-screen">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
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
