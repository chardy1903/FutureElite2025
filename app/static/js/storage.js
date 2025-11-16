/**
 * Client-side storage manager using IndexedDB
 * Provides the same interface as the server-side storage but stores data locally in the browser
 */

class ClientStorage {
    constructor() {
        this.dbName = 'FutureEliteDB';
        this.dbVersion = 1;
        this.db = null;
    }

    /**
     * Initialize the IndexedDB database
     */
    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Create object stores
                if (!db.objectStoreNames.contains('matches')) {
                    const matchesStore = db.createObjectStore('matches', { keyPath: 'id' });
                    matchesStore.createIndex('user_id', 'user_id', { unique: false });
                    matchesStore.createIndex('date', 'date', { unique: false });
                }

                if (!db.objectStoreNames.contains('settings')) {
                    db.createObjectStore('settings', { keyPath: 'user_id' });
                }

                if (!db.objectStoreNames.contains('physical_measurements')) {
                    const pmStore = db.createObjectStore('physical_measurements', { keyPath: 'id' });
                    pmStore.createIndex('user_id', 'user_id', { unique: false });
                }

                if (!db.objectStoreNames.contains('achievements')) {
                    const achStore = db.createObjectStore('achievements', { keyPath: 'id' });
                    achStore.createIndex('user_id', 'user_id', { unique: false });
                }

                if (!db.objectStoreNames.contains('club_history')) {
                    const chStore = db.createObjectStore('club_history', { keyPath: 'id' });
                    chStore.createIndex('user_id', 'user_id', { unique: false });
                }

                if (!db.objectStoreNames.contains('training_camps')) {
                    const tcStore = db.createObjectStore('training_camps', { keyPath: 'id' });
                    tcStore.createIndex('user_id', 'user_id', { unique: false });
                }

                if (!db.objectStoreNames.contains('physical_metrics')) {
                    const pmetricsStore = db.createObjectStore('physical_metrics', { keyPath: 'id' });
                    pmetricsStore.createIndex('user_id', 'user_id', { unique: false });
                }

                if (!db.objectStoreNames.contains('users')) {
                    const usersStore = db.createObjectStore('users', { keyPath: 'id' });
                    usersStore.createIndex('username', 'username', { unique: true });
                }

