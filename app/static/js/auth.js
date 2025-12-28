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
            // Note: Login endpoint is exempt from CSRF (entry point, rate-limited, requires credentials)
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Include cookies for session
                body: JSON.stringify({ username, password })
            });

            // Check if response is JSON before parsing
            const contentType = response.headers.get('content-type') || '';
            if (!contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Non-JSON response from login:', {
                    status: response.status,
                    contentType: contentType,
                    body: text.substring(0, 200)
                });
                throw new Error(`Server returned non-JSON response (${response.status}): ${text.substring(0, 100)}`);
            }

            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.errors?.[0] || 'Login failed');
            }

            // Server sets session cookie, store username and user_id locally for UI
            sessionStorage.setItem('username', username);
            localStorage.setItem('username', username);
            
            // Store user ID for authentication checks
            if (result.user_id) {
                clientStorage.setCurrentUserId(result.user_id);
            }

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

            // Email is now required for password reset functionality
            if (!email || !email.trim()) {
                throw new Error('Email address is required for password reset functionality');
            }

            // Basic email validation
            const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
            if (!emailPattern.test(email)) {
                throw new Error('Please enter a valid email address');
            }

            if (password.length < 8) {
                throw new Error('Password must be at least 8 characters');
            }

            // Note: Register endpoint is exempt from CSRF (entry point, rate-limited, requires credentials)
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Include cookies for session
                body: JSON.stringify({ username, password, email })
            });

            // Check if response is JSON before parsing
            const contentType = response.headers.get('content-type') || '';
            if (!contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Non-JSON response from register:', {
                    status: response.status,
                    contentType: contentType,
                    body: text.substring(0, 200)
                });
                throw new Error(`Server returned non-JSON response (${response.status}): ${text.substring(0, 100)}`);
            }

            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.errors?.[0] || 'Registration failed');
            }

            // Server sets session cookie, store username and user_id locally for UI
            sessionStorage.setItem('username', username);
            localStorage.setItem('username', username);
            
            // Store user ID for authentication checks
            if (result.user_id) {
                clientStorage.setCurrentUserId(result.user_id);
            }

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

