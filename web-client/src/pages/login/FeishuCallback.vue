<template>
  <div class="callback-container">
    <div class="callback-content">
      <h2>正在处理登录...</h2>
      <p>{{ statusMessage }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const statusMessage = ref('正在验证飞书授权...')

onMounted(async () => {
  try {
    // 从 URL 获取 code 和 state
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
    const state = urlParams.get('state')
    const error = urlParams.get('error')

    if (error) {
      statusMessage.value = `授权失败: ${error}`
      setTimeout(() => router.push('/login'), 2000)
      return
    }

    if (!code || !state) {
      statusMessage.value = '缺少授权参数'
      setTimeout(() => router.push('/login'), 2000)
      return
    }

    statusMessage.value = '正在完成登录...'

    // 调用后端完成登录
    const response = await fetch('/auth/feishu/callback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ code, state })
    })

    const data = await response.json()

    if (data.success && data.user) {
      // 保存用户信息到 store (直接设置 state)
      authStore.$patch({ user: data.user, initialized: true })
      statusMessage.value = '登录成功，正在跳转...'
      
      // 延迟跳转，让用户看到成功消息
      setTimeout(() => {
        router.push(data.redirect_url || '/')
      }, 500)
    } else {
      statusMessage.value = data.message || '登录失败'
      setTimeout(() => router.push('/login'), 2000)
    }
  } catch (error) {
    console.error('登录处理失败:', error)
    statusMessage.value = '登录处理失败，请重试'
    setTimeout(() => router.push('/login'), 2000)
  }
})
</script>

<style scoped>
.callback-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: var(--el-bg-color-page);
}

.callback-content {
  text-align: center;
  padding: 40px;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.callback-content h2 {
  margin-bottom: 16px;
  color: var(--el-text-color-primary);
}

.callback-content p {
  color: var(--el-text-color-secondary);
}
</style>
