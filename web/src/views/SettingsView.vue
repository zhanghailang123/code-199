<script setup>
import { ref, onMounted } from 'vue'
import { API_BASE } from '../config/api.js'

// State
const config = ref({
  api_key_masked: '',
  base_url: '',
  model: ''
})
const newApiKey = ref('')
const showApiKey = ref(false)
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)
const saveMessage = ref('')

// Common models
const commonModels = [
  'gpt-4o',
  'gpt-4o-mini',
  'gpt-4-turbo',
  'gpt-3.5-turbo',
  'gemini-2.0-flash-exp',
  'gemini-2.5-pro',
  'claude-3-5-sonnet',
  'deepseek-chat'
]

// Fetch current config
async function fetchConfig() {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/api/config`)
    if (res.ok) {
      const data = await res.json()
      config.value = data.llm
    }
  } catch (e) {
    console.error('Failed to fetch config:', e)
  } finally {
    loading.value = false
  }
}

// Save config
async function saveConfig() {
  saving.value = true
  saveMessage.value = ''
  try {
    const updateData = {
      base_url: config.value.base_url,
      model: config.value.model
    }
    
    // Only update API key if user entered a new one
    if (newApiKey.value.trim()) {
      updateData.api_key = newApiKey.value.trim()
    }
    
    const res = await fetch(`${API_BASE}/api/config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updateData)
    })
    
    if (res.ok) {
      const data = await res.json()
      config.value = data.llm
      newApiKey.value = ''
      saveMessage.value = '✅ 配置已保存'
      setTimeout(() => saveMessage.value = '', 3000)
    } else {
      saveMessage.value = '❌ 保存失败'
    }
  } catch (e) {
    console.error('Failed to save config:', e)
    saveMessage.value = '❌ 保存失败: ' + e.message
  } finally {
    saving.value = false
  }
}

// Test connection
async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    const testData = {
      base_url: config.value.base_url,
      model: config.value.model
    }
    // Only send API key if user entered a new one, otherwise backend uses saved key
    if (newApiKey.value.trim()) {
      testData.api_key = newApiKey.value.trim()
    }

    const res = await fetch(`${API_BASE}/api/config/test`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(testData)
    })
    const data = await res.json()
    testResult.value = data
  } catch (e) {
    testResult.value = { success: false, error: e.message }
  } finally {
    testing.value = false
  }
}

onMounted(fetchConfig)
</script>

<template>
  <div class="settings-page">
    <header class="page-header">
      <h1>⚙️ 系统设置</h1>
    </header>
    
    <div class="settings-content">
      <!-- LLM Configuration -->
      <section class="settings-section">
        <h2>🤖 LLM 配置</h2>
        <p class="section-desc">配置用于智能分析的大语言模型接口</p>
        
        <div v-if="loading" class="loading">加载中...</div>
        
        <div v-else class="form-group">
          <!-- API Key -->
          <div class="form-item">
            <label>API Key</label>
            <div class="input-with-button">
              <input 
                v-if="showApiKey"
                v-model="newApiKey"
                type="text"
                :placeholder="config.api_key_masked || '输入新的 API Key'"
                class="form-input"
              >
              <input 
                v-else
                v-model="newApiKey"
                type="password"
                :placeholder="config.api_key_masked || '输入新的 API Key'"
                class="form-input"
              >
              <button @click="showApiKey = !showApiKey" class="toggle-btn">
                {{ showApiKey ? '🙈' : '👁️' }}
              </button>
            </div>
            <span class="form-hint">当前: {{ config.api_key_masked || '未设置' }}</span>
          </div>
          
          <!-- Base URL -->
          <div class="form-item">
            <label>Base URL</label>
            <input 
              v-model="config.base_url"
              type="text"
              placeholder="https://api.openai.com/v1"
              class="form-input"
            >
            <span class="form-hint">OpenAI 兼容的 API 地址</span>
          </div>
          
          <!-- Model -->
          <div class="form-item">
            <label>Model</label>
            <div class="input-with-select">
              <input 
                v-model="config.model"
                type="text"
                placeholder="gpt-4o-mini"
                class="form-input"
                list="model-list"
              >
              <datalist id="model-list">
                <option v-for="m in commonModels" :key="m" :value="m" />
              </datalist>
            </div>
            <span class="form-hint">模型名称，可从下拉选择或自定义输入</span>
          </div>
          
          <!-- Actions -->
          <div class="form-actions">
            <button 
              @click="testConnection" 
              :disabled="testing"
              class="btn btn-secondary"
            >
              {{ testing ? '测试中...' : '🔗 测试连接' }}
            </button>
            <button 
              @click="saveConfig" 
              :disabled="saving"
              class="btn btn-primary"
            >
              {{ saving ? '保存中...' : '💾 保存配置' }}
            </button>
          </div>
          
          <!-- Test Result -->
          <div v-if="testResult" class="test-result" :class="testResult.success ? 'success' : 'error'">
            <span v-if="testResult.success">✅ {{ testResult.message }} ({{ testResult.model }})</span>
            <span v-else>❌ 连接失败: {{ testResult.error }}</span>
          </div>
          
          <!-- Save Message -->
          <div v-if="saveMessage" class="save-message">{{ saveMessage }}</div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #f4f4f5;
  margin: 0;
}

.settings-section {
  background: #18181b;
  border: 1px solid #27272a;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.settings-section h2 {
  font-size: 18px;
  font-weight: 600;
  color: #f4f4f5;
  margin: 0 0 8px 0;
}

.section-desc {
  color: #71717a;
  font-size: 14px;
  margin: 0 0 24px 0;
}

.loading {
  color: #71717a;
  padding: 20px 0;
  text-align: center;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item label {
  font-size: 14px;
  font-weight: 500;
  color: #a1a1aa;
}

.form-input {
  padding: 12px 16px;
  background: #09090b;
  border: 1px solid #3f3f46;
  border-radius: 8px;
  color: #f4f4f5;
  font-size: 14px;
  width: 100%;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.form-hint {
  font-size: 12px;
  color: #52525b;
}

.input-with-button {
  display: flex;
  gap: 8px;
}

.input-with-button .form-input {
  flex: 1;
}

.toggle-btn {
  padding: 0 16px;
  background: #27272a;
  border: 1px solid #3f3f46;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
}

.toggle-btn:hover {
  background: #3f3f46;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #3b82f6;
  border: none;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-secondary {
  background: transparent;
  border: 1px solid #3f3f46;
  color: #a1a1aa;
}

.btn-secondary:hover:not(:disabled) {
  background: #27272a;
  color: #f4f4f5;
}

.test-result {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
}

.test-result.success {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #22c55e;
}

.test-result.error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.save-message {
  font-size: 14px;
  color: #22c55e;
}
</style>
