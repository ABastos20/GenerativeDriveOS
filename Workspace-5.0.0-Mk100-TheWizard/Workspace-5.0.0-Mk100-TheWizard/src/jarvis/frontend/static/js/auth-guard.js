/**
 * JARVIS Auth Guard - Keycloak Authentication Layer
 * 
 * Story 11-1: Sovereign Identity
 * 
 * Uses check-sso to detect existing session, redirects to /login if needed.
 */
(function() {
    'use strict';

    const KC_CONFIG = {
        url: 'http://localhost:8081',
        realm: 'jarvis',
        clientId: 'jarvis-ui'
    };

    // Public API
    window.JarvisAuth = {
        keycloak: null,
        initialized: false,
        token: null,
        user: null,
        _initPromise: null,

        /**
         * Initialize Keycloak with check-sso (non-blocking)
         */
        async init() {
            if (this._initPromise) return this._initPromise;
            if (this.initialized) return this.keycloak?.authenticated || false;

            this._initPromise = this._doInit();
            return this._initPromise;
        },

        async _doInit() {
            if (typeof Keycloak === 'undefined') {
                console.error('[AuthGuard] Keycloak adapter not loaded!');
                return false;
            }

            try {
                this.keycloak = new Keycloak(KC_CONFIG);

                // check-sso: checks for existing session without forcing login
                const authenticated = await this.keycloak.init({
                    onLoad: 'check-sso',
                    checkLoginIframe: false,
                    silentCheckSsoFallback: false,
                    enableLogging: true
                });

                this.initialized = true;

                if (authenticated) {
                    this.token = this.keycloak.token;
                    this.user = this._parseUser();
                    console.log('[AuthGuard] Authenticated as:', this.user?.username);
                    this._setupTokenRefresh();
                    this._updateUI();
                    return true;
                } else {
                    console.log('[AuthGuard] Not authenticated');
                    return false;
                }
            } catch (error) {
                console.error('[AuthGuard] Init failed:', error);
                this.initialized = true; // Mark as initialized to prevent retry loops
                return false;
            }
        },

        /**
         * Force login via Keycloak
         */
        login() {
            if (this.keycloak) {
                this.keycloak.login({
                    redirectUri: window.location.href
                });
            } else {
                window.location.href = '/login';
            }
        },

        /**
         * Check auth and redirect to login if not authenticated
         */
        async requireAuth() {
            const authenticated = await this.init();
            if (!authenticated) {
                console.log('[AuthGuard] Auth required, redirecting to login');
                this.login();
                return false;
            }
            return true;
        },

        _parseUser() {
            if (!this.keycloak?.tokenParsed) return null;
            const t = this.keycloak.tokenParsed;
            return {
                sub: t.sub,
                username: t.preferred_username,
                name: t.name,
                email: t.email,
                roles: t.realm_access?.roles || []
            };
        },

        _setupTokenRefresh() {
            setInterval(async () => {
                if (this.keycloak?.authenticated) {
                    try {
                        const refreshed = await this.keycloak.updateToken(70);
                        if (refreshed) {
                            this.token = this.keycloak.token;
                        }
                    } catch (e) {
                        console.warn('[AuthGuard] Token refresh failed');
                    }
                }
            }, 60000);
        },

        async getAuthHeaders() {
            if (!this.initialized) await this.init();
            
            if (!this.keycloak?.token) return {};

            try {
                await this.keycloak.updateToken(30);
                this.token = this.keycloak.token;
                return { 'Authorization': `Bearer ${this.keycloak.token}` };
            } catch (e) {
                return {};
            }
        },

        getUser() { return this.user; },
        hasRole(role) { return this.user?.roles?.includes(role) || false; },

        logout() {
            if (this.keycloak) {
                this.keycloak.logout({ redirectUri: window.location.origin + '/login' });
            }
        },

        _updateUI() {
            const userDisplay = document.getElementById('user-display');
            const loginBtn = document.getElementById('login-btn');
            const logoutBtn = document.getElementById('logout-btn');

            if (this.keycloak?.authenticated && this.user) {
                if (userDisplay) userDisplay.textContent = this.user.username || 'User';
                if (loginBtn) loginBtn.style.display = 'none';
                if (logoutBtn) {
                    logoutBtn.style.display = 'block';
                    logoutBtn.onclick = () => this.logout();
                }
            } else {
                if (loginBtn) {
                    loginBtn.style.display = 'block';
                    loginBtn.onclick = () => this.login();
                }
                if (logoutBtn) logoutBtn.style.display = 'none';
            }
        }
    };

    // Auto-init but DON'T auto-redirect
    console.log('[AuthGuard] Loading...');
    window.JarvisAuth.init().then(auth => {
        console.log('[AuthGuard] Init complete, authenticated:', auth);
    });
})();
