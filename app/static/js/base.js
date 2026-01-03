/**
 * Base utility functions for the application
 * These functions are used across multiple pages
 */

(function() {
    'use strict';

    // Toast notification functions - available globally
    window.showToast = function(message, type = 'success') {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toast-message');
        
        if (!toast || !toastMessage) {
            console.warn('Toast elements not found');
            return;
        }
        
        // Update toast styling based on type
        const toastDiv = toast.querySelector('div');
        if (type === 'error') {
            toastDiv.className = 'bg-white border-l-4 border-red-400 p-4 shadow-lg rounded';
            toastMessage.className = 'text-sm font-medium text-red-900';
        } else if (type === 'warning') {
            toastDiv.className = 'bg-white border-l-4 border-yellow-400 p-4 shadow-lg rounded';
            toastMessage.className = 'text-sm font-medium text-yellow-900';
        } else {
            toastDiv.className = 'bg-white border-l-4 border-green-400 p-4 shadow-lg rounded';
            toastMessage.className = 'text-sm font-medium text-gray-900';
        }
        
        toastMessage.textContent = message;
        toast.classList.remove('hidden');
        toast.classList.add('show');
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.classList.add('hidden'), 300);
        }, 3000);
    };

    window.showLoading = function(message = 'Please wait...') {
        const loading = document.getElementById('loading');
        const loadingMessage = document.getElementById('loading-message');
        if (loading && loadingMessage) {
            loadingMessage.textContent = message;
            loading.classList.remove('hidden');
        }
    };

    window.hideLoading = function() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.classList.add('hidden');
        }
    };

    // Format date for input (converts "dd MMM yyyy" to "YYYY-MM-DD" for HTML date input)
    window.formatDateForInput = function(dateStr) {
        if (!dateStr || dateStr === 'None' || dateStr === 'null') return '';
        
        // If already in YYYY-MM-DD format, return as is
        if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr.trim())) {
            return dateStr.trim();
        }
        
        // Try to parse "dd MMM yyyy" format
        const months = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
            'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        };
        
        const parts = dateStr.trim().split(' ');
        if (parts.length === 3) {
            const day = parts[0].padStart(2, '0');
            const month = months[parts[1]];
            const year = parts[2];
            if (month) {
                return `${year}-${month}-${day}`;
            }
        }
        return '';
    };

    // Format date for display
    window.formatDateForDisplay = function(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-GB', { 
            day: '2-digit', 
            month: 'short', 
            year: 'numeric' 
        });
    };

    // Get result color class
    window.getResultColor = function(result) {
        switch(result) {
            case 'Win': return 'text-green-600';
            case 'Draw': return 'text-yellow-600';
            case 'Loss': return 'text-red-600';
            default: return 'text-gray-600';
        }
    };

    // Get category badge color
    window.getCategoryBadgeColor = function(category) {
        switch(category) {
            case 'Pre-Season Friendly': return 'bg-blue-100 text-blue-800';
            case 'League': return 'bg-green-100 text-green-800';
            case 'Friendly': return 'bg-purple-100 text-purple-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    // Check authentication on page load
    document.addEventListener('DOMContentLoaded', async function() {
        // Wait for dependencies to be available
        if (typeof ensureStorageReady === 'function' && typeof clientAuth !== 'undefined') {
            await ensureStorageReady();
            const isAuth = clientAuth.isAuthenticated();
            const username = clientAuth.getCurrentUsername();
            
            if (isAuth && username) {
                // Show authenticated UI
                const navLinks = document.getElementById('navLinks');
                const userInfo = document.getElementById('userInfo');
                const logoutLink = document.getElementById('logoutLink');
                const loginLink = document.getElementById('loginLink');
                const registerLink = document.getElementById('registerLink');
                
                if (navLinks) navLinks.style.display = 'flex';
                if (userInfo) {
                    userInfo.textContent = username;
                    userInfo.style.display = 'block';
                }
                if (logoutLink) logoutLink.style.display = 'block';
                if (loginLink) loginLink.style.display = 'none';
                if (registerLink) registerLink.style.display = 'none';
                
                // Handle logout
                if (logoutLink) {
                    logoutLink.addEventListener('click', function(e) {
                        e.preventDefault();
                        clientAuth.logout();
                        window.location.href = '/login';
                    });
                }
            } else {
                // Show unauthenticated UI
                const navLinks = document.getElementById('navLinks');
                const userInfo = document.getElementById('userInfo');
                const logoutLink = document.getElementById('logoutLink');
                const loginLink = document.getElementById('loginLink');
                const registerLink = document.getElementById('registerLink');
                
                if (navLinks) navLinks.style.display = 'none';
                if (userInfo) userInfo.style.display = 'none';
                if (logoutLink) logoutLink.style.display = 'none';
                if (loginLink) loginLink.style.display = 'block';
                if (registerLink) registerLink.style.display = 'block';
            }
        }
    });
})();

