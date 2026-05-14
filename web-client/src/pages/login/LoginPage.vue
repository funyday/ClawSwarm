<template>
  <div class="login-page">
    <div class="login-card">
      <img class="login-card__logo" src="/Logo-2.png" alt="ClawSwarm Logo" />
      <h1 class="login-card__title">{{ t("feishu.loginTitle") }}</h1>
      <p class="login-card__subtitle">{{ t("feishu.loginSubtitle") }}</p>

      <div class="login-card__sso">
        <el-button 
          type="primary" 
          size="large" 
          class="feishu-login-btn"
          :loading="loading"
          @click="handleFeishuLogin"
        >
          <span class="feishu-icon">飞</span>
          {{ t("feishu.loginWithFeishu") }}
        </el-button>
      </div>

      <p class="login-card__agreement">
        {{ t("feishu.loginAgreement") }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { useI18n } from "@/composables/useI18n";

const router = useRouter();
const route = useRoute();
const { t } = useI18n();
const loading = ref(false);

async function handleFeishuLogin() {
    loading.value = true;
    try {
        // 跳转到后端飞书 OAuth 授权页面
        window.location.href = "/auth/feishu";
    } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : String(error));
        loading.value = false;
    }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(8, 145, 178, 0.14), transparent 30%),
    radial-gradient(circle at bottom right, rgba(249, 115, 22, 0.12), transparent 26%),
    #eff2f4;
}

.login-card {
  width: min(100%, 420px);
  padding: 28px;
  border: 1px solid var(--color-border);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.10);
}

.login-card__logo {
  height: 42px;
  width: auto;
  object-fit: contain;
}

.login-card__title {
  margin: 18px 0 8px;
  font-size: 1.6rem;
  line-height: 1.2;
}

.login-card__subtitle {
  margin: 0 0 24px;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.login-card__sso {
  margin-bottom: 20px;
}

.feishu-login-btn {
  width: 100%;
  height: 48px;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, #3370ff 0%, #2860e5 100%);
  border: none;
}

.feishu-login-btn:hover {
  background: linear-gradient(135deg, #2860e5 0%, #2356d5 100%);
}

.feishu-icon {
  width: 24px;
  height: 24px;
  background: white;
  color: #3370ff;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.login-card__agreement {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-align: center;
}
</style>
