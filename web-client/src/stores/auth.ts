import { defineStore } from "pinia";

import { fetchCurrentUser, login as loginRequest, logout as logoutRequest, updateProfile as updateProfileRequest } from "@/api/auth";
import type { AuthUserOutput, LoginInput, UpdateProfileInput } from "@/types/view/auth";

type AuthState = {
    user: AuthUserOutput | null;
    initialized: boolean;
    loadingMe: Promise<AuthUserOutput | null> | null;
    feishuToken: string | null;
};

const FEISHU_TOKEN_KEY = "clawswarm_feishu_token";

export const useAuthStore = defineStore("auth", {
    state: (): AuthState => ({
        user: null,
        initialized: false,
        loadingMe: null,
        feishuToken: localStorage.getItem(FEISHU_TOKEN_KEY),
    }),
    getters: {
        isAuthenticated: (state) => !!state.user,
    },
    actions: {
        async ensureLoaded() {
            if (this.initialized) {
                return this.user;
            }
            if (this.loadingMe) {
                return this.loadingMe;
            }
            this.loadingMe = (async () => {
                try {
                    // 检查 URL 中是否有飞书登录 token
                    this.checkFeishuLoginToken();
                    
                    console.log("[Auth] feishuToken after check:", this.feishuToken);
                    
                    // 如果有保存的飞书 token，先尝试用它获取用户信息
                    if (this.feishuToken) {
                        try {
                            console.log("[Auth] Fetching user with token...");
                            this.user = await fetchCurrentUser();
                            console.log("[Auth] User fetched:", this.user);
                            this.initialized = true;
                            this.loadingMe = null;
                            return this.user;
                        } catch (e) {
                            console.error("[Auth] Failed to fetch user with token:", e);
                            this.user = null;
                        }
                    }
                    
                    // 如果还没获取到用户信息，尝试常规方式
                    if (!this.user) {
                        try {
                            console.log("[Auth] Trying regular fetch...");
                            this.user = await fetchCurrentUser();
                            console.log("[Auth] Regular fetch success:", this.user);
                        } catch (e) {
                            console.error("[Auth] Regular fetch failed:", e);
                            this.user = null;
                        }
                    }
                } catch (e) {
                    console.error("[Auth] ensureLoaded error:", e);
                    this.user = null;
                } finally {
                    this.initialized = true;
                    this.loadingMe = null;
                }
                return this.user;
            })();
            return this.loadingMe;
        },
        // 检查 URL 中的飞书登录 token
        checkFeishuLoginToken() {
            if (typeof window === "undefined") return;
            
            const urlParams = new URLSearchParams(window.location.search);
            const loginToken = urlParams.get("login_token");
            
            if (loginToken) {
                // 保存 token 到 localStorage
                localStorage.setItem(FEISHU_TOKEN_KEY, loginToken);
                this.feishuToken = loginToken;
                
                // 清除 URL 中的 token 参数
                const cleanUrl = window.location.origin + window.location.pathname;
                window.history.replaceState({}, "", cleanUrl);
            }
        },
        // 获取飞书 token 用于 API 请求
        getFeishuToken(): string | null {
            return this.feishuToken || localStorage.getItem(FEISHU_TOKEN_KEY);
        },
        async login(payload: LoginInput) {
            const user = await loginRequest(payload);
            this.user = user;
            this.initialized = true;
            return user;
        },
        async logout() {
            await logoutRequest();
            this.user = null;
            this.feishuToken = null;
            localStorage.removeItem(FEISHU_TOKEN_KEY);
            this.initialized = true;
        },
        async updateProfile(payload: UpdateProfileInput) {
            const user = await updateProfileRequest(payload);
            this.user = user;
            this.initialized = true;
            return user;
        },
        // 飞书 SSO 登录后设置用户
        setUser(user: AuthUserOutput) {
            this.user = user;
            this.initialized = true;
        },
    },
});
