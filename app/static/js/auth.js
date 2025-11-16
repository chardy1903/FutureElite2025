/**
 * Client-side authentication
 */

// Helper to ensure storage is ready
async function ensureStorageReady() {
    if (!clientStorage.db) {
        await clientStorage.init();
    }
}

// Authentication functions
const clientAuth = {
    async login(username, password) {
        await ensureStorageReady();
        const user = await clientStorage.getUserByUsername(username);
        if (!user) {
            throw new Error('Invalid username or password');
        }

        const isValid = await clientStorage.verifyPassword(user, password);
        if (!isValid) {
            throw new Error('Invalid username or password');
        }

        // Set current user
        clientStorage.setCurrentUserId(user.id);
        sessionStorage.setItem('username', user.username);
        localStorage.setItem('username', user.username);

        return { success: true, user: user };
    },

    async register(username, password, email = null) {
        await ensureStorageReady();
        
        if (!username || !password) {
            throw new Error('Username and password are required');
        }

        if (password.length < 6) {
            throw new Error('Password must be at least 6 characters');
        }

        const user = await clientStorage.createUser(username, password, email);
        if (!user) {
            throw new Error('Username already exists');
        }

        // Auto-login after registration
        clientStorage.setCurrentUserId(user.id);
        sessionStorage.setItem('username', user.username);
        localStorage.setItem('username', user.username);

        return { success: true, user: user };
    },

    logout() {
        clientStorage.clearCurrentUserId();
        sessionStorage.removeItem('username');
        localStorage.removeItem('username');
        return { success: true };
    },

    isAuthenticated() {
        return !!clientStorage.getCurrentUserId();
    },

    getCurrentUsername() {
        return sessionStorage.getItem('username') || localStorage.getItem('username');
    }
};

