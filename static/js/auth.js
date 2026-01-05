// 认证相关工具函数

/**
 * 获取当前 token
 */
function getToken() {
    return localStorage.getItem('token') || sessionStorage.getItem('token');
}

/**
 * 获取当前用户信息
 */
function getCurrentUser() {
    const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
    if (userStr) {
        return JSON.parse(userStr);
    }
    return null;
}

/**
 * 检查是否已登录
 */
function isLoggedIn() {
    return !!getToken();
}

/**
 * 检查用户是否具有指定角色
 */
function hasRole(requiredRole) {
    const user = getCurrentUser();
    if (!user) {
        return false;
    }
    return user.role === requiredRole;
}

/**
 * 检查是否为管理员
 */
function isAdmin() {
    return hasRole('admin');
}

/**
 * 登出
 */
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
    window.location.href = '/login';
}

/**
 * 检查登录状态，如果未登录则跳转到登录页
 */
function requireLogin() {
    if (!isLoggedIn()) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

/**
 * 检查管理员权限，如果不是管理员则跳转到首页
 */
function requireAdmin() {
    if (!requireLogin()) {
        return false;
    }
    if (!isAdmin()) {
        alert('权限不足，需要管理员权限');
        window.location.href = '/';
        return false;
    }
    return true;
}

/**
 * 为 fetch 请求添加认证 token
 */
function fetchWithAuth(url, options = {}) {
    const token = getToken();

    if (!options.headers) {
        options.headers = {};
    }

    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }

    return fetch(url, options);
}

/**
 * 处理认证错误
 */
function handleAuthError(response) {
    if (response.status === 401) {
        // Token 无效或过期，清除登录信息并跳转到登录页
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('user');
        window.location.href = '/login';
    }
    return response;
}

/**
 * 检查响应状态，如果是 401 则清除 token 并跳转到登录页
 */
function checkAuthError(response) {
    if (response.status === 401) {
        // Token 无效或过期，清除登录信息并跳转到登录页
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('user');
        window.location.href = '/login';
        return true;
    }
    return false;
}