<template>
    <div class="feishu-sso-pane">
        <!-- Status Card -->
        <ElCard class="status-card">
            <div class="status-content">
                <div class="status-item">
                    <span class="status-label">{{ t('feishu.connectionStatus') }}:</span>
                    <ElTag :type="ssoConfig?.enabled ? 'success' : 'info'" size="small">
                        {{ ssoConfig?.enabled ? t('feishu.enabled') : t('feishu.disabled') }}
                    </ElTag>
                </div>
                <div class="status-item">
                    <span class="status-label">{{ t('feishu.todayLogins') }}:</span>
                    <span class="status-value">{{ stats?.today_logins ?? 0 }}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">{{ t('feishu.totalUsers') }}:</span>
                    <span class="status-value">{{ stats?.total_users ?? 0 }}</span>
                </div>
            </div>
        </ElCard>

        <!-- SSO Config Form -->
        <ElCard>
            <template #header>
                <div class="card-header">
                    <span>{{ t('feishu.ssoSettings') }}</span>
                    <ElSwitch v-model="formData.enabled" @change="(val: any) => formData.enabled = val" />
                </div>
            </template>

            <ElForm :model="formData" label-width="140px" :disabled="!formData.enabled">
                <ElDivider content-position="left">{{ t('feishu.basicConfig') }}</ElDivider>

                <ElFormItem :label="t('feishu.appId')" required>
                    <ElInput
                        v-model="formData.app_id"
                        :placeholder="t('feishu.appIdPlaceholder')"
                    />
                </ElFormItem>

                <ElFormItem :label="t('feishu.appSecret')" required>
                    <ElInput
                        v-model="formData.app_secret"
                        type="password"
                        :placeholder="formData.app_secret ? t('feishu.appSecretUpdated') : t('feishu.appSecretPlaceholder')"
                        show-password
                    />
                </ElFormItem>

                <ElFormItem :label="t('feishu.redirectUri')">
                    <ElInput v-model="formData.redirect_uri" readonly>
                        <template #append>
                            <ElButton @click="copyRedirectUri">
                                {{ t('feishu.copy') }}
                            </ElButton>
                        </template>
                    </ElInput>
                    <div class="form-tip">{{ t('feishu.redirectUriTip') }}</div>
                </ElFormItem>

                <ElDivider content-position="left">{{ t('feishu.accessControl') }}</ElDivider>

                <ElFormItem :label="t('feishu.autoCreateUser')">
                    <ElSwitch v-model="formData.auto_create_user" />
                    <div class="form-tip">{{ t('feishu.autoCreateUserTip') }}</div>
                </ElFormItem>

                <ElFormItem :label="t('feishu.allowedEmails')">
                    <ElInput
                        v-model="formData.allowed_emails"
                        :placeholder="t('feishu.allowedEmailsPlaceholder')"
                    />
                    <div class="form-tip">{{ t('feishu.allowedEmailsTip') }}</div>
                </ElFormItem>

                <ElDivider content-position="left">{{ t('feishu.operation') }}</ElDivider>

                <ElFormItem>
                    <ElButton type="primary" :loading="saving" @click="handleSave">
                        {{ t('feishu.saveConfig') }}
                    </ElButton>
                    <ElButton :loading="testing" @click="handleTest">
                        {{ t('feishu.testConnection') }}
                    </ElButton>
                </ElFormItem>
            </ElForm>
        </ElCard>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import axios from 'axios';
import { resolveApiBaseUrl } from '@/api/baseUrl';

const { t } = useI18n();

const apiBase = computed(() => resolveApiBaseUrl());

interface SSOConfig {
    id: number;
    app_id: string;
    app_secret: string;
    redirect_uri: string;
    enabled: boolean;
    auto_create_user: boolean;
    allowed_departments: string | null;
    allowed_emails: string | null;
    created_at: string;
    updated_at: string;
}

interface SSOStats {
    today_logins: number;
    total_users: number;
}

const ssoConfig = ref<SSOConfig | null>(null);
const stats = ref<SSOStats | null>(null);
const saving = ref(false);
const testing = ref(false);

const formData = reactive({
    app_id: '',
    app_secret: '',
    redirect_uri: '',
    enabled: false,
    auto_create_user: true,
    allowed_departments: '',
    allowed_emails: '',
});

const loadConfig = async () => {
    try {
        const response = await axios.get(`${apiBase.value}/admin/auth/config`);
        ssoConfig.value = response.data;
        
        formData.app_id = response.data.app_id || '';
        formData.app_secret = response.data.app_secret || '';
        formData.enabled = response.data.enabled || false;
        formData.auto_create_user = response.data.auto_create_user ?? true;
        formData.allowed_departments = response.data.allowed_departments || '';
        formData.allowed_emails = response.data.allowed_emails || '';
        
        // 生成默认回调地址
        const baseUrl = window.location.origin;
        formData.redirect_uri = `${baseUrl}/auth/feishu/callback`;
    } catch (error) {
        console.error('Failed to load SSO config:', error);
    }
};

const loadStats = async () => {
    try {
        const response = await axios.get(`${apiBase.value}/admin/auth/stats`);
        stats.value = response.data;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
};

const handleEnabledChange = (value: boolean) => {
    formData.enabled = value;
};

const copyRedirectUri = async () => {
    try {
        await navigator.clipboard.writeText(formData.redirect_uri);
        ElMessage.success(t('feishu.redirectUriCopied'));
    } catch (error) {
        ElMessage.error('Copy failed');
    }
};

const handleSave = async () => {
    saving.value = true;
    try {
        const payload = {
            app_id: formData.app_id,
            app_secret: formData.app_secret,
            enabled: formData.enabled,
            auto_create_user: formData.auto_create_user,
            allowed_departments: formData.allowed_departments || null,
            allowed_emails: formData.allowed_emails || null,
            redirect_uri: formData.redirect_uri,
        };
        
        await axios.put(`${apiBase.value}/admin/auth/config`, payload);
        ElMessage.success(t('feishu.saved'));
        await loadConfig();
    } catch (error: any) {
        ElMessage.error(error.response?.data?.message || t('feishu.saveFailed'));
    } finally {
        saving.value = false;
    }
};

const handleTest = async () => {
    testing.value = true;
    try {
        const payload = {
            app_id: formData.app_id,
            app_secret: formData.app_secret,
        };
        
        await axios.post(`${apiBase.value}/admin/auth/config/test`, payload);
        ElMessage.success(t('feishu.testSuccess'));
    } catch (error: any) {
        ElMessage.error(error.response?.data?.message || t('feishu.testFailed'));
    } finally {
        testing.value = false;
    }
};

onMounted(() => {
    loadConfig();
    loadStats();
});
</script>

<style scoped>
.fewishu-sso-pane {
    padding: 16px 0;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.status-card {
    margin-bottom: 24px;
    background: #f5f7fa;
    border: none;
}

.status-content {
    display: flex;
    gap: 48px;
    flex-wrap: wrap;
}

.status-item {
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-label {
    color: #606266;
    font-size: 14px;
}

.status-value {
    font-weight: 500;
    color: #303133;
}

.form-tip {
    color: #909399;
    font-size: 12px;
    margin-top: 4px;
}
</style>
