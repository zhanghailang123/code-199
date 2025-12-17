import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: HomeView
        },
        {
            path: '/new/question',
            name: 'new-question',
            component: () => import('../views/NewQuestionView.vue')
        },
        {
            path: '/smart-entry',
            name: 'smart-entry',
            component: () => import('../views/SmartEntryView.vue')
        },
        {
            path: '/question/:id',
            name: 'question',
            component: () => import('../views/ContentView.vue')
        },
        {
            path: '/graph',
            name: 'graph',
            component: () => import('../views/KnowledgeGraphView.vue')
        },
        {
            path: '/curriculum',
            name: 'curriculum',
            component: () => import('../views/CurriculumView.vue')
        },
        {
            path: '/questions',
            name: 'questions',
            component: () => import('../views/HomeView.vue')  // Redirect to home for now
        },
        {
            path: '/pdf-import',
            name: 'pdf-import',
            component: () => import('../views/PdfUploadView.vue')
        },
        {
            path: '/knowledge/:category/:id',
            name: 'knowledge',
            component: () => import('../views/ContentView.vue')
        }
    ]
})

export default router
