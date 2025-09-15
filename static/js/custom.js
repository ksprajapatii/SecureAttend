// Custom JavaScript for SecureAttend

// Global variables
let currentUser = null;
let apiToken = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Check for authentication token
    const token = localStorage.getItem('authToken');
    if (token) {
        apiToken = token;
        setAuthHeader(token);
    }
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize charts
    initializeCharts();
    
    // Setup form handlers
    setupFormHandlers();
    
    // Setup real-time updates
    setupRealTimeUpdates();
}

// Authentication functions
function login(username, password) {
    return fetch('/api/auth/token/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.access) {
            apiToken = data.access;
            localStorage.setItem('authToken', data.access);
            localStorage.setItem('refreshToken', data.refresh);
            setAuthHeader(data.access);
            return data;
        } else {
            throw new Error(data.detail || 'Login failed');
        }
    });
}

function logout() {
    apiToken = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    window.location.href = '/login/';
}

function setAuthHeader(token) {
    // Set default authorization header for all requests
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        options.headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        };
        return originalFetch(url, options);
    };
}

// API helper functions
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    };
    
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (response.status === 401) {
        // Token expired, try to refresh
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
            try {
                const refreshResponse = await fetch('/api/auth/token/refresh/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh: refreshToken })
                });
                const refreshData = await refreshResponse.json();
                if (refreshData.access) {
                    apiToken = refreshData.access;
                    localStorage.setItem('authToken', refreshData.access);
                    setAuthHeader(refreshData.access);
                    // Retry original request
                    return fetch(url, { ...defaultOptions, ...options });
                }
            } catch (error) {
                console.error('Token refresh failed:', error);
                logout();
                return;
            }
        } else {
            logout();
            return;
        }
    }
    
    return response;
}

// Face recognition functions
async function recognizeFace(imageFile) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('check_liveness', 'true');
    formData.append('check_mask', 'true');
    
    const response = await apiRequest('/api/recognize-face/', {
        method: 'POST',
        headers: {}, // Don't set Content-Type for FormData
        body: formData
    });
    
    return response.json();
}

async function markAttendance(userId, confidence, livenessScore, isLive, hasMask, capturedImage = null) {
    const data = {
        user_id: userId,
        confidence: confidence,
        liveness_score: livenessScore,
        is_live: isLive,
        has_mask: hasMask
    };
    
    if (capturedImage) {
        data.captured_image = capturedImage;
    }
    
    const response = await apiRequest('/api/mark-attendance/', {
        method: 'POST',
        body: JSON.stringify(data)
    });
    
    return response.json();
}

// User management functions
async function getUsers() {
    const response = await apiRequest('/api/users/');
    return response.json();
}

async function createUser(userData) {
    const formData = new FormData();
    Object.keys(userData).forEach(key => {
        if (userData[key] !== null && userData[key] !== undefined) {
            formData.append(key, userData[key]);
        }
    });
    
    const response = await apiRequest('/api/users/', {
        method: 'POST',
        headers: {}, // Don't set Content-Type for FormData
        body: formData
    });
    
    return response.json();
}

async function updateUser(userId, userData) {
    const formData = new FormData();
    Object.keys(userData).forEach(key => {
        if (userData[key] !== null && userData[key] !== undefined) {
            formData.append(key, userData[key]);
        }
    });
    
    const response = await apiRequest(`/api/users/${userId}/`, {
        method: 'PATCH',
        headers: {}, // Don't set Content-Type for FormData
        body: formData
    });
    
    return response.json();
}

// Attendance functions
async function getAttendanceRecords(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await apiRequest(`/api/attendance/?${params}`);
    return response.json();
}

async function getAttendanceStats() {
    const response = await apiRequest('/api/stats/');
    return response.json();
}

// Alert functions
async function getAlerts(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await apiRequest(`/api/alerts/?${params}`);
    return response.json();
}

async function resolveAlert(alertId) {
    const response = await apiRequest(`/api/alerts/${alertId}/`, {
        method: 'PATCH',
        body: JSON.stringify({ is_resolved: true })
    });
    
    return response.json();
}

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

function showLoading(element) {
    if (element) {
        element.innerHTML = '<span class="spinner"></span> Loading...';
        element.disabled = true;
    }
}

