/**
 * Memory Dashboard - Real-time Cognitive Knowledge System Visibility
 * Fetches dashboard stats and renders charts
 */

(function() {
  'use strict';

  const API_BASE = '/dashboard/api';
  let charts = {};

  // === DOM Elements ===
  const elements = {
    // Sidebar stats
    totalPoints: document.getElementById('total-points'),
    enrichedCount: document.getElementById('enriched-count'),
    enrichedPct: document.getElementById('enriched-pct'),
    totalCost: document.getElementById('total-cost'),
    totalTokens: document.getElementById('total-tokens'),
    heuristicRate: document.getElementById('heuristic-rate'),
    researchSessions: document.getElementById('research-sessions'),
    
    // Panel stat grids
    enrichmentStats: document.getElementById('enrichment-stats'),
    costStats: document.getElementById('cost-stats'),
    providerBreakdown: document.getElementById('provider-breakdown'),
    heuristicStats: document.getElementById('heuristic-stats'),
    researchStats: document.getElementById('research-stats'),
    
    // Charts
    domainChart: document.getElementById('domainChart'),
    ingestionChart: document.getElementById('ingestionChart'),
    heatmapChart: document.getElementById('heatmapChart'),
    enrichmentChart: document.getElementById('enrichmentChart'),
    heuristicChart: document.getElementById('heuristicChart'),
    researchChart: document.getElementById('researchChart'),
    
    // Controls
    refreshBtn: document.getElementById('refresh-btn'),
    timestamp: document.getElementById('timestamp')
  };

  // === Color Palette ===
  const colors = {
    primary: '#00d4ff',
    secondary: '#00ff88',
    tertiary: '#6366f1',
    warning: '#f59e0b',
    danger: '#ef4444',
    muted: '#94a3b8',
    
    palette: [
      '#00d4ff', '#00ff88', '#6366f1', '#f59e0b', '#ef4444',
      '#14b8a6', '#8b5cf6', '#ec4899', '#84cc16', '#f97316'
    ]
  };

  // === API Functions ===
  async function fetchStats() {
    try {
      const response = await fetch(`${API_BASE}/stats`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      return null;
    }
  }

  // === Render Functions ===
  function renderDashboard(data) {
    // Destroy existing charts
    Object.values(charts).forEach(chart => chart && chart.destroy());
    charts = {};

    // Update sidebar stats
    updateSidebarStats(data);

    // Render charts
    renderDomainChart(data.domain_distribution || {});
    renderIngestionChart(data.ingestion_timeline || {});
    renderHeatmapChart(data.retrieval_heatmap || {});
    renderEnrichmentPanel(data.enrichment_coverage || {});
    renderCostPanel(data.cost_tracking || {});
    renderHeuristicPanel(data.heuristic_hit_rate || {});
    renderResearchPanel(data.research_stats || {});

    // Update timestamp
    if (data.timestamp) {
      elements.timestamp.textContent = `Last updated: ${new Date(data.timestamp).toLocaleString()}`;
    }
  }

  function updateSidebarStats(data) {
    const enrichment = data.enrichment_coverage || {};
    const costs = data.cost_tracking || {};
    const heuristics = data.heuristic_hit_rate || {};
    const research = data.research_stats || {};

    elements.totalPoints.textContent = formatNumber(enrichment.total_points);
    elements.enrichedCount.textContent = formatNumber(enrichment.enriched_points);
    elements.enrichedPct.textContent = `${enrichment.coverage_percent || 0}%`;
    elements.totalCost.textContent = `$${(costs.total_cost_usd || 0).toFixed(2)}`;
    elements.totalTokens.textContent = formatNumber(costs.total_tokens);
    elements.heuristicRate.textContent = `${heuristics.heuristic_rate_percent || 0}%`;
    elements.researchSessions.textContent = formatNumber(research.sessions);
  }

  function renderDomainChart(distribution) {
    const ctx = elements.domainChart;
    if (!ctx) return;

    const labels = Object.keys(distribution);
    const values = Object.values(distribution);

    charts.domain = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: colors.palette.slice(0, labels.length),
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: colors.muted, font: { size: 10 }, boxWidth: 12 }
          }
        }
      }
    });
  }

  function renderIngestionChart(timeline) {
    const ctx = elements.ingestionChart;
    if (!ctx) return;

    const labels = Object.keys(timeline);
    const values = Object.values(timeline);

    charts.ingestion = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Points Ingested',
          data: values,
          borderColor: colors.primary,
          backgroundColor: 'rgba(0, 212, 255, 0.1)',
          fill: true,
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4
        }]
      },
      options: chartOptions()
    });
  }

  function renderHeatmapChart(heatmap) {
    const ctx = elements.heatmapChart;
    if (!ctx) return;

    const labels = Object.keys(heatmap);
    const values = Object.values(heatmap);

    charts.heatmap = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Retrieval Count',
          data: values,
          backgroundColor: colors.secondary,
          borderRadius: 4
        }]
      },
      options: {
        ...chartOptions(),
        indexAxis: 'y',
        plugins: { legend: { display: false } }
      }
    });
  }

  function renderEnrichmentPanel(coverage) {
    const fields = coverage.field_coverage || {};
    
    elements.enrichmentStats.innerHTML = `
      <div class="stat-item">
        <div class="label">Total Points</div>
        <div class="value">${formatNumber(coverage.total_points)}</div>
      </div>
      <div class="stat-item">
        <div class="label">Enriched</div>
        <div class="value">${formatNumber(coverage.enriched_points)}</div>
      </div>
    `;

    const ctx = elements.enrichmentChart;
    if (!ctx) return;

    charts.enrichment = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: Object.keys(fields),
        datasets: [{
          data: Object.values(fields),
          backgroundColor: [colors.primary, colors.secondary, colors.tertiary, colors.warning],
          borderRadius: 4
        }]
      },
      options: {
        ...chartOptions(),
        plugins: { legend: { display: false } },
        scales: { ...chartOptions().scales, y: { ...chartOptions().scales.y, max: 100 } }
      }
    });
  }

  function renderCostPanel(costs) {
    const byProvider = costs.by_provider || {};

    elements.costStats.innerHTML = `
      <div class="stat-item">
        <div class="label">Total Cost</div>
        <div class="value">$${(costs.total_cost_usd || 0).toFixed(4)}</div>
      </div>
      <div class="stat-item">
        <div class="label">Avg/Query</div>
        <div class="value">$${(costs.avg_cost_per_query || 0).toFixed(6)}</div>
      </div>
    `;

    elements.providerBreakdown.innerHTML = Object.entries(byProvider)
      .map(([name, cost]) => `
        <div class="provider-row">
          <span class="name">${escapeHtml(name)}</span>
          <span class="cost">$${Number(cost).toFixed(4)}</span>
        </div>
      `).join('');
  }

  function renderHeuristicPanel(stats) {
    elements.heuristicStats.innerHTML = `
      <div class="stat-item">
        <div class="label">Classified</div>
        <div class="value">${formatNumber(stats.total_classified)}</div>
      </div>
      <div class="stat-item">
        <div class="label">Keywords</div>
        <div class="value">${formatNumber(stats.total_heuristic_keywords)}</div>
      </div>
    `;

    const ctx = elements.heuristicChart;
    if (!ctx) return;

    charts.heuristic = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Heuristic', 'LLM', 'Direct'],
        datasets: [{
          data: [stats.heuristic_count || 0, stats.llm_count || 0, stats.direct_count || 0],
          backgroundColor: [colors.secondary, colors.tertiary, colors.warning],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: colors.muted, font: { size: 10 } }
          }
        }
      }
    });
  }

  function renderResearchPanel(stats) {
    elements.researchStats.innerHTML = `
      <div class="stat-item">
        <div class="label">Sessions</div>
        <div class="value">${stats.sessions || 0}</div>
      </div>
      <div class="stat-item">
        <div class="label">Queries Executed</div>
        <div class="value">${formatNumber(stats.executed_queries)}</div>
      </div>
      <div class="stat-item">
        <div class="label">Sources Collected</div>
        <div class="value">${formatNumber(stats.sources_collected)}</div>
      </div>
      <div class="stat-item">
        <div class="label">Avg Cost</div>
        <div class="value">$${(stats.avg_cost_usd || 0).toFixed(4)}</div>
      </div>
    `;

    const trend = stats.trend || [];
    const ctx = elements.researchChart;
    if (!ctx || trend.length === 0) return;

    charts.research = new Chart(ctx, {
      type: 'line',
      data: {
        labels: trend.map(t => t.date),
        datasets: [
          {
            label: 'Sessions',
            data: trend.map(t => t.sessions),
            borderColor: colors.primary,
            backgroundColor: 'rgba(0, 212, 255, 0.1)',
            fill: true,
            tension: 0.4,
            yAxisID: 'y'
          },
          {
            label: 'Cost ($)',
            data: trend.map(t => t.cost_usd),
            borderColor: colors.secondary,
            borderDash: [5, 5],
            tension: 0.4,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        ...chartOptions(),
        scales: {
          x: { ticks: { color: colors.muted }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { position: 'left', ticks: { color: colors.muted }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y1: { position: 'right', ticks: { color: colors.muted }, grid: { display: false } }
        }
      }
    });
  }

  // === Utilities ===
  function chartOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: colors.muted, font: { size: 11 } } }
      },
      scales: {
        x: { ticks: { color: colors.muted }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: colors.muted }, grid: { color: 'rgba(255,255,255,0.05)' } }
      }
    };
  }

  function formatNumber(num) {
    if (num === undefined || num === null) return '--';
    return num.toLocaleString();
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // === Initialization ===
  async function loadDashboard() {
    console.log('[Memory Dashboard] Loading...');
    
    const data = await fetchStats();
    if (data) {
      renderDashboard(data);
      console.log('[Memory Dashboard] Loaded successfully');
    } else {
      console.error('[Memory Dashboard] Failed to load data');
    }
  }

  function init() {
    elements.refreshBtn?.addEventListener('click', loadDashboard);
    loadDashboard();
    
    // Auto-refresh every 60 seconds
    setInterval(loadDashboard, 60000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
