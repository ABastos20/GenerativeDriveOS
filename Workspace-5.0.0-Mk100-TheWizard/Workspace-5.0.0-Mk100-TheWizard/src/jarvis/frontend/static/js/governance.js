/**
 * Governance Dashboard - Real-time Governance Control Plane
 * Connects to WebSocket for live events, fetches API data, renders UI
 */

(function() {
  'use strict';

  // === Configuration ===
  const API_BASE = '/api/governance';
  const WS_URL = `ws://${window.location.host}/ws/governance/events`;
  const KC_CONFIG = { url: 'http://localhost:8081', realm: 'jarvis', clientId: 'jarvis-ui' };
  
  // === State ===
  let ws = null;
  let keycloak = null;
  let reconnectAttempts = 0;
  const MAX_RECONNECT_ATTEMPTS = 5;
  const events = [];
  const MAX_EVENTS = 50;

  // === DOM Elements ===
  const elements = {
    // Sidebar stats
    totalUsers: document.getElementById('total-users'),
    activeProposals: document.getElementById('active-proposals'),
    constitutionVersion: document.getElementById('constitution-version'),
    systemHealth: document.getElementById('system-health'),
    totalWeight: document.getElementById('total-weight'),
    pendingEscalations: document.getElementById('pending-escalations'),
    wsStatus: document.getElementById('ws-status'),
    
    // Constitution params
    sybilThreshold: document.getElementById('sybil-threshold'),
    minorityFloor: document.getElementById('minority-floor'),
    antiElite: document.getElementById('anti-elite'),
    maxDrift: document.getElementById('max-drift'),
    eternityList: document.getElementById('eternity-list'),
    
    // Trust stats
    medianWeight: document.getElementById('median-weight'),
    eliteCap: document.getElementById('elite-cap'),
    trustChart: document.getElementById('trust-chart'),
    
    // Panels
    proposalsList: document.getElementById('proposals-list'),
    eventsList: document.getElementById('events-list'),
    legitimacyChecks: document.getElementById('legitimacy-checks'),
    
    // Buttons
    refreshProposals: document.getElementById('refresh-proposals'),
    viewHistory: document.getElementById('view-history'),
    exportTrust: document.getElementById('export-trust'),
    clearEvents: document.getElementById('clear-events'),
    
    // Modal
    modal: document.getElementById('proposal-modal'),
    modalTitle: document.getElementById('modal-title'),
    modalBody: document.getElementById('modal-body'),
    closeModal: document.getElementById('close-modal'),
    
    // Auth
    userDisplay: document.getElementById('user-display'),
    loginBtn: document.getElementById('login-btn'),
    logoutBtn: document.getElementById('logout-btn'),
    navLinks: document.querySelectorAll('.nav-link') // For RBAC
  };

  // === API Functions ===
  // DEBUG_USER_ID removed - auth is now mandatory

  async function fetchJSON(endpoint, options = {}) {
    try {
      // Identity Routing Fix (OIDC + Legacy Fallback)
      const headers = {
        'Content-Type': 'application/json',
        ...options.headers
      };

      if (keycloak && keycloak.token) {
         try {
             await keycloak.updateToken(30);
             headers['Authorization'] = `Bearer ${keycloak.token}`;
         } catch (e) {
             console.warn('Failed to refresh token', e);
             keycloak.login();
         }
      } else {
         // No token available - this shouldn't happen if login-required is working
         console.warn('[Auth] No token available, requests may fail');
      }

      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      return null;
    }
  }

  async function loadDashboardData() {
    const data = await fetchJSON('/dashboard/system');
    if (!data) return;

    // Update sidebar stats
    // Fix: Unwrap governance_system for AC3
    const sys = data.governance_system || {};
    elements.totalUsers.textContent = sys.total_users ?? '--';
    elements.activeProposals.textContent = data.proposals?.open ?? '--';
    elements.pendingEscalations.textContent = data.escalations?.pending ?? 0;
    elements.totalWeight.textContent = (sys.total_weight ?? 0).toFixed(2);
    
    // System health indicator
    const health = data.system_health ?? 'healthy';
    elements.systemHealth.textContent = '●';
    elements.systemHealth.className = `stat-value health-indicator ${health}`;
  }

  async function loadConstitution() {
    const data = await fetchJSON('/constitution');
    if (!data) return;

    elements.constitutionVersion.textContent = data.version ?? 1;
    elements.sybilThreshold.textContent = data.sybil_threshold ?? '--';
    elements.minorityFloor.textContent = data.minority_floor ?? '--';
    elements.antiElite.textContent = `${data.anti_elite_multiplier ?? 3}× median`;
    elements.maxDrift.textContent = data.max_legitimacy_drift ?? '--';

    // Eternity clauses
    const clauses = data.eternity_clauses ?? [];
    elements.eternityList.innerHTML = clauses.length 
      ? clauses.map(c => `<li>${escapeHtml(c)}</li>`).join('')
      : '<li>No eternity clauses defined</li>';
  }

  async function loadProposals() {
    elements.proposalsList.innerHTML = '<div class="loading">Loading proposals...</div>';
    
    const data = await fetchJSON('/dashboard/proposals');
    if (!data || !data.proposals) {
      elements.proposalsList.innerHTML = '<div class="loading">No proposals found</div>';
      return;
    }

    if (data.proposals.length === 0) {
      elements.proposalsList.innerHTML = '<div class="loading">No active proposals</div>';
      return;
    }

    elements.proposalsList.innerHTML = data.proposals.map(p => `
      <div class="proposal-item" data-id="${p.id}">
        <div class="proposal-title">${escapeHtml(p.title)}</div>
        <div class="proposal-meta">
          <span class="proposal-status ${p.status}">${p.status}</span>
          <span>👍 ${p.yes_votes ?? 0} / 👎 ${p.no_votes ?? 0}</span>
          <span>⚖️ ${(p.current_weight ?? 0).toFixed(2)} / ${(p.required_quorum ?? 0).toFixed(2)}</span>
        </div>
        <div class="quorum-bar">
          <div class="quorum-fill" style="width: ${Math.min(100, ((p.current_weight ?? 0) / (p.required_quorum || 1)) * 100)}%"></div>
        </div>
      </div>
    `).join('');

    // Add click handlers
    document.querySelectorAll('.proposal-item').forEach(el => {
      el.addEventListener('click', () => showProposalDetail(el.dataset.id));
    });
  }

  async function loadLegitimacy() {
    elements.legitimacyChecks.innerHTML = '<div class="loading">Loading legitimacy data...</div>';
    
    const data = await fetchJSON('/legitimacy/system');
    if (!data) {
      elements.legitimacyChecks.innerHTML = '<div class="loading">Unable to load legitimacy data</div>';
      return;
    }

    const checks = [
      { label: 'Trust Conservation', value: data.legitimacy_conserved ? 'Conserved' : 'Drift Detected', pass: data.legitimacy_conserved },
      { label: 'Active Violations', value: (data.violation_count ?? 0) === 0 ? 'None' : `${data.violation_count} violations`, pass: (data.violation_count ?? 0) === 0 },
      { label: 'Constitution Valid', value: data.constitution_valid ? 'Valid' : 'Invalid', pass: data.constitution_valid }
    ];

    elements.legitimacyChecks.innerHTML = checks.map(c => `
      <div class="legitimacy-check">
        <div class="legitimacy-icon ${c.pass ? 'pass' : 'fail'}">${c.pass ? '✓' : '✗'}</div>
        <div class="legitimacy-info">
          <div class="legitimacy-label">${c.label}</div>
          <div class="legitimacy-value">${c.value}</div>
        </div>
      </div>
    `).join('');
  }

  async function showProposalDetail(proposalId) {
    elements.modal.style.display = 'flex';
    elements.modalBody.innerHTML = '<div class="loading">Loading proposal details...</div>';

    const data = await fetchJSON(`/proposals/${proposalId}`);
    if (!data) {
      elements.modalBody.innerHTML = '<div class="loading">Unable to load proposal</div>';
      return;
    }

    elements.modalTitle.textContent = data.title ?? 'Proposal Details';
    elements.modalBody.innerHTML = `
      <div class="proposal-detail">
        <div class="param-row">
          <span class="param-label">Status</span>
          <span class="param-value"><span class="proposal-status ${data.status}">${data.status}</span></span>
        </div>
        <div class="param-row">
          <span class="param-label">Domain</span>
          <span class="param-value">${escapeHtml(data.domain ?? 'general')}</span>
        </div>
        <div class="param-row">
          <span class="param-label">Proposer</span>
          <span class="param-value">${escapeHtml(data.proposer?.display_name ?? 'Unknown')}</span>
        </div>
        <div class="param-row">
          <span class="param-label">Votes</span>
          <span class="param-value">👍 ${data.yes_votes ?? 0} / 👎 ${data.no_votes ?? 0} / 🤷 ${data.abstain_votes ?? 0}</span>
        </div>
        <div class="param-row">
          <span class="param-label">Weight</span>
          <span class="param-value">${(data.weighted_yes ?? 0).toFixed(2)} / ${(data.required_quorum ?? 0).toFixed(2)}</span>
        </div>
        <div style="margin-top: 16px; padding: 12px; background: rgba(15,23,42,0.5); border-radius: 8px;">
          <div class="param-label" style="margin-bottom: 8px;">Description</div>
          <div style="font-size: 13px; color: var(--text-main); line-height: 1.5;">
            ${escapeHtml(data.description ?? 'No description provided.')}
          </div>
        </div>
      </div>
    `;
  }

  // === WebSocket Functions ===
  function connectWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) return;

    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('[WS] Connected to governance events');
      reconnectAttempts = 0;
      updateConnectionStatus(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleEvent(data);
      } catch (e) {
        console.error('[WS] Parse error:', e);
      }
    };

    ws.onclose = () => {
      console.log('[WS] Disconnected');
      updateConnectionStatus(false);
      scheduleReconnect();
    };

    ws.onerror = (error) => {
      console.error('[WS] Error:', error);
    };
  }

  function scheduleReconnect() {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.log('[WS] Max reconnect attempts reached');
      return;
    }
    reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
    console.log(`[WS] Reconnecting in ${delay}ms...`);
    setTimeout(connectWebSocket, delay);
  }

  function updateConnectionStatus(connected) {
    const dot = elements.wsStatus.querySelector('.status-dot');
    const text = elements.wsStatus.querySelector('span:last-child');
    
    if (connected) {
      dot.className = 'status-dot connected';
      text.textContent = 'Connected';
    } else {
      dot.className = 'status-dot disconnected';
      text.textContent = 'Disconnected';
    }
  }

  function handleEvent(data) {
    if (data.type === 'heartbeat') return;

    const eventConfig = {
      'proposal_opened': { icon: '📋', class: 'proposal', text: `New proposal: ${data.title ?? data.proposal_id}` },
      'vote_cast': { icon: '🗳️', class: 'vote', text: `Vote cast on ${data.proposal_id?.slice(0, 8) ?? 'proposal'}` },
      'quorum_reached': { icon: '🎯', class: 'quorum', text: `Quorum reached on ${data.proposal_id?.slice(0, 8) ?? 'proposal'}` },
      'proposal_resolved': { icon: '✅', class: 'resolved', text: `Proposal ${data.outcome ?? 'resolved'}: ${data.proposal_id?.slice(0, 8) ?? 'proposal'}` },
      'trust_updated': { icon: '📊', class: 'vote', text: `Trust updated for ${data.user_id?.slice(0, 8) ?? 'user'}` },
      'constitution_amended': { icon: '📜', class: 'proposal', text: 'Constitution amended' },
      'legitimacy_violation': { icon: '⚠️', class: 'violation', text: data.message ?? 'Legitimacy violation detected' },
      'escalation_triggered': { icon: '🚨', class: 'violation', text: data.reason ?? 'Escalation triggered' }
    };

    const config = eventConfig[data.type] ?? { icon: 'ℹ️', class: 'info', text: data.type };

    addEventToList({
      icon: config.icon,
      class: config.class,
      text: config.text,
      time: new Date().toLocaleTimeString()
    });

    // Refresh relevant data on certain events
    if (['proposal_opened', 'proposal_resolved', 'vote_cast', 'quorum_reached'].includes(data.type)) {
      loadProposals();
      loadDashboardData();
    }
    if (data.type === 'constitution_amended') {
      loadConstitution();
    }
    if (['legitimacy_violation', 'trust_updated'].includes(data.type)) {
      loadLegitimacy();
    }
  }

  function addEventToList(event) {
    events.unshift(event);
    if (events.length > MAX_EVENTS) events.pop();
    renderEvents();
  }

  function renderEvents() {
    if (events.length === 0) {
      elements.eventsList.innerHTML = `
        <div class="event-item info">
          <span class="event-icon">ℹ️</span>
          <span class="event-text">Waiting for events...</span>
          <span class="event-time">--</span>
        </div>
      `;
      return;
    }

    elements.eventsList.innerHTML = events.map(e => `
      <div class="event-item ${e.class}">
        <span class="event-icon">${e.icon}</span>
        <span class="event-text">${escapeHtml(e.text)}</span>
        <span class="event-time">${e.time}</span>
      </div>
    `).join('');
  }

  // === Export Functions ===
  async function exportTrustData() {
    try {
      const response = await fetch(`${API_BASE}/export/trust?format=csv`);
      if (!response.ok) throw new Error('Export failed');
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `trust_export_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export error:', error);
      alert('Failed to export trust data');
    }
  }

  // === AC7: Vote History ===
  async function loadVoteHistory() {
    const list = document.getElementById('vote-history-list');
    if (!list) return;
    
    list.innerHTML = '<div class="loading">Loading vote history...</div>';
    
    const data = await fetchJSON('/votes/history');
    if (!data || !data.votes || data.votes.length === 0) {
      list.innerHTML = '<div class="loading">No votes found</div>';
      return;
    }
    
    list.innerHTML = data.votes.map(v => `
      <div class="event-item vote">
        <span class="event-icon">${v.vote_type === 'yes' ? '👍' : v.vote_type === 'no' ? '👎' : '🤷'}</span>
        <span class="event-text">${escapeHtml(v.proposal_title || v.proposal_id.slice(0, 8))}</span>
        <span class="event-time">${v.created_at ? new Date(v.created_at).toLocaleDateString() : '--'}</span>
      </div>
    `).join('');
  }

  // === AC8: Quick Vote ===
  async function quickVote(proposalId, voteType) {
    try {
      const response = await fetch(`${API_BASE}/proposals/${proposalId}/quick-vote?vote_type=${voteType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        const error = await response.json();
        alert(`Vote failed: ${error.detail || 'Unknown error'}`);
        return false;
      }
      
      const result = await response.json();
      if (result.success) {
        addEventToList({
          icon: '🗳️',
          class: 'vote',
          text: `Your ${voteType} vote recorded`,
          time: new Date().toLocaleTimeString()
        });
        loadProposals();
        return true;
      }
    } catch (error) {
      console.error('Quick vote error:', error);
      alert('Failed to cast vote');
    }
    return false;
  }

  // === AC11: Trust Trend Chart ===
  let trustTrendChart = null;
  
  async function loadTrustTrend() {
    const canvas = document.getElementById('trust-trend-chart');
    if (!canvas) return;
    
    const data = await fetchJSON('/trust-trend?days=30');
    if (!data || !data.trend || data.trend.length === 0) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    if (trustTrendChart) {
      trustTrendChart.destroy();
    }
    
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
      console.warn('Chart.js not loaded');
      return;
    }
    
    trustTrendChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.trend.map(t => t.date),
        datasets: [{
          label: 'Trust Updates',
          data: data.trend.map(t => t.updates),
          borderColor: '#00d4ff',
          backgroundColor: 'rgba(0, 212, 255, 0.1)',
          fill: true,
          tension: 0.4,
          borderWidth: 2
        }, {
          label: 'Avg Delta',
          data: data.trend.map(t => t.avg_delta * 100), // Scale for visibility
          borderColor: '#00ff88',
          borderDash: [5, 5],
          tension: 0.4,
          borderWidth: 1.5
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: '#94a3b8', font: { size: 10 } }
          }
        },
        scales: {
          x: { ticks: { color: '#94a3b8', maxTicksLimit: 7 }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
        }
      }
    });
  }

  // === AC12: Expertise Claims ===
  async function loadExpertiseClaims() {
    const list = document.getElementById('expertise-list');
    if (!list) return;
    
    list.innerHTML = '<div class="loading">Loading expertise claims...</div>';
    
    const data = await fetchJSON('/expertise/claims');
    if (!data || !data.claims || data.claims.length === 0) {
      list.innerHTML = '<div class="loading">No expertise claims</div>';
      return;
    }
    
    list.innerHTML = data.claims.map(c => `
      <div class="event-item vote">
        <span class="event-icon">🎓</span>
        <span class="event-text">${escapeHtml(c.user_name)}: ${escapeHtml(c.domain)}</span>
        <span class="event-time">${(c.expertise_score * 100).toFixed(0)}%</span>
      </div>
    `).join('');
  }

  async function submitExpertiseClaim() {
    const domainSelect = document.getElementById('claim-domain');
    const domain = domainSelect?.value;
    
    if (!domain) {
      alert('Please select a domain');
      return;
    }
    
    try {
      const response = await fetch(`${API_BASE}/expertise/claim?domain=${encodeURIComponent(domain)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        const error = await response.json();
        alert(`Claim failed: ${error.detail || 'Unknown error'}`);
        return;
      }
      
      const result = await response.json();
      if (result.success) {
        addEventToList({
          icon: '🎓',
          class: 'proposal',
          text: `Expertise claim ${result.action}: ${domain}`,
          time: new Date().toLocaleTimeString()
        });
        document.getElementById('claim-form').style.display = 'none';
        loadExpertiseClaims();
      }
    } catch (error) {
      console.error('Expertise claim error:', error);
      alert('Failed to submit claim');
    }
  }

  // === AC16: Violation Log ===
  async function loadViolations() {
    const list = document.getElementById('violations-list');
    if (!list) return;
    
    list.innerHTML = '<div class="loading">Loading violations...</div>';
    
    const data = await fetchJSON('/violations');
    if (!data || !data.violations || data.violations.length === 0) {
      list.innerHTML = '<div class="event-item info"><span class="event-icon">✓</span><span class="event-text">No constitutional violations</span></div>';
      return;
    }
    
    list.innerHTML = data.violations.map(v => `
      <div class="event-item violation">
        <span class="event-icon">🚫</span>
        <span class="event-text">${escapeHtml(v.proposal_title || v.violation_type)}</span>
        <span class="event-time">${v.created_at ? new Date(v.created_at).toLocaleDateString() : '--'}</span>
      </div>
    `).join('');
  }

  // === Updated Proposal Modal with Quick Vote ===
  async function showProposalDetail(proposalId) {
    elements.modal.style.display = 'flex';
    elements.modalBody.innerHTML = '<div class="loading">Loading proposal details...</div>';

    const data = await fetchJSON(`/proposals/${proposalId}`);
    if (!data) {
      elements.modalBody.innerHTML = '<div class="loading">Unable to load proposal</div>';
      return;
    }

    const isVotable = data.status.toLowerCase() === 'open' || data.status.toLowerCase() === 'voting';

    elements.modalTitle.textContent = data.title ?? 'Proposal Details';
    elements.modalBody.innerHTML = `
      <div class="proposal-detail">
        <div class="param-row">
          <span class="param-label">Status</span>
          <span class="param-value"><span class="proposal-status ${data.status}">${data.status}</span></span>
        </div>
        <div class="param-row">
          <span class="param-label">Domain</span>
          <span class="param-value">${escapeHtml(data.domain ?? 'general')}</span>
        </div>
        <div class="param-row">
          <span class="param-label">Proposer</span>
          <span class="param-value">${escapeHtml(data.proposer?.display_name ?? 'Unknown')}</span>
        </div>
        <div class="param-row">
          <span class="param-label">Votes</span>
          <span class="param-value">👍 ${data.yes_votes ?? 0} / 👎 ${data.no_votes ?? 0} / 🤷 ${data.abstain_votes ?? 0}</span>
        </div>
        <div class="param-row">
          <span class="param-label">Weight</span>
          <span class="param-value">${(data.weighted_yes ?? 0).toFixed(2)} / ${(data.required_quorum ?? 0).toFixed(2)}</span>
        </div>
        <div style="margin-top: 16px; padding: 12px; background: rgba(15,23,42,0.5); border-radius: 8px;">
          <div class="param-label" style="margin-bottom: 8px;">Description</div>
          <div style="font-size: 13px; color: var(--text-main); line-height: 1.5;">
            ${escapeHtml(data.description ?? 'No description provided.')}
          </div>
        </div>
        ${isVotable ? `
        <div style="margin-top: 16px; display: flex; gap: 10px; justify-content: center;">
          <button class="quick-vote-btn yes" data-vote="yes" data-proposal="${proposalId}" style="padding: 10px 24px; background: #10b981; border: none; border-radius: 8px; color: white; font-weight: 600; cursor: pointer;">👍 YES</button>
          <button class="quick-vote-btn no" data-vote="no" data-proposal="${proposalId}" style="padding: 10px 24px; background: #ef4444; border: none; border-radius: 8px; color: white; font-weight: 600; cursor: pointer;">👎 NO</button>
          <button class="quick-vote-btn abstain" data-vote="abstain" data-proposal="${proposalId}" style="padding: 10px 16px; background: #6366f1; border: none; border-radius: 8px; color: white; font-weight: 600; cursor: pointer;">🤷 ABSTAIN</button>
        </div>
        ` : ''}
      </div>
    `;
    
    // Attach quick vote handlers
    document.querySelectorAll('.quick-vote-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const voteType = e.target.dataset.vote;
        const pId = e.target.dataset.proposal;
        e.target.disabled = true;
        e.target.textContent = '...';
        const success = await quickVote(pId, voteType);
        if (success) {
          elements.modal.style.display = 'none';
        } else {
          e.target.disabled = false;
          e.target.textContent = e.target.dataset.vote.toUpperCase();
        }
      });
    });
  }

  // === Utilities ===
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // === Event Handlers ===
  function setupEventHandlers() {
    elements.refreshProposals?.addEventListener('click', loadProposals);
    elements.exportTrust?.addEventListener('click', exportTrustData);
    elements.clearEvents?.addEventListener('click', () => {
      events.length = 0;
      renderEvents();
    });

    // Modal handlers
    elements.closeModal?.addEventListener('click', () => {
      elements.modal.style.display = 'none';
    });
    
    elements.modal?.querySelector('.modal-overlay')?.addEventListener('click', () => {
      elements.modal.style.display = 'none';
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && elements.modal.style.display !== 'none') {
        elements.modal.style.display = 'none';
      }
    });

    // New AC handlers
    document.getElementById('refresh-votes')?.addEventListener('click', loadVoteHistory);
    
    document.getElementById('claim-expertise')?.addEventListener('click', () => {
      const form = document.getElementById('claim-form');
      form.style.display = form.style.display === 'none' ? 'block' : 'none';
    });
    
    document.getElementById('submit-claim')?.addEventListener('click', submitExpertiseClaim);
    
    // Auth Handlers
    elements.loginBtn?.addEventListener('click', () => keycloak?.login());
    elements.logoutBtn?.addEventListener('click', () => keycloak?.logout());
  }

  // === Initialization ===
  async function init() {
    console.log('[Governance] Initializing dashboard (BFF Mode)...');
    
    // Check Session (or just rely on API calls)
    // Since /governance is server-side protected, we are likely authenticated.
    // We fetch user info to populate UI.
    try {
        const res = await fetch('/auth/me');
        if (!res.ok) throw new Error('Session invalid');
        const user = await res.json();
        
        // Update UI with User Info
        elements.userDisplay.textContent = user.preferred_username || user.sub;
        elements.loginBtn.style.display = 'none';
        elements.logoutBtn.style.display = 'block';
        
        // Logout handler
        elements.logoutBtn.onclick = () => window.location.href = '/auth/logout';
        
        // Unmask UI
        const shell = document.getElementById('main-shell');
        if (shell) shell.style.display = 'block';
        
    } catch (e) {
        console.warn('[Governance] Not authenticated (or session expired). Redirecting...');
        window.location.href = '/login?returnUrl=/governance';
        return;
    }
    
    setupEventHandlers();
    connectWebSocket();
    
    // Load initial data
    await Promise.all([
      loadDashboardData(),
      loadConstitution(),
      loadProposals(),
      loadLegitimacy(),
      loadVoteHistory(),
      loadTrustTrend(),
      loadExpertiseClaims(),
      loadExpertiseClaims(),
      loadViolations()
    ]);

    // Auto-refresh every 30 seconds
    setInterval(() => {
      loadDashboardData();
      loadProposals();
      loadVoteHistory();
      loadViolations();
    }, 30000);

    console.log('[Governance] Dashboard ready');
  }

  // Start when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