function hideLoading(element, originalText) {
    if (element) {
        element.innerHTML = originalText;
        element.disabled = false;
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatConfidence(confidence) {
    return (confidence * 100).toFixed(1) + '%';
}

// Image handling functions
function convertImageToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function resizeImage(file, maxWidth = 800, maxHeight = 600) {
    return new Promise((resolve) => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        
        img.onload = () => {
            let { width, height } = img;
            
            if (width > height) {
                if (width > maxWidth) {
                    height = (height * maxWidth) / width;
                    width = maxWidth;
                }
            } else {
                if (height > maxHeight) {
                    width = (width * maxHeight) / height;
                    height = maxHeight;
                }
            }
            
            canvas.width = width;
            canvas.height = height;
            
            ctx.drawImage(img, 0, 0, width, height);
            canvas.toBlob(resolve, 'image/jpeg', 0.8);
        };
        
        img.src = URL.createObjectURL(file);
    });
}

// Chart functions
function initializeCharts() {
    // Initialize any charts on the page
    const chartElements = document.querySelectorAll('[data-chart]');
    chartElements.forEach(element => {
        const chartType = element.dataset.chart;
        const chartData = JSON.parse(element.dataset.chartData || '{}');
        createChart(element, chartType, chartData);
    });
}

function createChart(canvas, type, data) {
    const ctx = canvas.getContext('2d');
    return new Chart(ctx, {
        type: type,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Form handlers
function setupFormHandlers() {
    // Handle file uploads
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', handleFileUpload);
    });
    
    // Handle form submissions
    const forms = document.querySelectorAll('form[data-ajax]');
    forms.forEach(form => {
        form.addEventListener('submit', handleAjaxForm);
    });
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
        if (!allowedTypes.includes(file.type)) {
            showNotification('Please select a valid image file (JPEG or PNG)', 'danger');
            event.target.value = '';
            return;
        }
        
        // Validate file size (10MB max)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            showNotification('File size must be less than 10MB', 'danger');
            event.target.value = '';
            return;
        }
        
        // Preview image
        const preview = document.getElementById(event.target.dataset.preview);
        if (preview) {
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    }
}

async function handleAjaxForm(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    showLoading(submitBtn);
    
    try {
        const formData = new FormData(form);
        const response = await apiRequest(form.action, {
            method: form.method || 'POST',
            headers: {}, // Don't set Content-Type for FormData
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Operation completed successfully', 'success');
            if (form.dataset.redirect) {
                window.location.href = form.dataset.redirect;
            } else {
                location.reload();
            }
        } else {
            showNotification(result.detail || 'Operation failed', 'danger');
        }
    } catch (error) {
        console.error('Form submission error:', error);
        showNotification('An error occurred. Please try again.', 'danger');
    } finally {
        hideLoading(submitBtn, originalText);
    }
}

// Real-time updates
function setupRealTimeUpdates() {
    // Update stats every 30 seconds
    setInterval(updateStats, 30000);
    
    // Check for new alerts every 60 seconds
    setInterval(checkNewAlerts, 60000);
}

async function updateStats() {
    try {
        const stats = await getAttendanceStats();
        updateStatsDisplay(stats);
    } catch (error) {
        console.error('Failed to update stats:', error);
    }
}

function updateStatsDisplay(stats) {
    // Update stat cards
    const statElements = {
        'total-users': stats.total_users,
        'present-today': stats.present_today,
        'absent-today': stats.absent_today,
        'active-alerts': stats.anomaly_alerts_today
    };
    
    Object.keys(statElements).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = statElements[id];
        }
    });
}

async function checkNewAlerts() {
    try {
        const alerts = await getAlerts({ is_resolved: 'false' });
        const alertCount = alerts.count;
        const currentCount = document.querySelector('.badge.bg-danger')?.textContent || '0';
        
        if (alertCount > parseInt(currentCount)) {
            showNotification(`You have ${alertCount} unresolved alerts`, 'warning');
            // Update alert badge
            const badge = document.querySelector('.badge.bg-danger');
            if (badge) {
                badge.textContent = alertCount;
            }
        }
    } catch (error) {
        console.error('Failed to check alerts:', error);
    }
}

// Tooltip initialization
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Export functions for global use
window.SecureAttend = {
    login,
    logout,
    recognizeFace,
    markAttendance,
    getUsers,
    createUser,
    updateUser,
    getAttendanceRecords,
    getAttendanceStats,
    getAlerts,
    resolveAlert,
    showNotification,
    formatDate,
    formatConfidence,
    convertImageToBase64,
    resizeImage
};
