/**
 * Client-side authentication
 */

// Helper to ensure storage is ready
async function ensureStorageReady() {
    if (!clientStorage.db) {
        await clientStorage.init();
    }
}

// Authentication functions - SECURITY FIX: Now uses server-side authentication
const clientAuth = {
    async login(username, password) {
        try {
            // SECURITY: Send plain password to server over HTTPS for secure server-side verification
            // Server uses werkzeug's scrypt-based password hashing
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Include cookies for session
                body: JSON.stringify({ username, password })
            });

            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.errors?.[0] || 'Login failed');
            }

            // Server sets session cookie, store username locally for UI
            sessionStorage.setItem('username', username);
            localStorage.setItem('username', username);

            return { success: true };
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    },

    async register(username, password, email = null) {
        try {
            // SECURITY: Send plain password to server over HTTPS for secure server-side hashing
            if (!username || !password) {
                throw new Error('Username and password are required');
            }

            if (password.length < 6) {
                throw new Error('Password must be at least 6 characters');
            }

            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Include cookies for session
                body: JSON.stringify({ username, password, email })
            });

            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.errors?.[0] || 'Registration failed');
            }

            // Server sets session cookie, store username locally for UI
            sessionStorage.setItem('username', username);
            localStorage.setItem('username', username);

            return { success: true };
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    },

    async logout() {
        try {
            // Call server logout endpoint to clear session
            await fetch('/logout', {
                method: 'GET',
                credentials: 'include'
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local storage regardless
            clientStorage.clearCurrentUserId();
            sessionStorage.removeItem('username');
            localStorage.removeItem('username');
        }
        return { success: true };
    },

    isAuthenticated() {
        return !!clientStorage.getCurrentUserId();
    },

    getCurrentUsername() {
        return sessionStorage.getItem('username') || localStorage.getItem('username');
    }
};

