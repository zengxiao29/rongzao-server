// 登录处理函数
async function handleLogin(event) {
    event.preventDefault();

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('rememberMe').checked;
    const errorDiv = document.getElementById('errorMessage');
    const loginButton = document.getElementById('loginButton');

    // 隐藏错误信息
    errorDiv.classList.remove('show');

    // 禁用登录按钮
    loginButton.disabled = true;
    loginButton.textContent = '登录中...';

    try {
        const headers = {
            'Content-Type': 'application/json',
        };

        // 获取CSRF token并添加到请求头
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                         document.querySelector('input[name="csrf_token"]')?.value;
        
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                username: username,
                password: password,
                remember_me: rememberMe
            })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            // 保存 token
            if (rememberMe) {
                // 记住我，保存到 localStorage
                localStorage.setItem('token', result.token);
                localStorage.setItem('user', JSON.stringify(result.user));
                // 同时保存到 cookie，过期时间为 14 天
                document.cookie = `token=${result.token}; path=/; max-age=${14 * 24 * 60 * 60}`;
            } else {
                // 不记住，保存到 sessionStorage
                sessionStorage.setItem('token', result.token);
                sessionStorage.setItem('user', JSON.stringify(result.user));
                // 同时保存到 cookie，会话级别（关闭浏览器即失效）
                document.cookie = `token=${result.token}; path=/`;
            }

            // 跳转到首页
            window.location.href = '/';
        } else {
            // 显示错误信息
            errorDiv.textContent = result.error || '登录失败，请重试';
            errorDiv.classList.add('show');
        }
    } catch (error) {
        console.error('登录失败:', error);
        errorDiv.textContent = '登录失败，请检查网络连接';
        errorDiv.classList.add('show');
    } finally {
        // 恢复登录按钮
        loginButton.disabled = false;
        loginButton.textContent = '登录';
    }
}

// 页面加载时检查是否已登录
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');

    if (token) {
        // 已登录，跳转到首页
        window.location.href = '/';
    }
});