document.getElementById('loginBtn').addEventListener('click', async () => {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const captcha = document.getElementById('captcha').value.trim();
    
    if (!username || !password) {
        showToast('用户名和密码不能为空', 'warning');
        return;
    }
    
    if (!captcha) {
        showToast('请输入验证码', 'warning');
        return;
    }
    
    try {
        const response = await fetch(window.loginUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password, captcha })
            });
        
        const data = await response.json();
        
        if (data.code === 0) {
            showToast('登录成功，正在跳转...', 'success');
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
        document.getElementById('loginBtn').click();
    }
});

document.getElementById('password').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('loginBtn').click();
    }
});