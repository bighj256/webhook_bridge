document.getElementById('registerBtn').addEventListener('click', async () => {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const confirmPassword = document.getElementById('confirmPassword').value.trim();
    const captcha = document.getElementById('captcha').value.trim();
    
    if (!username || !password) {
        showToast('用户名和密码不能为空', 'warning');
        return;
    }
    
    if (username.length < 3 || username.length > 20) {
        showToast('用户名长度需在3-20字符之间', 'warning');
        return;
    }
    
    if (password.length < 6) {
        showToast('密码长度至少6位', 'warning');
        return;
    }
    
    if (password !== confirmPassword) {
        showToast('两次输入的密码不一致', 'warning');
        return;
    }
    
    if (!captcha) {
        showToast('请输入验证码', 'warning');
        return;
    }
    
    try {
        const response = await fetch(window.registerUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password, confirmPassword, captcha })
            });
        
        const data = await response.json();
        
        if (data.code === 0) {
            showToast('注册成功，正在跳转...', 'success');
            setTimeout(() => {
                window.location.href = window.dashboardUrl;
            }, 1000);
        } else {
            showToast(data.message, 'alert');
            refreshCaptcha();
        }
    } catch (error) {
        showToast('网络错误，请稍后重试', 'alert');
    }
});

document.getElementById('captcha').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('registerBtn').click();
    }
});

document.getElementById('confirmPassword').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('registerBtn').click();
    }
});