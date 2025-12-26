/**
 * CSRF Token Management
 * Fetches and manages CSRF tokens for API requests
 * Tokens are stored only in memory, never in localStorage or cookies
 */

const csrfManager = {
    _token: null,
    _fetching: false,
    _fetchPromise: null,

    /**
     * Get CSRF token, fetching if necessary
     * @returns {Promise<string>} CSRF token
     */
    async getToken() {
        // Return cached token if available
        if (this._token) {
            return this._token;
        }

        // If already fetching, wait for that promise
        if (this._fetching && this._fetchPromise) {
            return await this._fetchPromise;
        }

        // Fetch new token
        this._fetching = true;
        this._fetchPromise = this._fetchToken();

        try {
            this._token = await this._fetchPromise;
            return this._token;
        } catch (error) {
            console.error('Failed to fetch CSRF token:', error);
            // Return empty string to allow request to proceed (will fail with 400, but better than blocking)
            return '';
        } finally {
            this._fetching = false;
            this._fetchPromise = null;
        }
    },

    /**
     * Fetch CSRF token from server
     * @returns {Promise<string>} CSRF token
     */
    async _fetchToken() {
        const response = await fetch('/api/csrf-token', {
            method: 'GET',
            credentials: 'include' // Include cookies for session
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch CSRF token: ${response.status}`);
        }

        const data = await response.json();
        if (!data.csrf_token) {
            throw new Error('CSRF token not in response');
        }

        return data.csrf_token;
    },

    /**
     * Clear cached token (e.g., on logout or session change)
     */
    clearToken() {
        this._token = null;
    },

    /**
     * Check if token is available
     * @returns {boolean}
     */
    hasToken() {
        return this._token !== null;
    }
};

// Initialize token on page load
document.addEventListener('DOMContentLoaded', async () => {
    // Only fetch token if user appears to be authenticated
    // (check for session cookie or other auth indicators)
    try {
        await csrfManager.getToken();
    } catch (error) {
        // Silently fail - token will be fetched on first API call
        console.debug('CSRF token fetch deferred:', error);
    }
});

