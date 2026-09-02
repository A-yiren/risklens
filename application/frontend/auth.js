/**
 * 金睛 RiskLens - 全局认证脚本
 * 所有受保护页面都应引用本脚本
 *
 * 用法: <script src="../auth.js"></script> (pages 目录)
 *      <script src="auth.js"></script> (根目录)
 *
 * 功能:
 * 1. 检查 localStorage 里的 token，没 token 跳 login.html
 * 2. 在 sidebar 底部注入"退出登录"按钮
 * 3. 提供 getToken() / getUser() 辅助函数
 * 4. 401 自动清 token 跳 login
 */

(function () {
    const pathPrefix = window.location.pathname.match(/^\/(risklens|legallens)\//);
    const API_BASE = pathPrefix ? `/${pathPrefix[1]}` : "";
    const TOKEN_KEY = "legallens_token";
    const USER_KEY = "legallens_user";

    // ===== Token 管理 =====
    function getToken() {
        return localStorage.getItem(TOKEN_KEY);
    }
    function getUser() {
        try {
            return JSON.parse(localStorage.getItem(USER_KEY) || "null");
        } catch {
            return null;
        }
    }
    function clearAuth() {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
    }
    window.LegalLensAuth = { getToken, getUser, clearAuth, API_BASE };

    // ===== 路由保护 =====
    const here = window.location.pathname;
    const isLoginPage = here.endsWith("/pages/login.html") || here.endsWith("/login.html");
    if (isLoginPage) return; // 登录页自身不需要 token

    const token = getToken();
    if (!token) {
        // 计算相对 login.html 的路径
        let loginPath = "pages/login.html";
        if (here.includes("/pages/")) {
            loginPath = "login.html";
        }
        window.location.replace(loginPath);
        return;
    }

    // ===== 注入退出按钮 =====
    function injectLogoutButton() {
        // 找 sidebar 底部的当前用户区域
        const candidates = document.querySelectorAll("aside .p-3.border-t, aside .p-4.border-t");
        if (candidates.length === 0) return;
        const container = candidates[0];

        const user = getUser();
        const display = user ? (user.display_name || user.username) : "已登录";

        // 在当前用户区域下方加一个退出按钮
        const logoutDiv = document.createElement("div");
        logoutDiv.className = "mt-2 flex items-center justify-between gap-2 px-2 py-1.5 text-xs text-stone-500 hover:text-rose-600 hover:bg-rose-50 rounded transition cursor-pointer";
        logoutDiv.innerHTML = `
            <span class="truncate">${escapeHtml(display)}</span>
            <span class="inline-flex items-center gap-1" data-action="logout">
                <i class="fa-solid fa-right-from-bracket"></i>退出
            </span>
        `;
        logoutDiv.addEventListener("click", doLogout);
        container.appendChild(logoutDiv);

        // 用实际登录账号替换模板中的占位用户信息。
        const userRow = container.querySelector(".flex.items-center.gap-3.px-2.py-2");
        if (userRow && user) {
            const avatar = userRow.children[0];
            const info = userRow.children[1];
            if (avatar) avatar.textContent = display.slice(0, 1).toUpperCase();
            if (info && info.children[0]) info.children[0].textContent = display;
            if (info && info.children[1]) {
                info.children[1].textContent = user.role === "admin" ? "系统管理员" : "普通用户 · 私有上传仅本人可见";
            }
        }
    }

    async function doLogout() {
        const t = getToken();
        if (t) {
            try {
                await fetch(`${API_BASE}/api/auth/logout`, {
                    method: "POST",
                    headers: { "Authorization": `Bearer ${t}` },
                });
            } catch (e) {
                // ignore
            }
        }
        clearAuth();
        const here2 = window.location.pathname;
        let loginPath = "pages/login.html";
        if (here2.includes("/pages/")) {
            loginPath = "login.html";
        }
        window.location.href = loginPath;
    }

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
    }

    // ===== 401 自动清 token 跳 login =====
    const origFetch = window.fetch;
    window.fetch = async function (input, init = {}) {
        const url = typeof input === "string" ? input : input.url;
        const headers = new Headers(
            init.headers || (typeof Request !== "undefined" && input instanceof Request ? input.headers : undefined)
        );
        const currentToken = getToken();
        if (currentToken && url.includes("/api/") && !headers.has("Authorization")) {
            headers.set("Authorization", `Bearer ${currentToken}`);
        }
        const requestInit = { ...init, headers };
        const res = typeof Request !== "undefined" && input instanceof Request
            ? await origFetch.call(this, new Request(input, requestInit))
            : await origFetch.call(this, input, requestInit);
        if (res.status === 401) {
            // auth API 自己 401 不跳（避免循环）
            if (!url.includes("/api/auth/")) {
                clearAuth();
                const here3 = window.location.pathname;
                let loginPath = "pages/login.html";
                if (here3.includes("/pages/")) {
                    loginPath = "login.html";
                }
                if (!window.location.pathname.endsWith("/login.html")) {
                    window.location.href = loginPath;
                }
            }
        }
        return res;
    };

    // 注入退出按钮
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", injectLogoutButton);
    } else {
        injectLogoutButton();
    }
})();
