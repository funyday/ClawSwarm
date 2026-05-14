<template>
    <div class="feishu-integration-page">
        <!-- 页面标题 -->
        <div class="page-header">
            <div class="header-left">
                <h2>{{ t('feishu.title') }}</h2>
                <span class="subtitle">{{ t('feishu.description') }}</span>
            </div>
            <div class="header-right">
                <ElButton :icon="RefreshRight" circle @click="handleRefresh" />
            </div>
        </div>

        <!-- 统计卡片 -->
        <div class="stats-row">
            <ElCard class="stat-card">
                <div class="stat-content">
                    <div class="stat-icon bot-icon">
                        <User />
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ stats.botCount }}</div>
                        <div class="stat-label">{{ t('feishu.overview.totalBots') }}</div>
                    </div>
                </div>
            </ElCard>

            <ElCard class="stat-card">
                <div class="stat-content">
                    <div class="stat-icon online-icon">
                        <ChatDotRound />
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ stats.onlineBots }}</div>
                        <div class="stat-label">{{ t('feishu.overview.onlineBots') }}</div>
                    </div>
                </div>
            </ElCard>

            <ElCard class="stat-card">
                <div class="stat-content">
                    <div class="stat-icon group-icon">
                        <UserFilled />
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ stats.groupCount }}</div>
                        <div class="stat-label">{{ t('feishu.overview.totalGroups') }}</div>
                    </div>
                </div>
            </ElCard>

            <ElCard class="stat-card">
                <div class="stat-content">
                    <div class="stat-icon message-icon">
                        <ChatDotRound />
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ stats.todayMessages }}</div>
                        <div class="stat-label">{{ t('feishu.overview.todayMessages') }}</div>
                    </div>
                </div>
            </ElCard>
        </div>

        <!-- Tab 页签 -->
        <ElCard class="main-content">
            <ElTabs v-model:activeTab="activeTab">
                <ElTabPane :label="t('feishu.tabs.bots')" name="bots">
                    <BotManagementPane @refresh="handleRefresh" />
                </ElTabPane>

                <ElTabPane :label="t('feishu.tabs.groups')" name="groups">
                    <GroupManagementPane @refresh="handleRefresh" />
                </ElTabPane>

                <ElTabPane :label="t('feishu.tabs.sso')" name="sso">
                    <FeishuSSOPane />
                </ElTabPane>
            </ElTabs>
        </ElCard>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { User, ChatDotRound, UserFilled, RefreshRight } from '@element-plus/icons-vue';
import { useI18n } from '@/composables/useI18n';
import { apiClient } from '@/api/client';
import BotManagementPane from './components/BotManagementPane.vue';
import GroupManagementPane from './components/GroupManagementPane.vue';
import FeishuSSOPane from './components/FeishuSSOPane.vue';

const { t } = useI18n();

const activeTab = ref('bots');

interface Stats {
    botCount: number;
    onlineBots: number;
    groupCount: number;
    todayMessages: number;
}

const stats = reactive<Stats>({
    botCount: 0,
    onlineBots: 0,
    groupCount: 0,
    todayMessages: 0,
});

const fetchStats = async () => {
    try {
        const [botsRes, groupsRes] = await Promise.all([
            apiClient.get('/feishu/bots').catch(() => ({ data: [] })),
            apiClient.get('/feishu/groups').catch(() => ({ data: [] })),
        ]);
        
        const bots = botsRes.data || [];
        stats.botCount = bots.length;
        stats.onlineBots = bots.filter((b: any) => b.status === 'active').length;
        stats.groupCount = (groupsRes.data || []).length;
        stats.todayMessages = 0;
    } catch (error) {
        console.error('Failed to fetch stats:', error);
    }
};

const handleRefresh = () => {
    fetchStats();
    ElMessage.success(t('common.saved'));
};

onMounted(() => {
    fetchStats();
});
</script>

<style scoped>
.fewishu-integration-page {
    padding: 24px;
}

.page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
}

.header-left h2 {
    margin: 0 0 8px 0;
    font-size: 24px;
    font-weight: 600;
}

.subtitle {
    color: #909399;
    font-size: 14px;
}

.stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}

.stat-card {
    --el-card-padding: 16px;
}

.stat-content {
    display: flex;
    align-items: center;
    gap: 16px;
}

.stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
}

.bot-icon {
    background: #e6f7ff;
    color: #1890ff;
}

.online-icon {
    background: #f6ffed;
    color: #52c41a;
}

.group-icon {
    background: #fff7e6;
    color: #fa8c16;
}

.message-icon {
    background: #f9f0ff;
    color: #722ed1;
}

.stat-info {
    flex: 1;
}

.stat-value {
    font-size: 24px;
    font-weight: 600;
    color: #303133;
}

.stat-label {
    font-size: 14px;
    color: #909399;
    margin-top: 4px;
}

.main-content {
    --el-card-padding: 16px;
}
</style>
