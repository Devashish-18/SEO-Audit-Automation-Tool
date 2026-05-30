// ============================================================================
// SHARED APP.JS - Global Functions and Navigation
// ============================================================================

// ============================================================================
// AUTHENTICATION FUNCTIONS
// ============================================================================

function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('email')?.value;
    const password = document.getElementById('password')?.value;
    const rememberMe = document.getElementById('remember')?.checked;

    if (!email || !password) {
        showAlert('Please fill in all fields', 'warning');
        return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showAlert('Please enter a valid email', 'warning');
        return;
    }

    // Store session
    sessionStorage.setItem('isLoggedIn', 'true');
    sessionStorage.setItem('userEmail', email);
    sessionStorage.setItem('userName', email.split('@')[0]);
    
    if (rememberMe) {
        localStorage.setItem('rememberEmail', email);
    }

    showAlert('Login successful! Redirecting...', 'success');
    setTimeout(() => {
        window.location.href = 'index.html';
    }, 1500);
}

function handleLogout() {
    sessionStorage.clear();
    localStorage.removeItem('rememberEmail');
    window.location.href = 'login.html';
}

function checkAuth() {
    const isLoggedIn = sessionStorage.getItem('isLoggedIn');
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    if (!isLoggedIn && currentPage !== 'login.html') {
        window.location.href = 'login.html';
    }
    
    if (isLoggedIn && currentPage === 'login.html') {
        window.location.href = 'index.html';
    }
}

// ============================================================================
// MODAL FUNCTIONS
// ============================================================================

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
    document.body.style.overflow = 'auto';
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        closeAllModals();
    }
});

// ============================================================================
// ALERT FUNCTIONS
// ============================================================================

function showAlert(message, type = 'info', duration = 3000) {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer; font-size: 18px;">×</button>
        </div>
    `;
    
    alertContainer.appendChild(alert);
    
    if (duration > 0) {
        setTimeout(() => alert.remove(), duration);
    }
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 3000; max-width: 400px;';
    document.body.appendChild(container);
    return container;
}

// ============================================================================
// NAVIGATION FUNCTIONS
// ============================================================================

function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const currentPath = window.location.pathname.split('/').pop() || 'index.html';
    
    navItems.forEach(item => {
        const href = item.getAttribute('href') || item.getAttribute('data-page');
        if (href === currentPath) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
        
        item.addEventListener('click', handleNavigation);
    });
}

function handleNavigation(event) {
    const href = this.getAttribute('href');
    if (!href) return;
    
    event.preventDefault();
    window.location.href = href;
}

// ============================================================================
// SIDEBAR MOBILE TOGGLE
// ============================================================================

function initializeSidebarToggle() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const closeSidebarBtn = document.getElementById('closeSidebarBtn');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    const closeSidebar = () => {
        sidebar.classList.remove('active');
        overlay?.classList.remove('active');
    };

    const openSidebar = () => {
        sidebar.classList.add('active');
        overlay?.classList.add('active');
    };

    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', () => {
            if (sidebar.classList.contains('active')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });

        if (closeSidebarBtn) {
            closeSidebarBtn.addEventListener('click', closeSidebar);
        }

        if (overlay) {
            overlay.addEventListener('click', closeSidebar);
        }

        // Close sidebar when clicking nav items on mobile
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                if (window.innerWidth <= 768) {
                    closeSidebar();
                }
            });
        });
    }
}

function initializeTopbarActions() {
    const notificationBtn = document.getElementById('notificationBtn');
    const profileMenu = document.getElementById('profileMenu');

    if (notificationBtn) {
        notificationBtn.addEventListener('click', () => {
            window.location.href = 'notifications.html';
        });
    }

    if (profileMenu) {
        profileMenu.addEventListener('click', () => {
            window.location.href = 'profile.html';
        });
    }
}

// ============================================================================
// TABLE FUNCTIONS
// ============================================================================

function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;
    
    input.addEventListener('keyup', () => {
        const filter = input.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(filter) ? '' : 'none';
        });
    });
}

function sortTable(tableId, columnIndex) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const isAsc = table.getAttribute('data-sort') === 'asc';
    
    rows.sort((a, b) => {
        const aVal = a.children[columnIndex].textContent;
        const bVal = b.children[columnIndex].textContent;
        return isAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
    
    rows.forEach(row => table.querySelector('tbody').appendChild(row));
    table.setAttribute('data-sort', isAsc ? 'desc' : 'asc');
}

// ============================================================================
// PAGINATION
// ============================================================================

function paginate(items, itemsPerPage, pageNumber) {
    const start = (pageNumber - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    return items.slice(start, end);
}

function createPagination(totalItems, itemsPerPage, onPageChange) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    let html = '<div class="pagination" style="display: flex; gap: 8px; margin-top: 20px; justify-content: center;">';
    
    for (let i = 1; i <= totalPages; i++) {
        html += `<button class="btn btn-sm" onclick="(${onPageChange})(${i})" style="min-width: 40px;">${i}</button>`;
    }
    
    html += '</div>';
    return html;
}

// ============================================================================
// FORM FUNCTIONS
// ============================================================================

function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = '#FF0000';
            isValid = false;
        } else {
            input.style.borderColor = '';
        }
    });
    
    return isValid;
}

function resetForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
        form.querySelectorAll('input, select, textarea').forEach(el => {
            el.style.borderColor = '';
        });
    }
}

function getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return null;
    
    const formData = new FormData(form);
    const data = {};
    
    formData.forEach((value, key) => {
        if (data[key]) {
            if (!Array.isArray(data[key])) {
                data[key] = [data[key]];
            }
            data[key].push(value);
        } else {
            data[key] = value;
        }
    });
    
    return data;
}

// ============================================================================
// STORAGE FUNCTIONS
// ============================================================================

function saveToLocalStorage(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

function getFromLocalStorage(key) {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : null;
}

function removeFromLocalStorage(key) {
    localStorage.removeItem(key);
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(date) {
    return new Date(date).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function generateId() {
    return '_' + Math.random().toString(36).substr(2, 9);
}

function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    initializeNavigation();
    initializeSidebarToggle();
    initializeTopbarActions();
    
    // Close modal buttons
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) closeModal(modal.id);
        });
    });
    
    // Logout handlers
    document.querySelectorAll('[data-logout]').forEach(btn => {
        btn.addEventListener('click', handleLogout);
    });
});

// Auto-fill remember me email on login page
window.addEventListener('load', () => {
    const rememberEmail = localStorage.getItem('rememberEmail');
    const emailInput = document.getElementById('email');
    if (rememberEmail && emailInput) {
        emailInput.value = rememberEmail;
        const rememberCheckbox = document.getElementById('remember');
        if (rememberCheckbox) rememberCheckbox.checked = true;
    }
});
