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
    ElCheckboxGroup,
    ElCheckbox,
    ElMessage,
} from "element-plus";
import { apiClient } from "../../../api/client";

interface Group {
    id: number;
    feishu_chat_id: string;
    name?: string;
    bound_group_id?: number;
    bound_group_name?: string;
    message_mode: string;
    bots?: Bot[];
    status: string;
}

interface Bot {
    id: number;
    name: string;
}

interface ClawSwarmGroup {
    id: number;
    name: string;
}

const { t } = useI18n();
const loading = ref(false);
const groups = ref<Group[]>([]);
const clawSwarmGroups = ref<ClawSwarmGroup[]>([]);
const availableBots = ref<Bot[]>([]);

const dialogVisible = ref(false);
const dialogTitle = ref("");
const formData = ref({
    id: 0,
    feishu_chat_id: "",
    name: "",
    bound_group_id: undefined as number | undefined,
    message_mode: "at_mode",
    round_robin_timeout: 30,
    bot_ids: [] as number[],
});
const formLoading = ref(false);

const fetchGroups = async () => {
    loading.value = true;
    try {
        const response = await apiClient.get("/feishu/groups");
        groups.value = response.data || [];
    } catch (error) {
        console.error("Failed to fetch groups:", error);
        ElMessage.error(t("feishu.fetchGroupsFailed"));
    } finally {
        loading.value = false;
    }
};

const fetchClawSwarmGroups = async () => {
    try {
        const response = await apiClient.get("/chat-groups");
        clawSwarmGroups.value = response.data || [];
    } catch (error) {
        console.error("Failed to fetch ClawSwarm groups:", error);
    }
};

const fetchAvailableBots = async () => {
    try {
        const response = await apiClient.get("/feishu/bots");
        availableBots.value = response.data || [];
    } catch (error) {
        console.error("Failed to fetch bots:", error);
    }
};

const openCreateDialog = async () => {
    dialogTitle.value = t("feishu.createGroup");
    formData.value = {
        id: 0,
        feishu_chat_id: "",
        name: "",
        bound_group_id: undefined,
        message_mode: "at_mode",
        round_robin_timeout: 30,
        bot_ids: [],
    };
    dialogVisible.value = true;
    await Promise.all([fetchClawSwarmGroups(), fetchAvailableBots()]);
};

const openEditDialog = async (row: Group) => {
    dialogTitle.value = t("feishu.editGroup");
    formData.value = {
        id: row.id,
        feishu_chat_id: row.feishu_chat_id,
        name: row.name || "",
        bound_group_id: row.bound_group_id,
        message_mode: row.message_mode,
        round_robin_timeout: 30,
        bot_ids: row.bots?.map((b) => b.id) || [],
    };
    dialogVisible.value = true;
    await Promise.all([fetchClawSwarmGroups(), fetchAvailableBots()]);
};

const handleSubmit = async () => {
    if (!formData.value.feishu_chat_id) {
        ElMessage.warning(t("feishu.fillRequiredFields"));
        return;
    }

    formLoading.value = true;
    try {
        if (formData.value.id) {
            await apiClient.put(`/feishu/groups/${formData.value.id}`, formData.value);
            ElMessage.success(t("feishu.updateSuccess"));
        } else {
            await apiClient.post("/feishu/groups", formData.value);
            ElMessage.success(t("feishu.createSuccess"));
        }
        dialogVisible.value = false;
        await fetchGroups();
    } catch (error: any) {
        ElMessage.error(error.message || t("feishu.saveFailed"));
    } finally {
        formLoading.value = false;
    }
};

const handleDelete = async (row: Group) => {
    try {
        await apiClient.delete(`/feishu/groups/${row.id}`);
        ElMessage.success(t("feishu.deleteSuccess"));
        await fetchGroups();
    } catch (error: any) {
        ElMessage.error(error.message || t("feishu.deleteFailed"));
    }
};

const handleAddBot = async (group: Group, bot: Bot) => {
    try {
        await apiClient.post(`/feishu/groups/${group.id}/bots`, {
            bot_id: bot.id,
            enabled: true,
        });
        ElMessage.success(t("feishu.addBotSuccess"));
        await fetchGroups();
    } catch (error: any) {
        ElMessage.error(error.message || t("feishu.addBotFailed"));
    }
};

const handleRemoveBot = async (group: Group, botId: number) => {
    try {
        await apiClient.delete(`/feishu/groups/${group.id}/bots/${botId}`);
        ElMessage.success(t("feishu.removeBotSuccess"));
        await fetchGroups();
    } catch (error: any) {
        ElMessage.error(error.message || t("feishu.removeBotFailed"));
    }
};

const getMessageModeText = (mode: string) => {
    const modes: Record<string, string> = {
        at_mode: t("feishu.atMode"),
        broadcast: t("feishu.broadcastMode"),
        round_robin: t("feishu.roundRobinMode"),
    };
    return modes[mode] || mode;
};

