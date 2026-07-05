//公共工具函数-验证码刷新-Toast提示
function refreshCaptcha() {
    const img = document.getElementById('captchaImage');
    img.src = window.captchaUrl + "?t=" + Date.now();
    document.getElementById('captcha').value = '';
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'warning') icon = '⚠️';
    if (type === 'alert') icon = '❌';
    
    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>
        <div class="toast-content">
            <div class="toast-title">${type === 'success' ? '成功' : type === 'alert' ? '错误' : '提示'}</div>
            <div class="toast-desc">${message}</div>
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => {
            toast.remove();
        }, 400);
    }, 3000);
}