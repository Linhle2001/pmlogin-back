/**
 * PM Login Client - Smart API adapter for frontend integration
 */

const axios = require('axios');

class PMLoginClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.token = null;
        
        this.client = axios.create({
            baseURL: this.baseUrl,
            timeout: 15000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // Add request interceptor for auth
        this.client.interceptors.request.use((config) => {
            if (this.token) {
                config.headers.Authorization = `Bearer ${this.token}`;
            }
            return config;
        });
    }
    
    setToken(token) {
        this.token = token;
    }
    
    async apiCall(endpoint, data = null) {
        try {
            const response = await this.client.post(endpoint, data);
            return response.data;
        } catch (error) {
            console.error(`API call failed: ${endpoint}`, error);
            return {
                success: false,
                message: error.response?.data?.detail || error.message,
                offline: error.code === 'ECONNREFUSED' || error.response?.status >= 500
            };
        }
    }
    
    /**
     * Smart login - tries original server first, falls back to demo
     */
    async login(email, password, hwid) {
        console.log('🔐 PM Login: Attempting smart login for:', email);
        
        const result = await this.apiCall('/login', { email, password, hwid });
        
        if (result.success && result.data?.access_token) {
            this.setToken(result.data.access_token);
            console.log('✅ PM Login: Login successful');
        } else {
            console.log('❌ PM Login: Login failed -', result.message);
        }
        
        return result;
    }
    
    /**
     * Force demo login
     */
    async demoLogin(email, password, hwid) {
        console.log('🎭 PM Login: Demo login for:', email);
        const result = await this.apiCall('/login-demo', { email, password, hwid });
        
        if (result.success && result.data?.access_token) {
            this.setToken(result.data.access_token);
        }
        
        return result;
    }
    
    async logout() {
        const result = await this.apiCall('/api/auth/logout');
        this.setToken(null);
        return result;
    }
    
    async changePassword(currentPassword, newPassword) {
        return await this.apiCall('/change-password', {
            current_password: currentPassword,
            password: newPassword,
            password_confirmation: newPassword
        });
    }
    
    // User data methods
    async getUserData() {
        return await this.apiCall('/api/user/get-data');
    }
    
    // System methods
    async getSystemInfo() {
        return await this.apiCall('/api/system/info');
    }
    
    async getDbStats() {
        return await this.apiCall('/api/db/stats');
    }
    
    // Proxy methods
    async getAllProxies(options = {}) {
        return await this.apiCall('/api/proxy/get-all', options);
    }
    
    async addProxy(proxyData) {
        return await this.apiCall('/api/proxy/add', proxyData);
    }
    
    async updateProxy(id, proxyData) {
        return await this.apiCall('/api/proxy/update', { id, data: proxyData });
    }
    
    async deleteProxies(ids) {
        return await this.apiCall('/api/proxy/delete-multiple', { ids });
    }
    
    async testProxy(proxyData) {
        return await this.apiCall('/api/proxy/test', proxyData);
    }
    
    async testProxies(proxyIds) {
        return await this.apiCall('/api/proxy/test-multiple', { proxyIds });
    }
    
    async importProxies(proxyText, tags = ['Default']) {
        return await this.apiCall('/api/proxy/import', { proxyText, tags });
    }
    
    async copySelectedProxies(proxyIds) {
        return await this.apiCall('/api/proxy/copy-selected', { proxyIds });
    }
    
    // Profile methods
    async getAllProfiles() {
        return await this.apiCall('/api/profile/get-all');
    }
    
    async createProfile(profileData) {
        return await this.apiCall('/api/create-profile', profileData);
    }
    
    async getProfile(profileId) {
        return await this.apiCall('/api/get-profile', { profileId });
    }
    
    async updateProfile(profileData) {
        return await this.apiCall('/api/update-profile', profileData);
    }
    
    // Database methods
    async dbGetAllProxies(tagId = null) {
        return await this.apiCall('/api/db/proxy/get-all', { tagId });
    }
    
    async dbGetAllProfiles() {
        return await this.apiCall('/api/db/profile/get-all');
    }
    
    async dbGetAllTags() {
        return await this.apiCall('/api/db/tag/get-all');
    }
    
    async dbGetAllGroups() {
        return await this.apiCall('/api/db/group/get-all');
    }
}

// Create singleton instance
const pmClient = new PMLoginClient();

module.exports = pmClient;

// Usage example:
/*
const pmClient = require('./client/pm_client');

// Login
const result = await pmClient.login('user@example.com', 'password', 'hwid');

// Get proxies
const proxies = await pmClient.getAllProxies();

// Create profile
const profile = await pmClient.createProfile({
    name: 'Test Profile',
    platform: 'windows'
});
*/