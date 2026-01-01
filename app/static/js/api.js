/**
 * Client-side API wrapper
 * Mimics the server API but uses client-side storage
 */

// Helper to ensure storage is ready
async function ensureStorageReady() {
    if (!clientStorage.db) {
        await clientStorage.init();
    }
}

// Client-side API that mimics server endpoints
const clientAPI = {
    // ========== Matches ==========
    async getMatches() {
        await ensureStorageReady();
        const matches = await clientStorage.getAllMatches();
        return { success: true, matches: matches };
    },

    async getMatch(matchId) {
        await ensureStorageReady();
        const match = await clientStorage.getMatch(matchId);
        return { success: true, match: match };
    },

    async saveMatch(matchData) {
        await ensureStorageReady();
        const match = await clientStorage.saveMatch(matchData);
        return { success: true, match: match };
    },

    async updateMatch(matchId, matchData) {
        await ensureStorageReady();
        matchData.id = matchId;
        const match = await clientStorage.saveMatch(matchData);
        return { success: true, match: match };
    },

    async deleteMatch(matchId) {
        await ensureStorageReady();
        await clientStorage.deleteMatch(matchId);
        return { success: true };
    },

    // ========== Settings ==========
    async getSettings() {
        await ensureStorageReady();
        const settings = await clientStorage.loadSettings();
        return { success: true, settings: settings };
    },

    async saveSettings(settingsData) {
        await ensureStorageReady();
        const settings = await clientStorage.saveSettings(settingsData);
        return { success: true, settings: settings };
    },

    // ========== Physical Measurements ==========
    async getPhysicalMeasurements() {
        await ensureStorageReady();
        const measurements = await clientStorage.getAllPhysicalMeasurements();
        return { success: true, measurements: measurements };
    },

    async savePhysicalMeasurement(measurementData) {
        await ensureStorageReady();
        const measurement = await clientStorage.savePhysicalMeasurement(measurementData);
        return { success: true, measurement: measurement };
    },

    async updatePhysicalMeasurement(measurementId, measurementData) {
        await ensureStorageReady();
        measurementData.id = measurementId;
        const measurement = await clientStorage.savePhysicalMeasurement(measurementData);
        return { success: true, measurement: measurement };
    },

    async deletePhysicalMeasurement(measurementId) {
        await ensureStorageReady();
        await clientStorage.deletePhysicalMeasurement(measurementId);
        return { success: true };
    },

    // ========== Achievements ==========
    async getAchievements() {
        await ensureStorageReady();
        const achievements = await clientStorage.getAllAchievements();
        return { success: true, achievements: achievements };
    },

    async saveAchievement(achievementData) {
        await ensureStorageReady();
        const achievement = await clientStorage.saveAchievement(achievementData);
        return { success: true, achievement: achievement };
    },

    async updateAchievement(achievementId, achievementData) {
        await ensureStorageReady();
        achievementData.id = achievementId;
        const achievement = await clientStorage.saveAchievement(achievementData);
        return { success: true, achievement: achievement };
    },

    async deleteAchievement(achievementId) {
        await ensureStorageReady();
        await clientStorage.deleteAchievement(achievementId);
        return { success: true };
    },

    // ========== Club History ==========
    async getClubHistory() {
        await ensureStorageReady();
        const history = await clientStorage.getAllClubHistory();
        return { success: true, club_history: history };
    },

    async saveClubHistory(historyData) {
        await ensureStorageReady();
        const history = await clientStorage.saveClubHistory(historyData);
        return { success: true, club_history: history };
    },

    async updateClubHistory(historyId, historyData) {
        await ensureStorageReady();
        historyData.id = historyId;
        const history = await clientStorage.saveClubHistory(historyData);
        return { success: true, club_history: history };
    },

    async deleteClubHistory(historyId) {
        await ensureStorageReady();
        await clientStorage.deleteClubHistory(historyId);
        return { success: true };
    },

    // ========== Training Camps ==========
    async getTrainingCamps() {
        await ensureStorageReady();
        const camps = await clientStorage.getAllTrainingCamps();
        return { success: true, training_camps: camps };
    },

    async saveTrainingCamp(campData) {
        await ensureStorageReady();
        const camp = await clientStorage.saveTrainingCamp(campData);
        return { success: true, training_camp: camp };
    },

    async updateTrainingCamp(campId, campData) {
        await ensureStorageReady();
        campData.id = campId;
        const camp = await clientStorage.saveTrainingCamp(campData);
        return { success: true, training_camp: camp };
    },

    async deleteTrainingCamp(campId) {
        await ensureStorageReady();
        await clientStorage.deleteTrainingCamp(campId);
        return { success: true };
    },

    // ========== Physical Metrics ==========
    async getPhysicalMetrics() {
        await ensureStorageReady();
        const metrics = await clientStorage.getAllPhysicalMetrics();
        return { success: true, physical_metrics: metrics };
    },

    async savePhysicalMetric(metricData) {
        await ensureStorageReady();
        const metric = await clientStorage.savePhysicalMetric(metricData);
        return { success: true, physical_metric: metric };
    },

    async updatePhysicalMetric(metricId, metricData) {
        await ensureStorageReady();
        metricData.id = metricId;
        const metric = await clientStorage.savePhysicalMetric(metricData);
        return { success: true, physical_metric: metric };
    },

    async deletePhysicalMetric(metricId) {
        await ensureStorageReady();
        await clientStorage.deletePhysicalMetric(metricId);
        return { success: true };
    },

    // ========== Statistics ==========
    async getStats(period = 'all_time') {
        await ensureStorageReady();
        const stats = await clientStorage.getSeasonStats(null, period);
        
        // Also calculate category stats
        const matches = await clientStorage.getAllMatches();
        const completedMatches = matches.filter(m => !m.is_fixture);
        let filteredMatches = completedMatches;
        if (period && period !== 'all_time') {
            filteredMatches = clientStorage._filterMatchesByPeriod(completedMatches, period);
        }

        const preSeasonMatches = filteredMatches.filter(m => m.category === 'Pre-Season Friendly');
        const leagueMatches = filteredMatches.filter(m => m.category === 'League');

        const calcStats = (matchList) => ({
            matches: matchList.length,
            goals: matchList.reduce((sum, m) => sum + (m.brodie_goals || 0), 0),
            assists: matchList.reduce((sum, m) => sum + (m.brodie_assists || 0), 0),
            minutes: matchList.reduce((sum, m) => sum + (m.minutes_played || 0), 0)
        });

        return {
            success: true,
            stats: {
                season: stats,
                pre_season: calcStats(preSeasonMatches),
                league: calcStats(leagueMatches)
            },
            period: period
        };
    },

    // ========== Export/Import ==========
    async exportData() {
        await ensureStorageReady();
        const data = await clientStorage.exportData();
        
        // Create ZIP file (using JSZip library - we'll need to include it)
        if (typeof JSZip !== 'undefined') {
            const zip = new JSZip();
            zip.file('matches.json', JSON.stringify(data.matches, null, 2));
            zip.file('settings.json', JSON.stringify(data.settings, null, 2));
            zip.file('physical_measurements.json', JSON.stringify(data.physical_measurements, null, 2));
            zip.file('achievements.json', JSON.stringify(data.achievements, null, 2));
            zip.file('club_history.json', JSON.stringify(data.club_history, null, 2));
            zip.file('training_camps.json', JSON.stringify(data.training_camps, null, 2));
            zip.file('physical_metrics.json', JSON.stringify(data.physical_metrics, null, 2));
            
            const blob = await zip.generateAsync({ type: 'blob' });
            return { success: true, blob: blob };
        } else {
            // Fallback: return JSON
            return { success: true, data: data };
        }
    },

    async importData(file) {
        await ensureStorageReady();
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = async (e) => {
                try {
                    let data;
                    if (file.name.endsWith('.zip')) {
                        // Handle ZIP import (would need JSZip)
                        reject(new Error('ZIP import requires JSZip library'));
                    } else {
                        data = JSON.parse(e.target.result);
                        await clientStorage.importData(data);
                        resolve({ success: true });
                    }
                } catch (err) {
                    reject(err);
                }
            };
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }
};

