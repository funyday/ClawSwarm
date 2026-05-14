/**
 * 统一的 HTTP 客户端。
 *
 * 集中处理 baseURL、超时、凭证和错误消息归一化。
 */
import axios from "axios";
import { resolveApiBaseUrl } from "@/api/baseUrl";

const FEISHU_TOKEN_KEY = "clawswarm_feishu_token";

function getFeishuToken(): string | null {
    if (typeof localStorage === "undefined") return null;
    return localStorage.getItem(FEISHU_TOKEN_KEY);
}

export const apiClient = axios.create({
    baseURL: resolveApiBaseUrl(),
    timeout: 10000,
    withCredentials: true,
});

// 添加 Authorization 头（用于飞书 SSO 登录）
apiClient.interceptors.request.use((config) => {
    const token = getFeishuToken();
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        const message = error?.response?.data?.message;
        const detail = error?.response?.data?.detail;
        const fallbackMessage = error?.message;

        if (typeof message === "string" && message.trim()) {
            return Promise.reject(new Error(message));
        }
        if (typeof detail === "string" && detail.trim()) {
            return Promise.reject(new Error(detail));
        }
        if (typeof fallbackMessage === "string" && fallbackMessage.trim()) {
            return Promise.reject(new Error(fallbackMessage));
        }
        return Promise.reject(new Error("Request failed"));
    },
);
