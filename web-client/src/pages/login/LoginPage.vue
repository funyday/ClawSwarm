<template>
  <div class="login-page">
    <div class="login-card">
      <img class="login-card__logo" src="/Logo-2.png" alt="ClawSwarm Logo" />
      <h1 class="login-card__title">{{ t("login.title") }}</h1>
      <p class="login-card__subtitle">{{ t("login.subtitle") }}</p>

      <!-- 本地账号登录 -->
      <el-form
        v-if="loginType === 'local'"
        ref="formRef"
        class="login-form"
        :model="form"
        :rules="rules"
        @submit.prevent="handleLocalLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            :placeholder="t('login.username')"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            :placeholder="t('login.password')"
            size="large"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLocalLogin"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="login-btn"
          :loading="loading"
          @click="handleLocalLogin"
        >
          {{ t("login.submit") }}
        </el-button>
      </el-form>

      <!-- 飞书登录 (仅公网部署可用) -->
      <div v-if="loginType === 'feishu'" class="feishu-section">
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

      <!-- 切换登录方式 -->
      <div class="login-divider">
        <span class="login-divider__text">{{ t("login.or") }}</span>
      </div>

      <div class="login-type-toggle">
        <el-button
          v-if="loginType === 'local'"
          class="toggle-btn"
          @click="loginType = 'feishu'"
        >
          {{ t("login.switchToFeishu") }}
        </el-button>
        <el-button
          v-else
          class="toggle-btn"
          @click="loginType = 'local'"
        >
          {{ t("login.switchToLocal") }}
        </el-button>
      </div>

      <!-- 飞书登录提示 -->
      <p v-if="loginType === 'feishu'" class="login-hint">
        {{ t("feishu.publicOnlyHint") }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useI18n } from "@/composables/useI18n";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const { t } = useI18n();
const authStore = useAuthStore();

const loginType = ref<"local" | "feishu">("local");
const loading = ref(false);
const formRef = ref();

const form = reactive({
    username: "",
    password: "",
});

const rules = {
    username: [{ required: true, message: "", trigger: "blur" }],
    password: [{ required: true, message: "", trigger: "blur" }],
};

async function handleLocalLogin() {
    if (!formRef.value) return;

    try {
        await formRef.value.validate();
    } catch {
        return;
    }

    loading.value = true;
    try {
        await authStore.login(form.username, form.password);
        ElMessage.success(t("login.success"));
        router.push("/messages");
    } catch (error: any) {
        ElMessage.error(error?.message || error?.detail || t("login.failed"));
    } finally {
        loading.value = false;
    }
}

async function handleFeishuLogin() {
    loading.value = true;
    try {
        window.location.href = "/auth/feishu";
    } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : String(error));
        loading.value = false;
    }
}

// 检查是否已登录
onMounted(async () => {
    const isLoggedIn = await authStore.checkAuth();
    if (isLoggedIn) {
        router.push("/messages");
    }
});
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

.login-form {
  margin-bottom: 16px;
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 1rem;
}

.feishu-section {
  margin-bottom: 16px;
}

.feishu-login-btn {
  width: 100%;
  height: 48px;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.feishu-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  margin-right: 8px;
  background: linear-gradient(135deg, #00d4ff 0%, #0072ff 100%);
  color: white;
  border-radius: 6px;
  font-weight: bold;
}

.login-divider {
  display: flex;
  align-items: center;
  margin: 16px 0;
}

.login-divider::before,
.login-divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--color-border);
}

.login-divider__text {
  padding: 0 12px;
  color: var(--color-text-secondary);
  font-size: 0.85rem;
}

.login-type-toggle {
  text-align: center;
}

.toggle-btn {
  width: 100%;
}

.login-hint {
  margin-top: 12px;
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  text-align: center;
}
</style>
