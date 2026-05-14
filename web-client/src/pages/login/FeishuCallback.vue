<template>
  <div class="callback-page">
    <div class="callback-card">
      <el-icon class="loading-icon" size="32"><Loading /></el-icon>
      <p>{{ t("feishu.processingLogin") }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { Loading } from "@element-plus/icons-vue";
import { useI18n } from "@/composables/useI18n";

const router = useRouter();
const { t } = useI18n();

onMounted(async () => {
  try {
    // 从 URL 获取查询参数
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get("code");
    const state = urlParams.get("state");

    if (!code) {
      ElMessage.error(t("feishu.callbackError"));
      router.push("/login");
      return;
    }

    // 调用后端回调接口
    const response = await fetch(`/auth/feishu/callback?code=${code}&state=${state}`, {
      method: "GET",
      credentials: "include",
    });

    if (response.ok) {
      const data = await response.json();
      // 保存用户信息到 localStorage
      if (data.user) {
        localStorage.setItem("clawswarm_user", JSON.stringify(data.user));
      }
      // 跳转到首页
      router.push("/");
    } else {
      const error = await response.json().catch(() => ({ detail: "Login failed" }));
      ElMessage.error(error.detail || t("feishu.callbackError"));
      router.push("/login");
    }
  } catch (error) {
    console.error("OAuth callback error:", error);
    ElMessage.error(t("feishu.callbackError"));
    router.push("/login");
  }
});
</script>

<style scoped>
.callback-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f8f4f4;
}

.callback-card {
  text-align: center;
  padding: 40px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.loading-icon {
  animation: rotate 1s linear infinite;
  color: #409eff;
  margin-bottom: 16px;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