                if (!db.objectStoreNames.contains('subscriptions')) {
                    const subStore = db.createObjectStore('subscriptions', { keyPath: 'user_id' });
                    subStore.createIndex('stripe_subscription_id', 'stripe_subscription_id', { unique: false });
                }
            };
        });
    }

    /**
     * Get current user ID (from sessionStorage or localStorage)
     */
    getCurrentUserId() {
        return sessionStorage.getItem('user_id') || localStorage.getItem('user_id');
    }

    /**
     * Set current user ID
     */
    setCurrentUserId(userId) {
        sessionStorage.setItem('user_id', userId);
        localStorage.setItem('user_id', userId);
    }

    /**
     * Clear current user ID
     */
    clearCurrentUserId() {
        sessionStorage.removeItem('user_id');
        localStorage.removeItem('user_id');
    }

    // ========== Generic CRUD operations ==========

    async _getAll(storeName, userId = null) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            
            // If userId is provided, use index for better performance and strict filtering
            if (userId) {
                const index = store.index('user_id');
                const request = index.getAll(userId);
                
                request.onsuccess = () => {
                    const items = request.result || [];
                    // Double-check: only return items with exact user_id match
                    const filtered = items.filter(item => item && item.user_id === userId);
                    resolve(filtered);
                };
                
                request.onerror = () => reject(request.error);
            } else {
                // If no userId, get all but this should rarely be used
                const request = store.getAll();
                
                request.onsuccess = () => {
                    const items = request.result || [];
                    resolve(items);
                };
                
                request.onerror = () => reject(request.error);
            }
        });
    }

    async _getById(storeName, id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.get(id);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async _save(storeName, item) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.put(item);

            request.onsuccess = () => resolve(item);
            request.onerror = () => reject(request.error);
        });
    }

    async _delete(storeName, id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.delete(id);

            request.onsuccess = () => resolve(true);
            request.onerror = () => reject(request.error);
        });
    }

    async _getByIndex(storeName, indexName, value) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const index = store.index(indexName);
            const request = index.getAll(value);

            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    // ========== Matches ==========

    async getAllMatches(userId = null) {
        const uid = userId || this.getCurrentUserId();
        if (!uid) {
            console.warn('No user_id provided to getAllMatches');
            return [];
        }
        const matches = await this._getAll('matches', uid);
        // Extra safety: filter out any items without user_id or with wrong user_id
        return matches.filter(m => m && m.user_id === uid);
    }

    async getMatch(matchId) {
        return await this._getById('matches', matchId);
    }

    async saveMatch(match) {
        const userId = this.getCurrentUserId();
        if (!userId) {
            throw new Error('User must be logged in to save matches');
        }
        // Always set user_id to current user (security: prevent saving to other users)
        match.user_id = userId;
        if (!match.id) {
            match.id = 'match_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
        return await this._save('matches', match);
    }

    async deleteMatch(matchId) {
        return await this._delete('matches', matchId);
    }

    // ========== Settings ==========

    async loadSettings(userId = null) {
        const uid = userId || this.getCurrentUserId();
        const settings = await this._getById('settings', uid);
        if (!settings) {
            // Return default settings
            return {
                user_id: uid,
                club_name: '',
                player_name: '',
                season_year: '',
                date_of_birth: null,
                position: null,
                dominant_foot: null,
                height_cm: null,
                weight_kg: null,
                phv_date: null,
                phv_age: null,
                primary_color: '#B22222',
                header_color: '#1F2937',
                player_photo_path: null,
                highlight_reel_urls: [],
                contact_email: null,
                social_media_links: {}
            };
        }
        return settings;
    }

    async saveSettings(settings) {
        const userId = this.getCurrentUserId();
        if (!userId) {
            throw new Error('User must be logged in to save settings');
        }
        settings.user_id = userId; // Always set to current user
        return await this._save('settings', settings);
    }

    // ========== Physical Measurements ==========

    async getAllPhysicalMeasurements(userId = null) {
        const uid = userId || this.getCurrentUserId();
        if (!uid) {
            return [];
        }
        const measurements = await this._getAll('physical_measurements', uid);
        return measurements.filter(m => m && m.user_id === uid);
    }

    async savePhysicalMeasurement(measurement) {
        const userId = this.getCurrentUserId();
        if (!userId) {
            throw new Error('User must be logged in to save physical measurements');
        }
        measurement.user_id = userId; // Always set to current user
        if (!measurement.id) {
            measurement.id = 'pm_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
        return await this._save('physical_measurements', measurement);
    }

    async deletePhysicalMeasurement(measurementId) {
        return await this._delete('physical_measurements', measurementId);
    }

    // ========== Achievements ==========

    async getAllAchievements(userId = null) {
        const uid = userId || this.getCurrentUserId();
        if (!uid) {
            return [];
        }
        const achievements = await this._getAll('achievements', uid);
        return achievements.filter(a => a && a.user_id === uid);
    }

    async saveAchievement(achievement) {
        const userId = this.getCurrentUserId();
        if (!userId) {
            throw new Error('User must be logged in to save achievements');
        }
        achievement.user_id = userId; // Always set to current user
        if (!achievement.id) {
            achievement.id = 'ach_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
        return await this._save('achievements', achievement);
    }

    async deleteAchievement(achievementId) {
        return await this._delete('achievements', achievementId);
    }

    // ========== Club History ==========

    async getAllClubHistory(userId = null) {
        const uid = userId || this.getCurrentUserId();
        if (!uid) {
            return [];
        }
        const history = await this._getAll('club_history', uid);
        return history.filter(h => h && h.user_id === uid);
    }

    async saveClubHistory(history) {
        const userId = this.getCurrentUserId();
        if (!userId) {
            throw new Error('User must be logged in to save club history');
        }
        history.user_id = userId; // Always set to current user
        if (!history.id) {
            history.id = 'ch_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
        return await this._save('club_history', history);
    }

    async deleteClubHistory(historyId) {
        return await this._delete('club_history', historyId);
    }

    // ========== Training Camps ==========

    async getAllTrainingCamps(userId = null) {
        const uid = userId || this.getCurrentUserId();
        if (!uid) {
            return [];
        }
        const camps = await this._getAll('training_camps', uid);
        return camps.filter(c => c && c.user_id === uid);
    }

    async saveTrainingCamp(camp) {
        const userId = this.getCurrentUserId();
        if (!userId) {
            throw new Error('User must be logged in to save training camps');
        }
        camp.user_id = userId; // Always set to current user
        if (!camp.id) {
            camp.id = 'tc_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
        return await this._save('training_camps', camp);
    }

    async deleteTrainingCamp(campId) {
        return await this._delete('training_camps', campId);
    }

    // ========== Physical Metrics ==========

    async getAllPhysicalMetrics(userId = null) {
        const uid = userId || this.getCurrentUserId();
        if (!uid) {
            return [];
        }
        const metrics = await this._getAll('physical_metrics', uid);
        return metrics.filter(m => m && m.user_id === uid);
    }

    async savePhysicalMetric(metric) {
        const userId = this.getCurrentUserId();
        if (!userId) {
            throw new Error('User must be logged in to save physical metrics');
        }
        metric.user_id = userId; // Always set to current user
        if (!metric.id) {
            metric.id = 'pmetric_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
        return await this._save('physical_metrics', metric);
    }

    async deletePhysicalMetric(metricId) {
        return await this._delete('physical_metrics', metricId);
    }

    // ========== Users ==========

    async getAllUsers() {
        return await this._getAll('users');
    }

    async getUserByUsername(username) {
        const users = await this._getByIndex('users', 'username', username);
        return users.length > 0 ? users[0] : null;
    }

    async getUserById(userId) {
        return await this._getById('users', userId);
    }

    async saveUser(user) {
        if (!user.id) {
            user.id = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
        return await this._save('users', user);
    }

    // Simple password hashing (using a basic approach - in production, use a proper library)
    async hashPassword(password) {
        // Use Web Crypto API for hashing
        const encoder = new TextEncoder();
        const data = encoder.encode(password);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    async verifyPassword(user, password) {
        const passwordHash = await this.hashPassword(password);
        return user.password_hash === passwordHash;
    }

    async createUser(username, password, email = null) {
        // Check if username exists
        const existing = await this.getUserByUsername(username);
        if (existing) {
            return null;
        }

        const passwordHash = await this.hashPassword(password);
        const user = {
            id: 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
            username: username,
            password_hash: passwordHash,
            email: email,
            created_at: new Date().toISOString()
        };

        await this.saveUser(user);
        return user;
    }

    // ========== Export/Import ==========

    async exportData(userId = null) {
        const uid = userId || this.getCurrentUserId();
        return {
            matches: await this.getAllMatches(uid),
            settings: await this.loadSettings(uid),
            physical_measurements: await this.getAllPhysicalMeasurements(uid),
            achievements: await this.getAllAchievements(uid),
            club_history: await this.getAllClubHistory(uid),
            training_camps: await this.getAllTrainingCamps(uid),
            physical_metrics: await this.getAllPhysicalMetrics(uid)
        };
    }

    async importData(data, userId = null) {
        const uid = userId || this.getCurrentUserId();
        
        // Import matches
        if (data.matches && Array.isArray(data.matches)) {
            for (const match of data.matches) {
                match.user_id = uid;
                await this.saveMatch(match);
            }
        }

        // Import settings
        if (data.settings) {
            data.settings.user_id = uid;
            await this.saveSettings(data.settings);
        }

        // Import physical measurements
        if (data.physical_measurements && Array.isArray(data.physical_measurements)) {
            for (const pm of data.physical_measurements) {
                pm.user_id = uid;
                await this.savePhysicalMeasurement(pm);
            }
        }

        // Import achievements
        if (data.achievements && Array.isArray(data.achievements)) {
            for (const ach of data.achievements) {
                ach.user_id = uid;
                await this.saveAchievement(ach);
            }
        }

        // Import club history
        if (data.club_history && Array.isArray(data.club_history)) {
            for (const ch of data.club_history) {
                ch.user_id = uid;
                await this.saveClubHistory(ch);
            }
        }

        // Import training camps
        if (data.training_camps && Array.isArray(data.training_camps)) {
            for (const tc of data.training_camps) {
                tc.user_id = uid;
                await this.saveTrainingCamp(tc);
            }
        }

        // Import physical metrics
        if (data.physical_metrics && Array.isArray(data.physical_metrics)) {
            for (const pm of data.physical_metrics) {
                pm.user_id = uid;
                await this.savePhysicalMetric(pm);
            }
        }

        return true;
    }

    // ========== Statistics ==========

    async getSeasonStats(userId = null, period = 'all_time') {
        const matches = await this.getAllMatches(userId);
        const completedMatches = matches.filter(m => !m.is_fixture);
        
        // Filter by period if needed
        let filteredMatches = completedMatches;
        if (period && period !== 'all_time') {
            filteredMatches = this._filterMatchesByPeriod(completedMatches, period);
        }

        const stats = {
            total_matches: filteredMatches.length,
            wins: 0,
            draws: 0,
            losses: 0,
            goals: 0,
            assists: 0,
            minutes: 0
        };

        for (const match of filteredMatches) {
            if (match.result === 'Win') stats.wins++;
            else if (match.result === 'Draw') stats.draws++;
            else if (match.result === 'Loss') stats.losses++;

            stats.goals += match.brodie_goals || 0;
            stats.assists += match.brodie_assists || 0;
            stats.minutes += match.minutes_played || 0;
        }

        return stats;
    }

    _filterMatchesByPeriod(matches, period) {
        const today = new Date();
        let cutoffDate = null;

        if (period === 'season') {
            // For season, we'd need settings to get season_year
            // For now, return all matches
            return matches;
        } else if (period === '12_months') {
            cutoffDate = new Date(today.getTime() - 365 * 24 * 60 * 60 * 1000);
        } else if (period === '6_months') {
            cutoffDate = new Date(today.getTime() - 180 * 24 * 60 * 60 * 1000);
        } else if (period === '3_months') {
            cutoffDate = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000);
        } else if (period === 'last_month') {
            cutoffDate = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
        } else {
            return matches;
        }

        return matches.filter(match => {
            try {
                // Parse date in "dd MMM yyyy" format
                const dateParts = match.date.split(' ');
                const months = {
                    'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
                    'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
                };
                const day = parseInt(dateParts[0]);
                const month = months[dateParts[1]];
                const year = parseInt(dateParts[2]);
                const matchDate = new Date(year, month, day);
                return matchDate >= cutoffDate;
            } catch (e) {
                return false;
            }
        });
    }

    // ========== Subscription Management ==========
    
    async getSubscription(userId = null) {
        const uid = userId || this.getCurrentUserId();
        if (!uid) {
            return null;
        }
        return await this._getById('subscriptions', uid);
    }

    async saveSubscription(subscription) {
        const userId = this.getCurrentUserId();
        if (!userId) {
            throw new Error('User must be logged in to save subscription');
        }
        // Ensure user_id matches current user
        subscription.user_id = userId;
        if (!subscription.updated_at) {
            subscription.updated_at = new Date().toISOString();
        }
        return await this._save('subscriptions', subscription);
    }

    async deleteSubscription(userId = null) {
        const uid = userId || this.getCurrentUserId();
        if (!uid) {
            throw new Error('User ID required');
        }
        return await this._delete('subscriptions', uid);
    }
}

// Create global instance
const clientStorage = new ClientStorage();

// Initialize on load
clientStorage.init().catch(err => {
    console.error('Failed to initialize IndexedDB:', err);
});