// Override the global apiCall function to use client storage
const originalApiCall = window.apiCall;
window.apiCall = async function(url, options = {}) {
    // Check if this is a client-side route
    // Note: /api/settings GET and /api/achievements should go to server to get latest data
    const clientRoutes = [
        '/matches', '/api/matches', '/api/physical-measurements',
        '/api/club-history', '/api/training-camps',
        '/api/physical-metrics', '/stats'
    ];

    const isClientRoute = clientRoutes.some(route => url.startsWith(route));
    const method = options.method || 'GET';
    
    // Settings GET should always go to server to ensure we have latest data
    if (url === '/api/settings' && method === 'GET') {
        if (originalApiCall) {
            return await originalApiCall(url, options);
        }
    }
    
    if (isClientRoute && !url.startsWith('/pdf') && !url.startsWith('/scout-pdf') && !url.startsWith('/export') && !url.startsWith('/import')) {
        // Use client-side API
        const body = options.body ? JSON.parse(options.body) : {};
        
        try {
            if (url.startsWith('/matches/') && method === 'GET') {
                const matchId = url.split('/matches/')[1];
                return await clientAPI.getMatch(matchId);
            } else if (url.startsWith('/matches/') && method === 'PUT') {
                const matchId = url.split('/matches/')[1];
                // PUT should go to server first for validation, then sync to client
                try {
                    // Security: Get CSRF token for state-changing request
                    const csrfToken = await csrfManager.getToken();
                    const headers = {
                        'Content-Type': 'application/json'
                    };
                    if (csrfToken) {
                        headers['X-CSRFToken'] = csrfToken;
                    }
                    
                    const response = await fetch(url, {
                        method: 'PUT',
                        headers: headers,
                        credentials: 'include',
                        body: options.body || JSON.stringify(body)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        // Reload match from server to get updated data, then sync to client
                        try {
                            const getResponse = await fetch(`/matches/${matchId}`, {
                                method: 'GET',
                                credentials: 'include'
                            });
                            const getResult = await getResponse.json();
                            if (getResult.success && getResult.match) {
                                await clientAPI.updateMatch(matchId, getResult.match);
                            }
                        } catch (e) {
                            console.warn('Failed to sync match to client storage:', e);
                        }
                    }
                    
                    if (!response.ok) {
                        throw new Error(result.errors ? result.errors.join(', ') : 'Request failed');
                    }
                    
                    return result;
                } catch (error) {
                    console.error('Error calling server API:', error);
                    throw error;
                }
            } else if (url.startsWith('/matches/') && method === 'DELETE') {
                const matchId = url.split('/matches/')[1];
                // DELETE should go to server first, then sync to client
                try {
                    // Security: Get CSRF token for state-changing request
                    const csrfToken = await csrfManager.getToken();
                    const headers = {};
                    if (csrfToken) {
                        headers['X-CSRFToken'] = csrfToken;
                    }
                    
                    const response = await fetch(url, {
                        method: 'DELETE',
                        headers: headers,
                        credentials: 'include'
                    });
                    
                    const result = await response.json();
                    
                    // Also delete from client storage
                    try {
                        await clientAPI.deleteMatch(matchId);
                    } catch (e) {
                        console.warn('Failed to delete match from client storage:', e);
                    }
                    
                    if (!response.ok) {
                        // If server says not found, but we deleted from client, that's okay
                        if (response.status === 404) {
                            return { success: true, message: 'Match deleted from client storage' };
                        }
                        throw new Error(result.errors ? result.errors.join(', ') : 'Request failed');
                    }
                    
                    return result;
                } catch (error) {
                    console.error('Error calling server API:', error);
                    // Even if server fails, try to delete from client
                    try {
                        await clientAPI.deleteMatch(matchId);
                        return { success: true, message: 'Match deleted from client storage (server delete failed)' };
                    } catch (e) {
                        throw error; // Re-throw original error if client delete also fails
                    }
                }
            } else if (url === '/matches' && method === 'POST') {
                // POST should go to server first for validation and subscription checks, then sync to client
                // Use fetch directly to ensure it goes to server
                try {
                    // Security: Get CSRF token for state-changing request
                    const csrfToken = await csrfManager.getToken();
                    const headers = {
                        'Content-Type': 'application/json'
                    };
                    if (csrfToken) {
                        headers['X-CSRFToken'] = csrfToken;
                    }
                    
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: headers,
                        credentials: 'include',
                        body: options.body || JSON.stringify(body)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        // If match object is returned, sync it; otherwise reload to get it
                        if (result.match) {
                            try {
                                await clientAPI.saveMatch(result.match);
                            } catch (e) {
                                console.warn('Failed to sync match to client storage:', e);
                            }
                        } else if (result.match_id) {
                            // Reload match from server to get full data
                            try {
                                const getResponse = await fetch(`/matches/${result.match_id}`, {
                                method: 'GET',
                                credentials: 'include'
                            });
                                const getResult = await getResponse.json();
                                if (getResult.success && getResult.match) {
                                    await clientAPI.saveMatch(getResult.match);
                                }
                            } catch (e) {
                                console.warn('Failed to sync match to client storage:', e);
                            }
                        }
                    }
                    
                    if (!response.ok) {
                        throw new Error(result.errors ? result.errors.join(', ') : 'Request failed');
                    }
                    
                    return result;
                } catch (error) {
                    console.error('Error calling server API:', error);
                    throw error;
                }
            } else if (url === '/matches' && method === 'GET') {
                return await clientAPI.getMatches();
            } else if (url === '/settings' && method === 'GET') {
                return await clientAPI.getSettings();
            } else if (url === '/settings' && method === 'POST') {
                // Settings POST should go to server to ensure PHV calculation works
                // Then sync to client storage
                if (originalApiCall) {
                    const result = await originalApiCall(url, options);
                    // Also save to client storage for local access
                    if (result.success && body) {
                        try {
                            // Parse the body to get the settings data
                            const settingsData = typeof body === 'string' ? JSON.parse(body) : body;
                            await clientAPI.saveSettings(settingsData);
                        } catch (e) {
                            console.warn('Failed to sync settings to client storage:', e);
                        }
                    }
                    return result;
                }
                return await clientAPI.saveSettings(body);
            } else if (url === '/api/physical-measurements' && method === 'GET') {
                // GET should go to server first, then sync to client storage
                if (originalApiCall) {
                    const result = await originalApiCall(url, options);
                    if (result.success && result.measurements) {
                        // Sync to client storage
                        for (const m of result.measurements) {
                            try {
                                await clientAPI.savePhysicalMeasurement(m);
                            } catch (e) {
                                console.warn('Failed to sync measurement to client storage:', e);
                            }
                        }
                    }
                    return result;
                }
                return await clientAPI.getPhysicalMeasurements();
            } else if (url === '/api/physical-measurements' && method === 'POST') {
                // POST should go to server first, then sync to client storage
                if (originalApiCall) {
                    const result = await originalApiCall(url, options);
                    if (result.success) {
                        try {
                            // Use the measurement from server response (has converted date format)
                            if (result.measurement) {
                                await clientAPI.savePhysicalMeasurement(result.measurement);
                            } else if (result.measurement_id) {
                                // If no measurement in response, reload all to get the new one with correct format
                                const getAllResult = await originalApiCall('/api/physical-measurements', {method: 'GET'});
                                if (getAllResult.success && getAllResult.measurements) {
                                    // Sync all measurements to client storage
                                    for (const m of getAllResult.measurements) {
                                        await clientAPI.savePhysicalMeasurement(m);
                                    }
                                }
                            }
                        } catch (e) {
                            console.warn('Failed to sync measurement to client storage:', e);
                        }
                    }
                    return result;
                }
                return await clientAPI.savePhysicalMeasurement(body);
            } else if (url.startsWith('/api/physical-measurements/') && method === 'PUT') {
                const id = url.split('/api/physical-measurements/')[1];
                // PUT should go to server first, then sync to client storage
                if (originalApiCall) {
                    const result = await originalApiCall(url, options);
                    if (result.success) {
                        try {
                            // Use the measurement from server response (has converted date format)
                            if (result.measurement) {
                                await clientAPI.savePhysicalMeasurement(result.measurement);
                            } else {
                                // Fallback: reload all measurements
                                const getAllResult = await originalApiCall('/api/physical-measurements', {method: 'GET'});
                                if (getAllResult.success && getAllResult.measurements) {
                                    for (const m of getAllResult.measurements) {
                                        await clientAPI.savePhysicalMeasurement(m);
                                    }
                                }
                            }
                        } catch (e) {
                            console.warn('Failed to sync measurement to client storage:', e);
                        }
                    }
                    return result;
                }
                return await clientAPI.updatePhysicalMeasurement(id, body);
            } else if (url.startsWith('/api/physical-measurements/') && method === 'DELETE') {
                const id = url.split('/api/physical-measurements/')[1];
                // DELETE should go to server first, then sync to client storage
                if (originalApiCall) {
                    const result = await originalApiCall(url, options);
                    if (result.success) {
                        try {
                            await clientAPI.deletePhysicalMeasurement(id);
                        } catch (e) {
                            console.warn('Failed to sync measurement deletion to client storage:', e);
                        }
                    }
                    return result;
                }
                return await clientAPI.deletePhysicalMeasurement(id);
            } else if (url === '/api/achievements' && method === 'GET') {
                // GET should go to server first, then sync to client storage
                if (originalApiCall) {
                    const result = await originalApiCall(url, options);
                    if (result.success && result.achievements) {
                        // Sync to client storage
                        for (const ach of result.achievements) {
                            try {
                                await clientAPI.saveAchievement(ach);
                            } catch (e) {
                                console.warn('Failed to sync achievement to client storage:', e);
                            }
                        }
                    }
                    return result;
                }
                return await clientAPI.getAchievements();
            } else if (url === '/api/achievements' && method === 'POST') {
                // POST should go to server first, then sync to client storage
                if (originalApiCall) {
                    const result = await originalApiCall(url, options);
                    if (result.success && body) {
                        try {
                            const achievementData = typeof body === 'string' ? JSON.parse(body) : body;
                            // Add the ID from the result if available
                            if (result.achievement_id) {
                                achievementData.id = result.achievement_id;
                            }
                            await clientAPI.saveAchievement(achievementData);
                        } catch (e) {
                            console.warn('Failed to sync achievement to client storage:', e);
                        }
                    }
                    return result;
                }
                return await clientAPI.saveAchievement(body);
            } else if (url.startsWith('/api/achievements/') && method === 'PUT') {
                const id = url.split('/api/achievements/')[1];
                // PUT should go to server first, then sync to client storage
                if (originalApiCall) {
                    const result = await originalApiCall(url, options);
                    if (result.success && body) {
                        try {
                            const achievementData = typeof body === 'string' ? JSON.parse(body) : body;
                            achievementData.id = id;
                            await clientAPI.saveAchievement(achievementData);
                        } catch (e) {
                            console.warn('Failed to sync achievement to client storage:', e);
                        }
                    }
                    return result;
                }
                return await clientAPI.updateAchievement(id, body);
            } else if (url.startsWith('/api/achievements/') && method === 'DELETE') {
                const id = url.split('/api/achievements/')[1];
                // DELETE should go to server first, then sync to client storage
                if (originalApiCall) {
                    const result = await originalApiCall(url, options);
                    if (result.success) {
                        try {
                            await clientAPI.deleteAchievement(id);
                        } catch (e) {
                            console.warn('Failed to sync achievement deletion to client storage:', e);
                        }
                    }
                    return result;
                }
                return await clientAPI.deleteAchievement(id);
            } else if (url === '/api/club-history' && method === 'GET') {
                return await clientAPI.getClubHistory();
            } else if (url === '/api/club-history' && method === 'POST') {
                return await clientAPI.saveClubHistory(body);
            } else if (url.startsWith('/api/club-history/') && method === 'PUT') {
                const id = url.split('/api/club-history/')[1];
                return await clientAPI.updateClubHistory(id, body);
            } else if (url.startsWith('/api/club-history/') && method === 'DELETE') {
                const id = url.split('/api/club-history/')[1];
                return await clientAPI.deleteClubHistory(id);
            } else if (url === '/api/training-camps' && method === 'GET') {
                return await clientAPI.getTrainingCamps();
            } else if (url === '/api/training-camps' && method === 'POST') {
                return await clientAPI.saveTrainingCamp(body);
            } else if (url.startsWith('/api/training-camps/') && method === 'PUT') {
                const id = url.split('/api/training-camps/')[1];
                return await clientAPI.updateTrainingCamp(id, body);
            } else if (url.startsWith('/api/training-camps/') && method === 'DELETE') {
                const id = url.split('/api/training-camps/')[1];
                return await clientAPI.deleteTrainingCamp(id);
            } else if (url === '/api/physical-metrics' && method === 'GET') {
                return await clientAPI.getPhysicalMetrics();
            } else if (url === '/api/physical-metrics' && method === 'POST') {
                return await clientAPI.savePhysicalMetric(body);
            } else if (url.startsWith('/api/physical-metrics/') && method === 'PUT') {
                const id = url.split('/api/physical-metrics/')[1];
                return await clientAPI.updatePhysicalMetric(id, body);
            } else if (url.startsWith('/api/physical-metrics/') && method === 'DELETE') {
                const id = url.split('/api/physical-metrics/')[1];
                return await clientAPI.deletePhysicalMetric(id);
            } else if (url.startsWith('/stats')) {
                const params = new URLSearchParams(url.split('?')[1] || '');
                const period = params.get('period') || 'all_time';
                return await clientAPI.getStats(period);
            }
            
            // Fallback to original API call for routes not handled client-side
            if (originalApiCall) {
                return await originalApiCall(url, options);
            }
            throw new Error('Route not handled');
        } catch (error) {
            console.error('Client API Error:', error);
            throw error;
        }
    } else {
        // Use server API (for PDF generation, export, etc.)
        if (originalApiCall) {
            return await originalApiCall(url, options);
        }
        // Fallback to fetch - ensure credentials included
        const fetchOptions = {
            ...options,
            credentials: 'include'
        };
        const response = await fetch(url, fetchOptions);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.errors ? data.errors.join(', ') : 'Request failed');
        }
        return data;
    }
};

