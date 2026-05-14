<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import {
    ElButton,
    ElTable,
    ElTableColumn,
    ElTag,
    ElDialog,
    ElForm,
    ElFormItem,
    ElInput,
    ElSelect,
    ElOption,
    ElPopconfirm,
    ElMessage,
    ElMessageBox,
} from "element-plus";
import { Plus } from "@element-plus/icons-vue";
import { apiClient } from "../../../api/client";

interface Bot {
    id: number;
    name: string;
    app_id: string;
    instance_id: number;
    instance_name?: string;
    agent_id?: number;
    agent_name?: string;
    status: string;
}

interface Instance {
    id: number;
    name: string;
}

interface Agent {
    id: number;
    name: string;
}

const { t } = useI18n();
const loading = ref(false);
const bots = ref<Bot[]>([]);
const instances = ref<Instance[]>([]);
const agents = ref<Agent[]>([]);

const dialogVisible = ref(false);
const dialogTitle = ref("");
const formData = ref({
    id: 0,
    name: "",
    app_id: "",
    app_secret: "",
    webhook_secret: "",
    instance_id: 0,
    agent_id: undefined as number | undefined,
});
const formLoading = ref(false);

const fetchBots = async () => {
    loading.value = true;
    try {
        const response = await apiClient.get("/feishu/bots");
        bots.value = response.data || [];
    } catch (error) {
        console.error("Failed to fetch bots:", error);
        ElMessage.error(t("feishu.fetchBotsFailed"));
    } finally {
        loading.value = false;
    }
};

const fetchInstances = async () => {
    try {
        const response = await apiClient.get("/instances");
        instances.value = response.data || [];
    } catch (error) {
        console.error("Failed to fetch instances:", error);
    }
};

const fetchAgents = async (instanceId?: number) => {
    try {
        if (!instanceId) {
            agents.value = [];
            return;
        }
        const response = await apiClient.get(`/instances/${instanceId}/agents`);
        agents.value = response.data || [];
    } catch (error) {
        console.error("Failed to fetch agents:", error);
    }
};

const openCreateDialog = async () => {
    dialogTitle.value = t("feishu.createBot");
    formData.value = {
        id: 0,
        name: "",
        app_id: "",
        app_secret: "",
        webhook_secret: "",
        instance_id: 0,
        agent_id: undefined,
    };
    dialogVisible.value = true;
    await fetchAgents();
};

const openEditDialog = async (row: Bot) => {
    dialogTitle.value = t("feishu.editBot");
    formData.value = {
        id: row.id,
        name: row.name,
        app_id: row.app_id,
        app_secret: "",
        webhook_secret: "",
        instance_id: row.instance_id,
        agent_id: row.agent_id,
    };
    dialogVisible.value = true;
    await fetchAgents(row.instance_id);
};

const handleSubmit = async () => {
    if (!formData.value.name || !formData.value.app_id || !formData.value.instance_id) {
        ElMessage.warning(t("feishu.fillRequiredFields"));
        return;
    }

    formLoading.value = true;
    try {
        if (formData.value.id) {
            await apiClient.put(`/feishu/bots/${formData.value.id}`, formData.value);
            ElMessage.success(t("feishu.updateSuccess"));
        } else {
            await apiClient.post("/feishu/bots", formData.value);
            ElMessage.success(t("feishu.createSuccess"));
        }
        dialogVisible.value = false;
        await fetchBots();
    } catch (error: any) {
        ElMessage.error(error.message || t("feishu.saveFailed"));
    } finally {
        formLoading.value = false;
    }
};

const handleDelete = async (row: Bot) => {
    try {
        await apiClient.delete(`/feishu/bots/${row.id}`);
        ElMessage.success(t("feishu.deleteSuccess"));
        await fetchBots();
    } catch (error: any) {
        ElMessage.error(error.message || t("feishu.deleteFailed"));
    }
};

const handleTest = async (row: Bot) => {
    try {
        await apiClient.post(`/feishu/bots/${row.id}/test`);
        ElMessage.success(t("feishu.testSuccess"));
    } catch (error: any) {
        ElMessage.error(error.message || t("feishu.testFailed"));
    }
};

const onInstanceChange = async (instanceId: number) => {
    formData.value.instance_id = instanceId;
    formData.value.agent_id = undefined;
    await fetchAgents(instanceId);
};

fetchBots();
fetchInstances();
</script>