fetchGroups();
</script>

<template>
    <div class="group-management-pane">
        <div class="toolbar">
            <ElButton type="primary" @click="openCreateDialog">
                {{ t("feishu.createGroup") }}
            </ElButton>
        </div>

        <ElTable :data="groups" v-loading="loading" stripe>
            <ElTableColumn prop="name" :label="t('feishu.groupName')" min-width="150">
                <template #default="{ row }">
                    <span class="group-name">{{ row.name || row.feishu_chat_id }}</span>
                </template>
            </ElTableColumn>

            <ElTableColumn prop="feishu_chat_id" :label="t('feishu.feishuChatId')" min-width="180">
                <template #default="{ row }">
                    <code class="chat-id">{{ row.feishu_chat_id }}</code>
                </template>
            </ElTableColumn>

            <ElTableColumn prop="bound_group_name" :label="t('feishu.bindGroup')" min-width="150">
                <template #default="{ row }">
                    <ElTag v-if="row.bound_group_name" type="success">
                        {{ row.bound_group_name }}
                    </ElTag>
                    <span v-else class="text-muted">{{ t("feishu.notBound") }}</span>
                </template>
            </ElTableColumn>

            <ElTableColumn prop="message_mode" :label="t('feishu.messageMode')" width="150">
                <template #default="{ row }">
                    <ElTag :type="row.message_mode === 'at_mode' ? 'primary' : 'warning'">
                        {{ getMessageModeText(row.message_mode) }}
                    </ElTag>
                </template>
            </ElTableColumn>

            <ElTableColumn :label="t('feishu.bindedBots')" min-width="200">
                <template #default="{ row }">
                    <div class="bots-tags">
                        <ElTag
                            v-for="bot in row.bots"
                            :key="bot.id"
                            size="small"
                            closable
                            @close="handleRemoveBot(row, bot.id)"
                        >
                            {{ bot.name }}
                        </ElTag>
                        <span v-if="!row.bots?.length" class="text-muted">
                            {{ t("feishu.noBots") }}
                        </span>
                    </div>
                </template>
            </ElTableColumn>

            <ElTableColumn :label="t('feishu.actions')" width="150" fixed="right">
                <template #default="{ row }">
                    <ElButton link type="primary" @click="openEditDialog(row)">
                        {{ t("common.edit") }}
                    </ElButton>
                    <ElButton link type="danger" @click="handleDelete(row)">
                        {{ t("common.delete") }}
                    </ElButton>
                </template>
            </ElTableColumn>
        </ElTable>

        <ElDialog
            v-model="dialogVisible"
            :title="dialogTitle"
            width="600px"
            :close-on-click-modal="false"
        >
            <ElForm :model="formData" label-width="130px">
                <ElFormItem :label="t('feishu.feishuChatId')" required>
                    <ElInput
                        v-model="formData.feishu_chat_id"
                        :placeholder="t('feishu.feishuChatIdPlaceholder')"
                    />
                </ElFormItem>

                <ElFormItem :label="t('feishu.groupName')">
                    <ElInput
                        v-model="formData.name"
                        :placeholder="t('feishu.groupNamePlaceholder')"
                    />
                </ElFormItem>

                <ElFormItem :label="t('feishu.bindGroup')">
                    <ElSelect
                        v-model="formData.bound_group_id"
                        :placeholder="t('feishu.selectBindGroup')"
                        clearable
                    >
                        <ElOption
                            v-for="group in clawSwarmGroups"
                            :key="group.id"
                            :label="group.name"
                            :value="group.id"
                        />
                    </ElSelect>
                </ElFormItem>

                <ElFormItem :label="t('feishu.messageMode')">
                    <ElSelect v-model="formData.message_mode">
                        <ElOption :label="t('feishu.atMode')" value="at_mode" />
                        <ElOption :label="t('feishu.broadcastMode')" value="broadcast" />
                        <ElOption :label="t('feishu.roundRobinMode')" value="round_robin" />
                    </ElSelect>
                </ElFormItem>

                <ElFormItem :label="t('feishu.bindBots')">
                    <ElCheckboxGroup v-model="formData.bot_ids">
                        <ElCheckbox
                            v-for="bot in availableBots"
                            :key="bot.id"
                            :value="bot.id"
                        >
                            {{ bot.name }}
                        </ElCheckbox>
                    </ElCheckboxGroup>
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
.group-management-pane {
    padding: 16px 0;
}

.toolbar {
    margin-bottom: 16px;
}

.group-name {
    font-weight: 500;
}

.chat-id {
    font-size: 12px;
    color: #666;
}

.bots-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}

.text-muted {
    color: #999;
    font-size: 13px;
}
</style>