<template>
    <div class="bot-management-pane">
        <div class="toolbar">
            <ElButton type="primary" :icon="Plus" @click="openCreateDialog">
                {{ t("feishu.createBot") }}
            </ElButton>
        </div>

        <ElTable :data="bots" v-loading="loading" stripe>
            <ElTableColumn prop="name" :label="t('feishu.botName')" min-width="150">
                <template #default="{ row }">
                    <div class="bot-name-cell">
                        <span class="bot-name">{{ row.name }}</span>
                    </div>
                </template>
            </ElTableColumn>

            <ElTableColumn prop="app_id" :label="t('feishu.appId')" min-width="180">
                <template #default="{ row }">
                    <code class="app-id">{{ row.app_id }}</code>
                </template>
            </ElTableColumn>

            <ElTableColumn prop="instance_name" :label="t('feishu.instance')" min-width="120">
                <template #default="{ row }">
                    <ElTag type="info">{{ row.instance_name || row.instance_id }}</ElTag>
                </template>
            </ElTableColumn>

            <ElTableColumn prop="agent_name" :label="t('feishu.bindAgent')" min-width="120">
                <template #default="{ row }">
                    <ElTag v-if="row.agent_name" type="success">{{ row.agent_name }}</ElTag>
                    <span v-else class="text-muted">{{ t("feishu.mainAgent") }}</span>
                </template>
            </ElTableColumn>

            <ElTableColumn prop="status" :label="t('feishu.status')" width="100">
                <template #default="{ row }">
                    <ElTag :type="row.status === 'active' ? 'success' : 'danger'">
                        {{ row.status === 'active' ? t("feishu.online") : t("feishu.offline") }}
                    </ElTag>
                </template>
            </ElTableColumn>

            <ElTableColumn :label="t('feishu.actions')" width="200" fixed="right">
                <template #default="{ row }">
                    <ElButton link type="primary" @click="handleTest(row)">
                        {{ t("feishu.test") }}
                    </ElButton>
                    <ElButton link type="primary" @click="openEditDialog(row)">
                        {{ t("common.edit") }}
                    </ElButton>
                    <ElPopconfirm
                        :title="t('feishu.deleteConfirm')"
                        @confirm="handleDelete(row)"
                    >
                        <template #reference>
                            <ElButton link type="danger">
                                {{ t("common.delete") }}
                            </ElButton>
                        </template>
                    </ElPopconfirm>
                </template>
            </ElTableColumn>
        </ElTable>

        <ElDialog
            v-model="dialogVisible"
            :title="dialogTitle"
            width="500px"
            :close-on-click-modal="false"
        >
            <ElForm :model="formData" label-width="120px">
                <ElFormItem :label="t('feishu.botName')" required>
                    <ElInput v-model="formData.name" :placeholder="t('feishu.botNamePlaceholder')" />
                </ElFormItem>

                <ElFormItem :label="t('feishu.appId')" required>
                    <ElInput v-model="formData.app_id" :placeholder="t('feishu.appIdPlaceholder')" />
                </ElFormItem>

                <ElFormItem :label="t('feishu.appSecret')" :required="!formData.id">
                    <ElInput
                        v-model="formData.app_secret"
                        type="password"
                        :placeholder="formData.id ? t('feishu.appSecretUpdateTip') : t('feishu.appSecretPlaceholder')"
                        show-password
                    />
                </ElFormItem>

                <ElFormItem :label="t('feishu.webhookSecret')" :required="!formData.id">
                    <ElInput
                        v-model="formData.webhook_secret"
                        :placeholder="formData.id ? t('feishu.webhookSecretUpdateTip') : t('feishu.webhookSecretPlaceholder')"
                    />
                </ElFormItem>

                <ElFormItem :label="t('feishu.instance')" required>
                    <ElSelect
                        v-model="formData.instance_id"
                        :placeholder="t('feishu.selectInstance')"
                        @change="onInstanceChange"
                    >
                        <ElOption
                            v-for="inst in instances"
                            :key="inst.id"
                            :label="inst.name"
                            :value="inst.id"
                        />
                    </ElSelect>
                </ElFormItem>

                <ElFormItem :label="t('feishu.bindAgent')">
                    <ElSelect
                        v-model="formData.agent_id"
                        :placeholder="t('feishu.selectAgent')"
                        clearable
                    >
                        <ElOption
                            v-for="agent in agents"
                            :key="agent.id"
                            :label="agent.name"
                            :value="agent.id"
                        />
                    </ElSelect>
                </ElFormItem>
            </ElForm>

            <template #footer>
                <ElButton @click="dialogVisible = false">{{ t("common.cancel") }}</ElButton>
                <ElButton type="primary" :loading="formLoading" @click="handleSubmit">
                    {{ t("common.confirm") }}
                </ElButton>
            </template>
        </ElDialog>
    </div>
</template>

<style scoped>
.bot-management-pane {
    padding: 16px 0;
}

.toolbar {
    margin-bottom: 16px;
}

.bot-name-cell {
    display: flex;
    align-items: center;
    gap: 8px;
}

.bot-name {
    font-weight: 500;
}

.app-id {
    font-size: 12px;
    color: #666;
}

.text-muted {
    color: #999;
    font-size: 13px;
}
</style>
