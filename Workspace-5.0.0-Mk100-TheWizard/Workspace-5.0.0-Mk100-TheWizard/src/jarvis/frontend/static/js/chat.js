// UI Version for observability & trace correlation
window.__JARVIS_UI_VERSION__ = "2.2.0";

(function () {
        var messagesEl = document.getElementById("messages");
        var formEl = document.getElementById("chat-form");
        var inputEl = document.getElementById("input");
        var sendBtn = document.getElementById("send-btn");
        var statusPill = document.getElementById("status-pill");
        var autoGroundingCheckbox = document.getElementById("auto-grounding");
        var showConfidenceCheckbox = document.getElementById("show-confidence");
        var researchCheckbox = document.getElementById("enable-research");
        var researchSettingsBtn = document.getElementById("research-settings-btn");
        var researchSettingsPanel = document.getElementById("research-settings");
        var coverageSlider = document.getElementById("coverage-threshold");
        var coverageValue = document.getElementById("coverage-threshold-value");
        var maxQueriesSlider = document.getElementById("max-queries");
        var maxQueriesValue = document.getElementById("max-queries-value");
        var costCapInput = document.getElementById("cost-cap");
        // sourceInput removed - domain filtering now via checkboxes (Story 4.5.7)
        var tagsInput = document.getElementById("tags-input");

        var convoListEl = document.getElementById("conversation-list");
        var newChatBtn = document.getElementById("new-chat-btn");
        var sourcesTooltip = document.createElement("div");
        sourcesTooltip.className = "sources-tooltip";
        document.body.appendChild(sourcesTooltip);
        var researchProgressEl = document.getElementById("research-progress");
        var researchProgressFill = document.getElementById("research-progress-fill");
        var researchStageLabel = document.getElementById("research-stage-label");
        var researchPercent = document.getElementById("research-percent");
        var researchEta = document.getElementById("research-eta");
        var cancelResearchBtn = document.getElementById("cancel-research-btn");
        var researchProgressTimer = null;
        var researchStageIndex = 0;
        var researchController = null;
        var researchStages = [
          { label: "🔍 Analyzing gaps...", percent: 10 },
          { label: "🧠 Planning research...", percent: 30 },
          { label: "🌐 Researching...", percent: 55 },
          { label: "🔗 Integrating knowledge...", percent: 75 },
          { label: "💾 Updating memory...", percent: 90 },
        ];
        function formatRelativeTime(iso) {
          if (!iso) {
            return null;
          }
          try {
            var date = new Date(iso);
            var now = new Date();
            var diffMs = now.getTime() - date.getTime();
            if (isNaN(diffMs)) {
              return null;
            }
            var seconds = Math.max(0, Math.floor(diffMs / 1000));
            if (seconds < 60) {
              return seconds + "s ago";
            }
            var minutes = Math.floor(seconds / 60);
            if (minutes < 60) {
              return minutes + "m ago";
            }
            var hours = Math.floor(minutes / 60);
            if (hours < 24) {
              return hours + "h ago";
            }
            var days = Math.floor(hours / 24);
            if (days < 30) {
              return days + "d ago";
            }
            var months = Math.floor(days / 30);
            if (months < 12) {
              return months + "mo ago";
            }
            var years = Math.floor(months / 12);
            return years + "y ago";
          } catch (e) {
            return null;
          }
        }

        function openDocViewer(docId) {
          if (!docId) return;
          if (docTitle) docTitle.textContent = "Loading...";
          if (docBody) docBody.textContent = "Fetching document content...";
          if (docViewer) docViewer.classList.add("open");
          
          var isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(docId);
          var url = isUuid ? "/api/memory/documents/" + encodeURIComponent(docId) : "/api/memory/documents/key/" + encodeURIComponent(docId);
          fetch(url)
            .then(function(resp) {
              if (!resp.ok) throw new Error("Failed to load document: " + resp.status);
              return resp.json();
            })
            .then(function(doc) {
              if (docTitle) docTitle.textContent = doc.source_file || doc.doc_key;
              if (docBody) {
                docBody.innerHTML = "";
                var pre = document.createElement("pre");
                pre.style.whiteSpace = "pre-wrap";
                pre.style.fontFamily = "monospace";
                pre.style.padding = "10px";
                pre.textContent = doc.content;
                docBody.appendChild(pre);
              }
            })
            .catch(function(err) {
              if (docTitle) docTitle.textContent = "Error";
              if (docBody) docBody.textContent = "Could not load document: " + err.message;
            });
        }
        var suggestionsEl = document.getElementById("suggestions");
        var refreshHistoryBtn = document.getElementById("refresh-history-btn");
        var clearSuggestionsBtn = document.getElementById("clear-suggestions-btn");
        var historyListEl = document.getElementById("history-list");
        var historyWindowSelect = document.getElementById("history-window");
        var historyGapSelect = document.getElementById("history-gap-filter");
        var historyChart = null;
        var gapChart = null;
        var healthStatus = document.getElementById("research-health-status");
        var healthRateBar = document.getElementById("health-rate-bar");
        var healthCostBar = document.getElementById("health-cost-bar");
        var healthRateLabel = document.getElementById("health-rate-label");
        var healthCostLabel = document.getElementById("health-cost-label");
        var retryBtn = document.getElementById("retry-btn");
        var lastUserMessage = "";
        var srAnnouncer = document.getElementById("sr-announcer");
        var exportHistoryBtn = document.getElementById("export-history-btn");
        var lastHistoryData = null;
        var timeSensitiveHits = parseInt(window.localStorage.getItem("jarvis_time_sensitive_hits") || "0", 10);
        var autoEnableThreshold = 5;
        var autoEnabledFromLearning = false;
        var docViewer = document.getElementById("doc-viewer");
        var docBody = document.getElementById("doc-body");
        var docTitle = document.getElementById("doc-title");
        var closeDocBtn = document.getElementById("close-doc-btn");
        var openDocTabBtn = document.getElementById("open-doc-tab-btn");
        var currentDocData = null;
        var currentDocId = null;
        
        // Conversation pagination and search state
        var convoSearchEl = document.getElementById("convo-search");
        var loadMoreConvosBtn = document.getElementById("load-more-convos");
        var convoSortEl = document.getElementById("convo-sort");
        var convoDateFilterEl = document.getElementById("convo-date-filter");
        var convoPersonaFilterEl = document.getElementById("convo-persona-filter");
        var allConvos = [];
        var convoOffset = 0;
        var convoLimit = 20;
        var hasMoreConvos = true;
        var convoSearchTerm = "";
        var convoLoading = false;
        var convoSortBy = "newest";
        var convoDateFilter = "all";
        var convoPersonaFilter = "all";
        
        // Conversation preview tooltip
        var previewTooltip = document.createElement("div");
        previewTooltip.className = "convo-preview-tooltip";
        document.body.appendChild(previewTooltip);
        
        // Debounce utility
        function debounce(func, wait) {
          var timeout;
          return function() {
            var context = this;
            var args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(function() {
              func.apply(context, args);
            }, wait);
          };
        }

        var conversationId = window.localStorage.getItem("jarvis_conversation_id") || null;
        var busy = false;

        // Restore controls from localStorage (best-effort)
        var storedAutoGrounding = window.localStorage.getItem("jarvis_auto_grounding");
        if (autoGroundingCheckbox && storedAutoGrounding !== null) {
          autoGroundingCheckbox.checked = storedAutoGrounding === "true";
        }
        var storedShowConfidence = window.localStorage.getItem("jarvis_show_confidence");
        if (showConfidenceCheckbox && storedShowConfidence !== null) {
          showConfidenceCheckbox.checked = storedShowConfidence === "true";
        }
        var storedResearch = window.localStorage.getItem("jarvis_enable_research");
        if (researchCheckbox && storedResearch !== null) {
          researchCheckbox.checked = storedResearch === "true";
        }
        // storedSource removed - domain filtering now via checkboxes (Story 4.5.7)
        var storedCoverage = window.localStorage.getItem("jarvis_research_coverage");
        if (coverageSlider && storedCoverage !== null) {
          coverageSlider.value = storedCoverage;
          coverageValue.textContent = parseFloat(storedCoverage).toFixed(2);
        }
        var storedMaxQueries = window.localStorage.getItem("jarvis_research_max_queries");
        if (maxQueriesSlider && storedMaxQueries !== null) {
          maxQueriesSlider.value = storedMaxQueries;
          maxQueriesValue.textContent = storedMaxQueries;
        }
        var storedCostCap = window.localStorage.getItem("jarvis_research_cost_cap");
        if (costCapInput && storedCostCap !== null) {
          costCapInput.value = storedCostCap;
        }

        if (autoGroundingCheckbox) {
          autoGroundingCheckbox.addEventListener("change", function () {
            window.localStorage.setItem(
              "jarvis_auto_grounding",
              autoGroundingCheckbox.checked ? "true" : "false"
            );
          });
        }
        if (showConfidenceCheckbox) {
          showConfidenceCheckbox.addEventListener("change", function () {
            window.localStorage.setItem(
              "jarvis_show_confidence",
              showConfidenceCheckbox.checked ? "true" : "false"
            );
          });
        }
        if (researchCheckbox) {
          researchCheckbox.addEventListener("change", function () {
            window.localStorage.setItem(
              "jarvis_enable_research",
              researchCheckbox.checked ? "true" : "false"
            );
          });
        }
        if (researchSettingsBtn && researchSettingsPanel) {
          researchSettingsBtn.addEventListener("click", function () {
            var visible = researchSettingsPanel.style.display === "block";
            researchSettingsPanel.style.display = visible ? "none" : "block";
          });
        }
        if (coverageSlider) {
          coverageSlider.addEventListener("input", function () {
            coverageValue.textContent = parseFloat(coverageSlider.value).toFixed(2);
            window.localStorage.setItem("jarvis_research_coverage", coverageSlider.value);
          });
        }
        if (maxQueriesSlider) {
          maxQueriesSlider.addEventListener("input", function () {
            maxQueriesValue.textContent = maxQueriesSlider.value;
            window.localStorage.setItem("jarvis_research_max_queries", maxQueriesSlider.value);
          });
        }
        if (costCapInput) {
          costCapInput.addEventListener("input", function () {
            window.localStorage.setItem("jarvis_research_cost_cap", costCapInput.value || "0.5");
          });
        }
        // sourceInput change listener removed - domain filtering now via checkboxes (Story 4.5.7)
        // Domain multi-select state
        var allDomains = [];
        var domainMetadata = {};  // Store metadata: {domain: {description, count}}
        var selectedDomains = [];

        function renderDomainCheckboxes(domains) {
          var container = document.getElementById("domain-checkboxes");
          var searchInput = document.getElementById("domain-search");
          if (!container || !Array.isArray(domains)) return;

          allDomains = domains.sort();

          function renderList(filterTerm) {
            container.innerHTML = "";
            var filtered = filterTerm
              ? allDomains.filter(function(d) { return d.toLowerCase().indexOf(filterTerm.toLowerCase()) >= 0; })
              : allDomains;

            filtered.forEach(function(domain) {
              var item = document.createElement("div");
              item.className = "domain-checkbox-item";

              var checkbox = document.createElement("input");
              checkbox.type = "checkbox";
              checkbox.id = "domain-check-" + domain.replace(/\\./g, "-");
              checkbox.value = domain;
              checkbox.checked = selectedDomains.indexOf(domain) >= 0;

              var label = document.createElement("label");
              label.textContent = domain;
              label.setAttribute("for", checkbox.id);

              // Add tooltip if metadata available
              if (domainMetadata[domain]) {
                var meta = domainMetadata[domain];
                var tooltip = meta.description;
                if (meta.count !== undefined) {
                  tooltip += " (" + meta.count + " chunks)";
                }
                label.setAttribute("data-tooltip", tooltip);
              }

              item.appendChild(checkbox);
              item.appendChild(label);
              container.appendChild(item);

              // Checkbox change handler
              checkbox.addEventListener("change", function() {
                if (checkbox.checked) {
                  if (selectedDomains.indexOf(domain) < 0) {
                    selectedDomains.push(domain);
                  }
                } else {
                  selectedDomains = selectedDomains.filter(function(d) { return d !== domain; });
                }
                updateSelectedDomainsCount();
              });

              // Label click also toggles
              label.addEventListener("click", function(e) {
                e.preventDefault();
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event("change"));
              });
            });
          }

          renderList("");

          if (searchInput) {
            searchInput.value = "";
            searchInput.addEventListener("input", function() {
              renderList(searchInput.value);
            });
          }
        }

        function updateSelectedDomainsCount() {
          var countEl = document.getElementById("selected-domains-count");
          if (countEl) {
            countEl.textContent = selectedDomains.length;
          }
        }

        function loadDomains() {
          // Load metadata endpoint for descriptions and counts
          fetch("/api/memory/domains/metadata")
            .then(function (resp) { return resp.ok ? resp.json() : null; })
            .then(function (data) {
              if (data && Array.isArray(data.domains)) {
                // Build metadata map
                domainMetadata = {};
                var domainNames = [];
                data.domains.forEach(function(item) {
                  domainNames.push(item.name);
                  domainMetadata[item.name] = {
                    description: item.description,
                    count: item.chunk_count
                  };
                });
                renderDomainCheckboxes(domainNames);
              }
            })
            .catch(function () {
              // Fallback to simple domains list if metadata fails
              fetch("/api/memory/domains")
                .then(function (resp) { return resp.ok ? resp.json() : null; })
                .then(function (data) {
                  if (data && Array.isArray(data.domains)) {
                    renderDomainCheckboxes(data.domains);
                  }
                })
                .catch(function () { /* ignore */ });
            });
        }

        // Domain selector panel handlers
        var domainSelectBtn = document.getElementById("domain-select-btn");
        var domainPanel = document.getElementById("domain-selector-panel");
        var clearDomainsBtn = document.getElementById("clear-domains");
        var applyDomainsBtn = document.getElementById("apply-domains");

        if (domainSelectBtn && domainPanel) {
          domainSelectBtn.addEventListener("click", function() {
            var visible = domainPanel.style.display === "block";
            domainPanel.style.display = visible ? "none" : "block";
            // Close research panel if open
            if (!visible && researchSettingsPanel) {
              researchSettingsPanel.style.display = "none";
            }
          });
        }

        if (clearDomainsBtn) {
          clearDomainsBtn.addEventListener("click", function() {
            selectedDomains = [];
            renderDomainCheckboxes(allDomains);
            updateSelectedDomainsCount();
          });
        }

        if (applyDomainsBtn) {
          applyDomainsBtn.addEventListener("click", function() {
            // Domain selections already stored via renderActiveFilterChips (Story 4.5.7)
            domainPanel.style.display = "none";
            window.localStorage.setItem("jarvis_domains", selectedDomains.join(","));
            renderActiveFilterChips();
          });
        }

        // Close button handler for domain panel
        var closeDomainBtn = document.getElementById("close-domain-panel");
        if (closeDomainBtn && domainPanel) {
          closeDomainBtn.addEventListener("click", function() {
            domainPanel.style.display = "none";
          });
        }

        // Tags multi-select state
        var allTags = [];
        var tagMetadata = {};  // Store metadata: {tag: {description, count}}
        var selectedTags = [];

        function renderTagsCheckboxes(tags) {
          var container = document.getElementById("tags-checkboxes");
          var searchInput = document.getElementById("tags-search");
          if (!container || !Array.isArray(tags)) return;

          allTags = tags.sort();

          function renderList(filterTerm) {
            container.innerHTML = "";
            var filtered = filterTerm
              ? allTags.filter(function(t) { return t.toLowerCase().indexOf(filterTerm.toLowerCase()) >= 0; })
              : allTags;

            filtered.forEach(function(tag) {
              var item = document.createElement("div");
              item.className = "domain-checkbox-item";

              var checkbox = document.createElement("input");
              checkbox.type = "checkbox";
              checkbox.id = "tag-check-" + tag.replace(/[^a-zA-Z0-9]/g, "-");
              checkbox.value = tag;
              checkbox.checked = selectedTags.indexOf(tag) >= 0;

              var label = document.createElement("label");
              label.textContent = tag;
              label.setAttribute("for", checkbox.id);

              // Add tooltip if metadata available
              if (tagMetadata[tag]) {
                var meta = tagMetadata[tag];
                var tooltip = meta.description;
                if (meta.count !== undefined) {
                  tooltip += " (" + meta.count + " chunks)";
                }
                label.setAttribute("data-tooltip", tooltip);
              }

              item.appendChild(checkbox);
              item.appendChild(label);
              container.appendChild(item);

              // Checkbox change handler
              checkbox.addEventListener("change", function() {
                if (checkbox.checked) {
                  if (selectedTags.indexOf(tag) < 0) {
                    selectedTags.push(tag);
                  }
                } else {
                  selectedTags = selectedTags.filter(function(t) { return t !== tag; });
                }
                updateSelectedTagsCount();
              });

              // Label click also toggles
              label.addEventListener("click", function(e) {
                e.preventDefault();
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event("change"));
              });
            });
          }

          renderList("");

          if (searchInput) {
            searchInput.value = "";
            searchInput.addEventListener("input", function() {
              renderList(searchInput.value);
            });
          }
        }

        function updateSelectedTagsCount() {
          var countEl = document.getElementById("selected-tags-count");
          if (countEl) {
            countEl.textContent = selectedTags.length;
          }
        }

        function loadTags() {
          // Load metadata endpoint for descriptions and counts
          fetch("/api/memory/tags/metadata")
            .then(function (resp) { return resp.ok ? resp.json() : null; })
            .then(function (data) {
              if (data && Array.isArray(data.tags)) {
                // Build metadata map
                tagMetadata = {};
                var tagNames = [];
                data.tags.forEach(function(item) {
                  tagNames.push(item.tag);
                  tagMetadata[item.tag] = {
                    description: item.description,
                    count: item.count
                  };
                });
                renderTagsCheckboxes(tagNames);
              }
            })
            .catch(function () {
              // Fallback to simple tags list if metadata fails
              fetch("/api/memory/tags")
                .then(function (resp) { return resp.ok ? resp.json() : null; })
                .then(function (data) {
                  if (data && Array.isArray(data.tags)) {
                    renderTagsCheckboxes(data.tags);
                  }
                })
                .catch(function () { /* ignore */ });
            });
        }

        // Tags selector panel handlers
        var tagsSelectBtn = document.getElementById("tags-select-btn");
        var tagsPanel = document.getElementById("tags-selector-panel");
        var clearTagsBtn = document.getElementById("clear-tags");
        var applyTagsBtn = document.getElementById("apply-tags");

        if (tagsSelectBtn && tagsPanel) {
          tagsSelectBtn.addEventListener("click", function() {
            var visible = tagsPanel.style.display === "block";
            tagsPanel.style.display = visible ? "none" : "block";
            // Close other panels if open
            if (!visible && domainPanel) {
              domainPanel.style.display = "none";
            }
            if (!visible && researchSettingsPanel) {
              researchSettingsPanel.style.display = "none";
            }
          });
        }

        if (clearTagsBtn) {
          clearTagsBtn.addEventListener("click", function() {
            selectedTags = [];
            renderTagsCheckboxes(allTags);
            updateSelectedTagsCount();
          });
        }

        if (applyTagsBtn) {
          applyTagsBtn.addEventListener("click", function() {
            tagsPanel.style.display = "none";
            window.localStorage.setItem("jarvis_tags", selectedTags.join(","));
          });
        }

        // Close button handler for tags panel
        var closeTagsBtn = document.getElementById("close-tags-panel");
        if (closeTagsBtn && tagsPanel) {
          closeTagsBtn.addEventListener("click", function() {
            tagsPanel.style.display = "none";
          });
        }

        // Active Filters Mini-Bar
        function renderActiveFilters() {
          var activeFiltersBar = document.getElementById("active-filters-bar");
          var filterChipsContainer = document.getElementById("active-filter-chips");
          if (!activeFiltersBar || !filterChipsContainer) return;

          // Show/hide bar based on whether there are active filters
          if (selectedDomains.length === 0 && selectedTags.length === 0) {
            activeFiltersBar.style.display = "none";
            return;
          }

          activeFiltersBar.style.display = "block";
          filterChipsContainer.innerHTML = "";

          // Render domain chips
          selectedDomains.forEach(function(domain) {
            var chip = document.createElement("span");
            chip.className = "filter-chip";
            chip.innerHTML = "📁 " + domain + " <span class='filter-chip-remove' data-domain='" + domain + "'>×</span>";
            filterChipsContainer.appendChild(chip);
          });

          // Render tag chips
          selectedTags.forEach(function(tag) {
            var chip = document.createElement("span");
            chip.className = "filter-chip";
            chip.innerHTML = "🏷️ " + tag + " <span class='filter-chip-remove' data-tag='" + tag + "'>×</span>";
            filterChipsContainer.appendChild(chip);
          });

          // Add click handlers for chip removal
          var removeButtons = filterChipsContainer.querySelectorAll(".filter-chip-remove");
          removeButtons.forEach(function(btn) {
            btn.addEventListener("click", function(e) {
              e.stopPropagation();
              var domain = btn.getAttribute("data-domain");
              var tag = btn.getAttribute("data-tag");

              if (domain) {
                selectedDomains = selectedDomains.filter(function(d) { return d !== domain; });
                renderDomainCheckboxes(allDomains);
                updateSelectedDomainsCount();
                window.localStorage.setItem("jarvis_domains", selectedDomains.join(","));
              }

              if (tag) {
                selectedTags = selectedTags.filter(function(t) { return t !== tag; });
                renderTagsCheckboxes(allTags);
                updateSelectedTagsCount();
                window.localStorage.setItem("jarvis_tags", selectedTags.join(","));
              }

              renderActiveFilters();
            });
          });
        }

        // Clear All Filters button
        var clearAllFiltersBtn = document.getElementById("clear-all-filters");
        if (clearAllFiltersBtn) {
          clearAllFiltersBtn.addEventListener("click", function() {
            selectedDomains = [];
            selectedTags = [];
            renderDomainCheckboxes(allDomains);
            renderTagsCheckboxes(allTags);
            updateSelectedDomainsCount();
            updateSelectedTagsCount();
            renderActiveFilters();
            window.localStorage.removeItem("jarvis_domains");
            window.localStorage.removeItem("jarvis_tags");
          });
        }

        // Update existing domain/tag selection handlers to also update active filters
        var originalUpdateDomainsCount = updateSelectedDomainsCount;
        updateSelectedDomainsCount = function() {
          originalUpdateDomainsCount();
          renderActiveFilters();
        };

        var originalUpdateTagsCount = updateSelectedTagsCount;
        updateSelectedTagsCount = function() {
          originalUpdateTagsCount();
          renderActiveFilters();
        };

        // Trace Viewer Modal (AC6 - Story 4.5.7)
        var traceModal = document.getElementById("trace-modal");
        var traceModalBody = document.getElementById("trace-modal-body");
        var closeTraceModal = document.getElementById("close-trace-modal");

        function openTraceViewer(traceId) {
          if (!traceId || !traceModal || !traceModalBody) return;

          traceModalBody.innerHTML = '<div class="trace-loading">Loading cognitive trace...</div>';
          traceModal.style.display = "block";

          fetch("/traces/" + traceId)
            .then(function(resp) {
              if (!resp.ok) throw new Error("Failed to load trace: " + resp.status);
              return resp.json();
            })
            .then(function(trace) {
              renderTrace(trace);
            })
            .catch(function(err) {
              traceModalBody.innerHTML = '<div class="trace-loading" style="color:#ef4444;">Error loading trace: ' + err.message + '</div>';
            });
        }

        function renderTrace(trace) {
          if (!traceModalBody) return;

          var html = '';

          // Section 1: Query & Mode
          html += '<div class="trace-section">';
          html += '  <div class="trace-section-header">';
          html += '    <span class="trace-section-title">📝 Query & Mode</span>';
          html += '    <span class="trace-section-badge">' + (trace.mode || 'qa') + '</span>';
          html += '  </div>';
          html += '  <div class="trace-section-body">';
          html += '    <div class="trace-meta-row"><span class="trace-meta-label">Query:</span><span class="trace-meta-value">' + escapeHtml(trace.query || '') + '</span></div>';
          html += '    <div class="trace-meta-row"><span class="trace-meta-label">Mode:</span><span class="trace-meta-value">' + (trace.mode || 'qa') + '</span></div>';
          html += '    <div class="trace-meta-row"><span class="trace-meta-label">Severity:</span><span class="trace-meta-value">' + (trace.severity || 'normal') + '</span></div>';
          html += '  </div>';
          html += '</div>';

          // Section 2: Memory Retrieval
          html += '<div class="trace-section">';
          html += '  <div class="trace-section-header">';
          html += '    <span class="trace-section-title">🔍 Memory Retrieval</span>';
          html += '    <span class="trace-section-badge">' + (trace.k_final || 0) + ' chunks</span>';
          html += '  </div>';
          html += '  <div class="trace-section-body">';
          html += '    <div class="trace-meta-row"><span class="trace-meta-label">Retrievers:</span><span class="trace-meta-value">' + (trace.retrievers_used || []).join(', ') + '</span></div>';
          html += '    <div class="trace-meta-row"><span class="trace-meta-label">Diversity Mode:</span><span class="trace-meta-value">' + (trace.diversity_mode || 'balanced') + '</span></div>';
          html += '    <div class="trace-meta-row"><span class="trace-meta-label">Chunks Retrieved:</span><span class="trace-meta-value">' + (trace.k_initial || 0) + ' → ' + (trace.k_final || 0) + '</span></div>';
          html += '    <div class="trace-meta-row"><span class="trace-meta-label">Domains:</span><span class="trace-meta-value">' + (trace.domains || []).join(', ') + '</span></div>';
          html += '  </div>';
          html += '</div>';

          // Section 3: Planner Actions (AC5)
          if (trace.planner_actions && trace.planner_actions.length > 0) {
            html += '<div class="trace-section">';
            html += '  <div class="trace-section-header">';
            html += '    <span class="trace-section-title">🧠 Planner Decisions</span>';
            html += '    <span class="trace-section-badge">' + trace.planner_actions.length + ' actions</span>';
            html += '  </div>';
            html += '  <div class="trace-section-body">';
            trace.planner_actions.forEach(function(action) {
              html += '    <div class="trace-planner-action">';
              html += '      <div class="trace-planner-action-type">' + escapeHtml(action.action) + '</div>';
              html += '      <div class="trace-planner-action-reason">' + escapeHtml(action.reason) + '</div>';
              html += '    </div>';
            });
            html += '  </div>';
            html += '</div>';
          }

          // Section 4: Response Summary
          html += '<div class="trace-section">';
          html += '  <div class="trace-section-header">';
          html += '    <span class="trace-section-title">💬 Response Summary</span>';
          html += '  </div>';
          html += '  <div class="trace-section-body">';
          html += '    <div class="trace-meta-row"><span class="trace-meta-label">Summary:</span><span class="trace-meta-value">' + escapeHtml(trace.final_answer_summary || 'No summary available') + '</span></div>';
          html += '    <div class="trace-meta-row"><span class="trace-meta-label">Sources:</span><span class="trace-meta-value">' + (trace.sources || []).length + ' sources</span></div>';
          if (trace.confidence_estimate !== null && trace.confidence_estimate !== undefined) {
            html += '    <div class="trace-meta-row"><span class="trace-meta-label">Confidence:</span><span class="trace-meta-value">' + (trace.confidence_estimate * 100).toFixed(1) + '%</span></div>';
          }
          html += '  </div>';
          html += '</div>';

          // Section 5: Performance
          html += '<div class="trace-section">';
          html += '  <div class="trace-section-header">';
          html += '    <span class="trace-section-title">⚡ Performance</span>';
          html += '    <span class="trace-section-badge">' + (trace.total_latency_ms || 0) + 'ms</span>';
          html += '  </div>';
          html += '  <div class="trace-section-body">';
          html += '    <div class="trace-meta-row"><span class="trace-meta-label">Total Latency:</span><span class="trace-meta-value">' + (trace.total_latency_ms || 0) + 'ms</span></div>';
          if (trace.phase_timings && Object.keys(trace.phase_timings).length > 0) {
            Object.keys(trace.phase_timings).forEach(function(phase) {
              html += '    <div class="trace-meta-row"><span class="trace-meta-label">' + phase + ':</span><span class="trace-meta-value">' + trace.phase_timings[phase] + 'ms</span></div>';
            });
          }
          html += '  </div>';
          html += '</div>';

          traceModalBody.innerHTML = html;
        }

        function escapeHtml(text) {
          var map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
          };
          return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
        }

        if (closeTraceModal) {
          closeTraceModal.addEventListener("click", function() {
            if (traceModal) traceModal.style.display = "none";
          });
        }

        // Close modal on overlay click
        if (traceModal) {
          traceModal.addEventListener("click", function(e) {
            if (e.target.className === "trace-modal-overlay") {
              traceModal.style.display = "none";
            }
          });
        }

        if (newChatBtn) {
          newChatBtn.addEventListener("click", function () {
            conversationId = null;
            window.localStorage.removeItem("jarvis_conversation_id");
            messagesEl.innerHTML = "";
            appendSystem(
              "New BMAD session. Your messages & answers will be logged into Jarvis conversations.",
              false
            );
            loadConversationsList();
          });
        }

        function pushSuggestion(text) {
          if (!suggestionsEl || !text) {
            return;
          }
          if (suggestionsEl.children.length > 6) {
            suggestionsEl.removeChild(suggestionsEl.firstChild);
          }
          var entry = document.createElement("div");
          entry.className = "suggestion";
          entry.textContent = text;
          suggestionsEl.appendChild(entry);
        }

        function announce(text) {
          if (srAnnouncer) {
            srAnnouncer.textContent = text;
          }
        }

        function clearSuggestions() {
          if (suggestionsEl) {
            suggestionsEl.innerHTML = "";
          }
        }

        function updateHealth(ratePct, costPct, status) {
          if (healthRateBar) {
            healthRateBar.style.width = Math.max(0, Math.min(100, ratePct || 0)) + "%";
          }
          if (healthCostBar) {
            healthCostBar.style.width = Math.max(0, Math.min(100, costPct || 0)) + "%";
          }
          if (healthRateLabel) {
            healthRateLabel.textContent = Math.round(ratePct || 0) + "%";
          }
          if (healthCostLabel) {
            healthCostLabel.textContent = Math.round(costPct || 0) + "%";
          }
          if (healthStatus) {
            healthStatus.textContent = status || "Idle";
            if (status && status.toLowerCase().indexOf("limit") !== -1) {
              healthStatus.className = "badge-gap missing";
            } else if (status && status.toLowerCase().indexOf("cost") !== -1) {
              healthStatus.className = "badge-gap stale";
            } else {
              healthStatus.className = "badge-gap";
            }
          }
        }

        if (clearSuggestionsBtn) {
          clearSuggestionsBtn.addEventListener("click", function () {
            clearSuggestions();
          });
        }
        function closeDocViewer() {
          if (docViewer) {
            docViewer.style.display = "none";
            docBody.textContent = "";
            docTitle.textContent = "Document";
            currentDocData = null;
            currentDocId = null;
          }
        }
        if (closeDocBtn) {
          closeDocBtn.addEventListener("click", function () {
            closeDocViewer();
          });
        }
        if (openDocTabBtn) {
          openDocTabBtn.addEventListener("click", async function () {
            if (!currentDocData && currentDocId) {
              try {
                var resp = await fetch("/api/memory/documents/" + currentDocId);
                if (resp.ok) {
                  currentDocData = await resp.json();
                }
              } catch (e) {
                // ignore fetch failures here; UI already shows modal
              }
            }
            if (!currentDocData) {
              pushSuggestion("Open a source chip first to load the document.");
              return;
            }
            openDocHtmlInTab(currentDocData);
          });
        }
        if (docViewer) {
          docViewer.addEventListener("click", function (e) {
            if (e.target === docViewer) {
              closeDocViewer();
            }
          });
        }

        if (retryBtn) {
          retryBtn.addEventListener("click", function () {
            if (busy || !lastUserMessage) {
              return;
            }
            sendMessage(lastUserMessage);
          });
        }

        if (historyListEl) {
          var touchStartX = null;
          historyListEl.addEventListener("touchstart", function (e) {
            touchStartX = e.changedTouches[0].clientX;
          });
          historyListEl.addEventListener("touchend", function (e) {
            if (touchStartX === null) {
              return;
            }
            var dx = e.changedTouches[0].clientX - touchStartX;
            if (dx < -40) {
              pushSuggestion("History entry dismissed. Swipe right to refresh.");
              var target = e.target.closest(".history-item");
              if (target && target.parentNode) {
                target.parentNode.removeChild(target);
              }
            } else if (dx > 40) {
              refreshHistory();
              pushSuggestion("History refreshed.");
            }
          touchStartX = null;
        });
      }

        function renderHistory(data) {
          if (!historyListEl) {
            return;
          }
          historyListEl.innerHTML = "";
          lastHistoryData = data;
          if (!data || !data.sessions) {
            var empty = document.createElement("div");
            empty.className = "convo-meta";
            empty.textContent = "No research sessions yet.";
            historyListEl.appendChild(empty);
            return;
          }
          var summary = document.createElement("div");
          summary.className = "history-item";
          summary.innerHTML =
            "<strong>" +
            data.sessions +
            "</strong> sessions • " +
            (data.executed_queries || 0) +
            " queries • " +
            (data.sources_collected || 0) +
            " sources • avg $" +
            Number(data.avg_cost_usd || 0).toFixed(2);
          historyListEl.appendChild(summary);
          if (data.gap_counts && data.gap_counts.length) {
            var i;
            for (i = 0; i < data.gap_counts.length; i += 1) {
              var pair = data.gap_counts[i];
              var row = document.createElement("div");
              row.className = "history-item";
              row.textContent = pair[0] + ": " + pair[1];
              historyListEl.appendChild(row);
            }
          }

          // Render charts (lightweight via Chart.js CDN)
          var trend = Array.isArray(data.trend) ? data.trend : [];
          var filteredTrend = trend;
          var labels = filteredTrend.map(function (t) {
            return t.date.slice(5);
          });
          var sessionsData = filteredTrend.map(function (t) {
            return t.sessions;
          });
          var costData = filteredTrend.map(function (t) {
            return t.cost_usd;
          });
          var historyCtx = document.getElementById("history-chart");
          if (historyCtx && window.Chart) {
            if (historyChart) {
              historyChart.destroy();
            }
            historyChart = new Chart(historyCtx, {
              type: "line",
              data: {
                labels: labels,
                datasets: [
                  {
                    label: "Sessions",
                    data: sessionsData,
                    borderColor: "#38bdf8",
                    backgroundColor: "rgba(56,189,248,0.2)",
                    tension: 0.35,
                  },
                  {
                    label: "Cost ($)",
                    data: costData,
                    borderColor: "#22c55e",
                    backgroundColor: "rgba(34,197,94,0.2)",
                    tension: 0.35,
                  },
                ],
              },
              options: {
                scales: {
                  y: { beginAtZero: true, ticks: { color: "#cbd5e1" } },
                  x: { ticks: { color: "#cbd5e1" } },
                },
                plugins: { legend: { labels: { color: "#e5e7eb" } } },
              },
            });
          }
          var gapCtx = document.getElementById("gap-chart");
          if (gapCtx && window.Chart) {
            if (gapChart) {
              gapChart.destroy();
            }
            var gapLabels = (data.gap_counts || []).map(function (g) {
              return g[0];
            });
            var gapValues = (data.gap_counts || []).map(function (g) {
              return g[1];
            });
            gapChart = new Chart(gapCtx, {
              type: "doughnut",
              data: {
                labels: gapLabels,
                datasets: [
                  {
                    data: gapValues,
                    backgroundColor: ["#f97373", "#f59e0b", "#60a5fa", "#22c55e"],
                  },
                ],
              },
              options: {
                plugins: {
                  legend: { labels: { color: "#e5e7eb" } },
                },
              },
            });
          }

          // Update health usage bars if limits provided
          if (data && typeof data.hourly_limit === "number" && typeof data.queries_last_hour === "number") {
            var ratePct = data.hourly_limit ? Math.min(100, (data.queries_last_hour / data.hourly_limit) * 100) : 0;
            var costPct = data.cost_cap_usd ? Math.min(100, (data.cost_last_24h / data.cost_cap_usd) * 100) : 0;
            updateHealth(ratePct, costPct, "History updated");
          }
        }

        function refreshHistory() {
          var days = historyWindowSelect ? Number(historyWindowSelect.value) || 30 : 30;
          fetch("/dashboard/api/research-stats?days=" + days)
            .then(function (resp) {
              if (!resp.ok) {
                throw new Error("history_fetch_failed");
              }
              return resp.json();
            })
            .then(function (data) {
              renderHistory(data);
            })
            .catch(function () {
              if (historyListEl) {
                historyListEl.innerHTML = "";
                var err = document.createElement("div");
                err.className = "convo-meta";
                err.textContent = "History unavailable.";
                historyListEl.appendChild(err);
              }
              if (healthStatus) {
                healthStatus.textContent = "History fetch failed";
                healthStatus.className = "badge-gap stale";
              }
            });
        }

        if (refreshHistoryBtn) {
          refreshHistoryBtn.addEventListener("click", function () {
            refreshHistory();
          });
        }
        if (exportHistoryBtn) {
          exportHistoryBtn.addEventListener("click", function () {
            if (!lastHistoryData) {
              pushSuggestion("No history available to export yet.");
              return;
            }
            var rows = [];
            rows.push(["date", "sessions", "cost_usd"]);
            var trend = Array.isArray(lastHistoryData.trend) ? lastHistoryData.trend : [];
            trend.forEach(function (t) {
              rows.push([t.date, t.sessions, t.cost_usd]);
            });
            if (!trend.length && lastHistoryData.sessions) {
              rows.push([new Date().toISOString().slice(0, 10), lastHistoryData.sessions, lastHistoryData.avg_cost_usd || 0]);
            }
            var csv = rows.map(function (r) { return r.join(","); }).join("\\n");
            var blob = new Blob([csv], { type: "text/csv" });
            var url = URL.createObjectURL(blob);
            var a = document.createElement("a");
            a.href = url;
            a.download = "jarvis_research_history.csv";
            a.click();
            URL.revokeObjectURL(url);
            pushSuggestion("Exported research history CSV.");
          });
        }
        if (historyWindowSelect) {
          historyWindowSelect.addEventListener("change", function () {
            refreshHistory();
          });
        }
          if (historyGapSelect) {
            historyGapSelect.addEventListener("change", function () {
              // Gap filter is informational; suggest enabling research if gaps frequent.
              var val = historyGapSelect.value;
              if (val !== "all") {
                pushSuggestion("Filtered gaps: " + val + ". Enable research to reduce these occurrences.");
              }
            });
          }
        async function openDocViewer(docId) {
          if (!docViewer || !docBody || !docTitle) {
            return;
          }
          try {
            docBody.textContent = "Loading document...";
            docViewer.style.display = "flex";
            currentDocData = null;
            currentDocId = docId;
            var resp = await fetch("/api/memory/documents/" + docId);
            if (!resp.ok) {
              throw new Error("Failed to fetch document");
            }
            var data = await resp.json();
            docTitle.textContent = data.source_file || data.doc_key || "Document";
            docBody.textContent = data.content || "No content";
            currentDocData = data;
          } catch (err) {
            docBody.textContent = "Could not load document.";
          }
        }

        function openDocHtmlInTab(data) {
          if (!data) {
            pushSuggestion("No document loaded yet.");
            return;
          }
          var title = data.source_file || data.doc_key || "Document";
          var metaBits = [];
          if (data.domain) {
            metaBits.push("domain: " + data.domain);
          }
          if (data.doc_key) {
            metaBits.push("key: " + data.doc_key);
          }
          var metaLine = metaBits.length ? "<p><strong>Meta:</strong> " + metaBits.join(" • ") + "</p>" : "";
          var safeContent = String(data.content || "No content")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
          var html = '<!doctype html><html><head><meta charset="utf-8"><title>' +
            title +
            "</title><style>body{font-family:system-ui, -apple-system, Segoe UI, sans-serif;padding:16px;background:#0b1020;color:#e5e7eb;}pre{white-space:pre-wrap;word-break:break-word;border:1px solid #1f2933;padding:12px;border-radius:8px;background:#0f172a;}</style></head><body>" +
            "<h2>" + title + "</h2>" + metaLine + "<pre>" + safeContent + "</pre></body></html>";
          var blob = new Blob([html], { type: "text/html" });
          var url = URL.createObjectURL(blob);
          window.open(url, "_blank");
          window.setTimeout(function () { URL.revokeObjectURL(url); }, 30000);
        }

        function collapseForMobile() {
          if (window.innerWidth < 640) {
            var bodies = document.querySelectorAll(".info-card-body");
            bodies.forEach(function (body) {
              if (!body.contains(historyListEl) && !body.contains(suggestionsEl)) {
                body.classList.add("mobile-collapsed");
                body.classList.remove("open");
              }
            });
          }
        }

        function hideResearchProgress() {
          if (researchProgressTimer) {
            window.clearInterval(researchProgressTimer);
            researchProgressTimer = null;
          }
          researchStageIndex = 0;
          if (researchProgressEl) {
            researchProgressEl.style.display = "none";
          }
          announce("Research idle");
        }

        function updateResearchProgressStage(stage) {
          if (!researchProgressEl) {
            return;
          }
          var stageInfo = researchStages[Math.min(stage, researchStages.length - 1)];
          researchStageIndex = stage;
          researchProgressEl.style.display = "block";
          researchStageLabel.textContent = stageInfo.label;
          var pct = stageInfo.percent;
          researchProgressFill.style.width = pct + "%";
          researchPercent.textContent = pct + "%";
          var etaSeconds = Math.max(0, (researchStages.length - stage - 1) * 2);
          researchEta.textContent = "ETA: " + etaSeconds + "s";
          announce(stageInfo.label);
        }

        function startResearchProgress() {
          if (!researchCheckbox || !researchCheckbox.checked) {
            hideResearchProgress();
            return;
          }
          researchStageIndex = 0;
          updateResearchProgressStage(0);
          if (researchProgressTimer) {
            window.clearInterval(researchProgressTimer);
          }
          researchProgressTimer = window.setInterval(function () {
            researchStageIndex += 1;
            if (researchStageIndex >= researchStages.length) {
              researchStageIndex = researchStages.length - 1;
            }
            updateResearchProgressStage(researchStageIndex);
          }, 1200);
        }

        function completeResearchProgress(statusText) {
          if (!researchProgressEl) {
            return;
          }
          if (researchProgressTimer) {
            window.clearInterval(researchProgressTimer);
            researchProgressTimer = null;
          }
          researchStageLabel.textContent = statusText || "Research complete";
          researchProgressFill.style.width = "100%";
          researchPercent.textContent = "100%";
          researchEta.textContent = "ETA: 0s";
          announce(statusText || "Research complete");
          window.setTimeout(function () {
            hideResearchProgress();
          }, 900);
        }

        if (cancelResearchBtn) {
          cancelResearchBtn.addEventListener("click", function () {
            if (researchController) {
              researchController.abort();
            }
            hideResearchProgress();
            appendSystem("Research cancelled by user.", true);
          });
        }

        function appendMessage(role, content) {
          var row = document.createElement("div");
          row.className = "message-row " + role;

          var bubble = document.createElement("div");
          bubble.className = "bubble " + role;
          
          // Story 4-13: Render Markdown links (e.g. [text](url)) as clickable HTML links
          // Simple regex to replace [text](url) with <a href="url" target="_blank">text</a>
          // We escape HTML first to prevent XSS, then un-escape the link tags
          var safeContent = content
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
            
          var linkedContent = safeContent.replace(
            /\[([^\]]+)\]\(([^)]+)\)/g,
            '<a href="$2" target="_blank" style="color: #38bdf8; text-decoration: underline;">$1</a>'
          );
          
          bubble.innerHTML = linkedContent;
          row.appendChild(bubble);
          messagesEl.appendChild(row);

          messagesEl.scrollTop = messagesEl.scrollHeight;
          return row;
        }

        function appendSourcesRow(sources) {
          if (!sources || !sources.length) {
            return;
          }
          var row = document.createElement("div");
          row.className = "sources-row";

          var label = document.createElement("span");
          label.className = "convo-meta";
          label.textContent = "Sources:";
          row.appendChild(label);

          var i;
          for (i = 0; i < sources.length; i += 1) {
            var src = sources[i];
            var chip = document.createElement("span");
            var researched = Boolean(
              src.source_type === "web_research" ||
                src.researched === true ||
                src.recency_status === "FRESH" ||
                src.fresh === true
            );
            chip.className = "source-chip" + (researched ? " researched" : "");

            var id = src.id != null ? src.id : "?";
            var domain = src.domain || "";
            var file = src.source_file || "";
            var score = null;
            if (typeof src.score === "number") {
              score = src.score;
            } else if (src.relevance_score != null) {
              var numeric = Number(src.relevance_score);
              if (!isNaN(numeric)) {
                score = numeric;
              }
            }

            var labelText = "[" + id + "]" + (researched ? "✨" : "");
            if (domain) {
              labelText += " " + domain;
            } else if (file) {
              labelText += " " + file;
            }
            if (score !== null) {
              labelText += " s=" + score.toFixed(2);
            }
            chip.textContent = labelText;

            var section = src.section || "";
            var chunkId = src.chunk_id;
            var previewSource = src.content || "";
            var preview = String(previewSource);
            if (preview.length > 200) {
              preview = preview.slice(0, 197) + "...";
            }
            var tooltipParts = [];
            if (file) {
              var loc = file;
              if (chunkId) {
                loc += " [chunk " + chunkId + "]";
              }
              if (section) {
                loc += " | " + section;
              }
              tooltipParts.push(loc);
            }
            if (src.verified_at) {
              var rel = formatRelativeTime(src.verified_at);
              tooltipParts.push("Verified: " + src.verified_at + (rel ? " (" + rel + ")" : ""));
            }
            if (src.confidence != null) {
              tooltipParts.push("Confidence: " + Number(src.confidence).toFixed(2));
            }
            if (src.supersedes) {
              tooltipParts.push("Supersedes: " + src.supersedes);
              chip.setAttribute("data-supersedes", src.supersedes);
            }
            if (src.quality_score != null) {
              tooltipParts.push("Quality: " + Number(src.quality_score).toFixed(1));
            }
            tooltipParts.push(preview);
            var tooltip = tooltipParts.join(" :: ");
            chip.setAttribute("data-tooltip", tooltip);
            if (researched) {
              chip.setAttribute("title", "Researched in this session");
            }
            var docId = src.doc_id || src.doc_key;
            if (docId) {
              chip.setAttribute("data-doc-id", docId);
              chip.style.cursor = "pointer";
              chip.title = (chip.title || "") + " • click to view document";
            }

            chip.addEventListener("mouseenter", function (e) {
              var text = this.getAttribute("data-tooltip");
              if (!text) {
                return;
              }
              sourcesTooltip.textContent = text;
              var x = e.clientX + 12;
              var y = e.clientY + 12;
              sourcesTooltip.style.left = x + "px";
              sourcesTooltip.style.top = y + "px";
              sourcesTooltip.style.display = "block";
            });

            chip.addEventListener("mouseleave", function () {
              sourcesTooltip.style.display = "none";
            });

            chip.addEventListener("click", function () {
              var docId = this.getAttribute("data-doc-id");
              if (docId) {
                openDocViewer(docId);
                return;
              }
              if (this._timelineShown) {
                return;
              }
              this._timelineShown = true;
              var detail = document.createElement("div");
              detail.className = "timeline";
              var parts = this.getAttribute("data-tooltip");
              var metaLines = parts ? parts.split(" :: ") : [];
              var chain = document.createElement("div");
              chain.className = "timeline-item";
              chain.textContent = metaLines.join(" → ");
              detail.appendChild(chain);
              var prev = this.getAttribute("data-supersedes");
              if (prev) {
                var prevLine = document.createElement("div");
                prevLine.className = "timeline-item";
                prevLine.textContent = "Updated from previous version: " + prev;
                detail.appendChild(prevLine);
              }
              row.appendChild(detail);
            });

            row.appendChild(chip);
          }

          messagesEl.appendChild(row);
          messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        function buildProgressRow(label, percent, suffix, severity) {
          var row = document.createElement("div");
          row.className = "progress-row";
          var header = document.createElement("div");
          header.className = "progress-label";
          var name = document.createElement("span");
          name.textContent = label;
          var value = document.createElement("span");
          value.textContent = percent.toFixed(1) + (suffix || "%");
          header.appendChild(name);
          header.appendChild(value);
          var bar = document.createElement("div");
          bar.className = "progress-bar";
          var fill = document.createElement("div");
          fill.className = "progress-bar-fill";
          fill.style.width = Math.max(0, Math.min(100, percent)) + "%";
          if (severity === "warn") {
            fill.style.background = "linear-gradient(90deg, #f97373, #f59e0b)";
          }
          bar.appendChild(fill);
          row.appendChild(header);
          row.appendChild(bar);
          return row;
        }

        function appendPlannerActions(actions, traceId) {
          if (!actions || !actions.length) return;

          var row = document.createElement("div");
          row.className = "sources-row";
          row.style.marginTop = "12px";

          var label = document.createElement("span");
          label.className = "convo-meta";
          label.textContent = "🧠 Planner Actions:";
          label.style.marginBottom = "8px";
          label.style.display = "block";
          row.appendChild(label);

          actions.forEach(function(action) {
            var actionDiv = document.createElement("div");
            actionDiv.style.padding = "8px 12px";
            actionDiv.style.margin = "4px 0";
            actionDiv.style.background = "rgba(56, 189, 248, 0.1)";
            actionDiv.style.borderLeft = "3px solid var(--accent)";
            actionDiv.style.borderRadius = "4px";
            actionDiv.style.fontSize = "12px";

            var actionType = document.createElement("div");
            actionType.style.fontWeight = "600";
            actionType.style.color = "var(--accent)";
            actionType.style.marginBottom = "4px";
            actionType.textContent = action.action;
            actionDiv.appendChild(actionType);

            var actionReason = document.createElement("div");
            actionReason.style.color = "var(--text-muted)";
            actionReason.style.fontSize = "11px";
            actionReason.textContent = action.reason;
            actionDiv.appendChild(actionReason);

            row.appendChild(actionDiv);
          });

          // Add "View Full Trace" button
          var traceBtn = document.createElement("button");
          traceBtn.className = "pill";
          traceBtn.textContent = "🔍 View Full Trace";
          traceBtn.style.marginTop = "8px";
          traceBtn.style.fontSize = "11px";
          traceBtn.addEventListener("click", function() {
            openTraceViewer(traceId);
          });
          row.appendChild(traceBtn);

          messagesEl.appendChild(row);
          messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        function appendTraceButton(traceId) {
          if (!traceId) return;

          var row = document.createElement("div");
          row.className = "sources-row";
          row.style.marginTop = "8px";

          var traceBtn = document.createElement("button");
          traceBtn.className = "pill";
          traceBtn.textContent = "🔍 View Cognitive Trace";
          traceBtn.style.fontSize = "11px";
          traceBtn.addEventListener("click", function() {
            openTraceViewer(traceId);
          });
          row.appendChild(traceBtn);

          messagesEl.appendChild(row);
          messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        // Story 4-9: Primary document viewer
        function appendPrimaryDocViewer(primaryDoc) {
          if (!primaryDoc || (!primaryDoc.doc_key && !primaryDoc.source_file)) {
            return;
          }
          var container = document.createElement("div");
          container.className = "primary-doc-viewer";
          
          var toggle = document.createElement("button");
          toggle.className = "primary-doc-toggle";
          var filename = primaryDoc.source_file ? primaryDoc.source_file.split('/').pop() : 'Document';
          toggle.innerHTML = '<span class="doc-icon">&#x1F4C4;</span> View full ' + filename + ' <span class="chevron">&#x25BC;</span>';
          
          var content = document.createElement("div");
          content.className = "primary-doc-content";
          content.innerHTML = '<span class="primary-doc-loading">Click to load...</span>';
          
          var loaded = false;
          toggle.addEventListener("click", function() {
            var isOpen = content.classList.contains("open");
            if (isOpen) {
              content.classList.remove("open");
              toggle.querySelector('.chevron').innerHTML = '&#x25BC;';
            } else {
              content.classList.add("open");
              toggle.querySelector('.chevron').innerHTML = '&#x25B2;';
              if (!loaded) {
                loaded = true;
                content.innerHTML = '<span class="primary-doc-loading">Loading document...</span>';
                fetch("/api/docs/" + encodeURIComponent(primaryDoc.doc_key))
                  .then(function(resp) {
                    console.log('[Primary Doc] Fetch response status:', resp.status);
                    if (!resp.ok) {
                      throw new Error('HTTP ' + resp.status);
                    }
                    return resp.json();
                  })
                  .then(function(data) {
                    console.log('[Primary Doc] Data received:', data ? 'has content' : 'no data', 'content length:', data && data.content ? data.content.length : 0, 'is_large:', data.is_large);
                    
                    // For large files, show Open in New Tab button
                    if (data.is_large) {
                      var sizeKB = Math.round((data.content_size || 0) / 1024);
                      content.innerHTML = '<div style="text-align:center;padding:20px;">' +
                        '<p style="color:var(--text-muted);margin-bottom:12px;">Document is large (' + sizeKB + ' KB) - better viewed in a new tab.</p>' +
                        '<button class="pill" id="open-doc-tab-btn" style="font-size:12px;padding:8px 16px;">&#x1F4C4; Open Full Document in New Tab</button>' +
                        '</div>';
                      var openBtn = content.querySelector('#open-doc-tab-btn');
                      if (openBtn) {
                        openBtn.addEventListener('click', function() {
                          window.open('/api/docs/' + encodeURIComponent(primaryDoc.doc_key) + '?format=html', '_blank');
                        });
                      }
                    } else {
                      content.textContent = data.content || 'No content';
                      if (data.truncated) {
                        content.textContent += String.fromCharCode(10,10) + '[Document truncated for display]';
                      }
                    }
                  })
                  .catch(function(err) {
                    console.error('[Primary Doc] Fetch error:', err);
                    content.innerHTML = '<span class="primary-doc-loading">Could not load document: ' + err.message + '</span>';
                  });
              }
            }
          });
          
          container.appendChild(toggle);
          container.appendChild(content);
          messagesEl.appendChild(container);
          messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        function appendGapAnalysis(gap) {
          if (!gap) {
            return;
          }
          var card = document.createElement("div");
          card.className = "info-card";
          var header = document.createElement("div");
          header.className = "info-card-header";
          var title = document.createElement("div");
          title.className = "info-card-title";
          title.textContent = "Gap Analysis";
          header.appendChild(title);

          var badges = document.createElement("div");
          badges.style.display = "flex";
          badges.style.gap = "4px";
          var recencyClass = gap.recency_status ? gap.recency_status.toLowerCase() : "";
          if (recencyClass && recencyClass !== "fresh") {
            var recencyBadge = document.createElement("span");
            recencyBadge.className = "badge-gap " + recencyClass;
            recencyBadge.textContent = gap.recency_status;
            badges.appendChild(recencyBadge);
          }
          if (gap.coverage_gap) {
            var covBadge = document.createElement("span");
            covBadge.className = "badge-gap missing";
            covBadge.textContent = "MISSING";
            badges.appendChild(covBadge);
          }
          if (gap.contradictory) {
            var contraBadge = document.createElement("span");
            contraBadge.className = "badge-gap contradictory";
            contraBadge.textContent = "CONTRADICTORY";
            badges.appendChild(contraBadge);
          }
          header.appendChild(badges);

          var body = document.createElement("div");
          body.className = "info-card-body";

          var coveragePct = (gap.coverage_score || 0) * 100;
          body.appendChild(
            buildProgressRow("Coverage", coveragePct, "%", gap.coverage_gap ? "warn" : null)
          );
          var recencyDays = gap.recency_average_days || gap.recency_oldest_days || 0;
          var recencyPct = Math.max(0, Math.min(100, (recencyDays / 180) * 100));
          var recencyLabel = document.createElement("div");
          recencyLabel.className = "convo-meta";
          recencyLabel.textContent =
            "Recency: " +
            (gap.recency_status || "UNKNOWN") +
            (recencyDays ? " (" + recencyDays.toFixed(0) + "d old)" : "");
          body.appendChild(recencyLabel);
          body.appendChild(
            buildProgressRow("Recency age", recencyPct, "%", gap.recency_gap ? "warn" : null)
          );
          var coherencePct = (gap.coherence_score || 0) * 100;
          body.appendChild(
            buildProgressRow("Coherence", coherencePct, "%", gap.contradictory ? "warn" : null)
          );

          var terms = document.createElement("div");
          terms.className = "convo-meta";
          terms.textContent =
            "Grounded: " +
            (gap.grounded_terms || []).join(", ") +
            " | Missing: " +
            (gap.missing_terms || []).join(", ");
          body.appendChild(terms);

          var autoExpand = Boolean(gap.coverage_gap || gap.recency_gap || gap.contradictory);
          if (autoExpand) {
            body.classList.add("open");
          }
          header.addEventListener("click", function () {
            body.classList.toggle("open");
          });
          card.appendChild(header);
          card.appendChild(body);
          messagesEl.appendChild(card);
          messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        function appendResearchSummaryCard(summary, metadata) {
          if (!summary) {
            return;
          }
          var card = document.createElement("div");
          card.className = "info-card";
          var header = document.createElement("div");
          header.className = "info-card-header";
          var title = document.createElement("div");
          title.className = "info-card-title";
          title.textContent = "Research Summary";
          header.appendChild(title);
          var badge = document.createElement("span");
          badge.className = "badge-gap " + (summary.triggered ? "contradictory" : "");
          badge.textContent = summary.triggered ? "Triggered" : "Not triggered";
          header.appendChild(badge);
          var body = document.createElement("div");
          body.className = "info-card-body open";

          var grid = document.createElement("div");
          grid.className = "research-summary-grid";
          var queries = document.createElement("div");
          queries.className = "summary-pill";
          queries.textContent =
            "Executed: " + (summary.executed_queries || 0) + " / Planned: " + summary.planned_queries.length;
          grid.appendChild(queries);
          var sources = document.createElement("div");
          sources.className = "summary-pill";
          sources.textContent = "Sources collected: " + (summary.sources_collected || 0);
          grid.appendChild(sources);
          var provider = document.createElement("div");
          provider.className = "summary-pill";
          var cost = metadata && metadata.cost_usd != null ? metadata.cost_usd : 0;
          provider.textContent =
            "Cost: $" +
            Number(cost).toFixed(2) +
            (metadata && metadata.llm_provider ? " • " + metadata.llm_provider : "");
          grid.appendChild(provider);
          body.appendChild(grid);

          if (summary.planned_queries && summary.planned_queries.length) {
            var list = document.createElement("div");
            list.className = "convo-meta";
            list.textContent = "Queries:";
            body.appendChild(list);
            var i;
            for (i = 0; i < summary.planned_queries.length; i += 1) {
              var q = document.createElement("div");
              q.className = "summary-pill";
              q.textContent = "🔎 " + summary.planned_queries[i];
              body.appendChild(q);
            }
          }

          if (summary.confidence_before != null || summary.confidence_after != null) {
            var before = summary.confidence_before || 0;
            var after = summary.confidence_after || 0;
            var delta = summary.confidence_delta || after - before;
            var deltaRow = document.createElement("div");
            deltaRow.className = "progress-row";
            var deltaLabel = document.createElement("div");
            deltaLabel.className = "progress-label";
            deltaLabel.textContent =
              "Confidence delta: " +
              (before * 100).toFixed(0) +
              "% → " +
              (after * 100).toFixed(0) +
              "% (" +
              delta.toFixed(2) +
              ")";
            deltaRow.appendChild(deltaLabel);
            var deltaBar = document.createElement("div");
            deltaBar.className = "progress-bar";
            var deltaFill = document.createElement("div");
            deltaFill.className = "progress-bar-fill";
            deltaFill.style.width = Math.min(100, Math.max(0, after * 100)) + "%";
            deltaBar.appendChild(deltaFill);
            deltaRow.appendChild(deltaBar);
            body.appendChild(deltaRow);
          }

          header.addEventListener("click", function () {
            body.classList.toggle("open");
          });
          card.appendChild(header);
          card.appendChild(body);
          messagesEl.appendChild(card);
          messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        function appendSystem(content, isError) {
          var row = document.createElement("div");
          row.className = "message-row";

          var bubble = document.createElement("div");
          bubble.className = "bubble system";
          if (isError) {
            bubble.classList.add("error");
          }
          bubble.textContent = content;
          row.appendChild(bubble);
          messagesEl.appendChild(row);
          messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        function ensureConversation() {
          if (conversationId) {
            return Promise.resolve(conversationId);
          }
          return fetch("/api/conversations", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: "web-ui" }),
          }).then(function (resp) {
            if (!resp.ok) {
              throw new Error("Failed to create conversation");
            }
            return resp.json();
          }).then(function (data) {
            conversationId = data.id;
            window.localStorage.setItem("jarvis_conversation_id", conversationId);
            return conversationId;
          });
        }

        function loadHistory() {
          if (!conversationId) {
            appendSystem(
              "New BMAD session. Your messages & answers will be logged into Jarvis conversations.",
              false
            );
            return;
          }
          var historyUrl = "/api/conversations/" + conversationId + "?page_size=500";
          fetch(historyUrl)
            .then(function (resp) {
              if (!resp.ok) {
                throw new Error("Failed to load history");
              }
              return resp.json();
            })
            .then(function (data) {
              messagesEl.innerHTML = "";
              appendSystem(
                "BMAD chat ready. Ask Jarvis about architecture, epics, or time-aware retrieval.",
                false
              );
              var i;
              for (i = 0; i < data.messages.length; i += 1) {
                var msg = data.messages[i];
                if (msg.role === "system") {
                  appendSystem(msg.content, false);
                } else if (msg.role === "assistant") {
                  appendMessage("assistant", msg.content);
                  if (msg.citation_provenance && msg.citation_provenance.length) {
                    appendSourcesRow(msg.citation_provenance);
                  }
                } else {
                  appendMessage("user", msg.content);
                }
              }
              
              // Story 4-13: Restore primary doc viewer if persisted
              var storedDoc = window.localStorage.getItem("jarvis_primary_doc_" + conversationId);
              if (storedDoc) {
                try {
                  var primaryDoc = JSON.parse(storedDoc);
                  appendPrimaryDocViewer(primaryDoc);
                } catch (e) {
                  console.error("Failed to parse stored primary doc", e);
                }
              }
            })
            .catch(function () {
              appendSystem(
                "Could not load previous conversation. Starting fresh.",
                true
              );
              conversationId = null;
              window.localStorage.removeItem("jarvis_conversation_id");
            });
        }

        function renderFilteredConvos() {
          if (!convoListEl) {
            return;
          }
          
          // Apply filters
          var filtered = allConvos.filter(function(item) {
            // Search filter
            if (convoSearchTerm) {
              var text = (item.last_message || "").toLowerCase();
              if (text.indexOf(convoSearchTerm) === -1) {
                return false;
              }
            }
            
            // Date filter
            if (convoDateFilter !== "all" && item.created_at) {
              var now = new Date();
              var itemDate = new Date(item.created_at);
              var diffDays = (now - itemDate) / (1000 * 60 * 60 * 24);
              
              if (convoDateFilter === "today" && diffDays > 1) return false;
              if (convoDateFilter === "week" && diffDays > 7) return false;
              if (convoDateFilter === "month" && diffDays > 30) return false;
            }
            
            // Persona filter
            if (convoPersonaFilter !== "all" && item.last_persona) {
              if (item.last_persona !== convoPersonaFilter) return false;
            }
            
            return true;
          });
          
          // Apply sorting
          filtered.sort(function(a, b) {
            if (convoSortBy === "newest") {
              return new Date(b.created_at || 0) - new Date(a.created_at || 0);
            } else if (convoSortBy === "oldest") {
              return new Date(a.created_at || 0) - new Date(b.created_at || 0);
            } else if (convoSortBy === "most-messages") {
              return (b.message_count || 0) - (a.message_count || 0);
            }
            return 0;
          });
          
          // Render
          convoListEl.innerHTML = "";
          if (!filtered.length) {
            var empty = document.createElement("div");
            empty.className = "convo-meta";
            empty.textContent = convoSearchTerm ? "No matching conversations." : "No conversations yet.";
            convoListEl.appendChild(empty);
            return;
          }
          
          for (var i = 0; i < filtered.length; i++) {
            (function() {
              var item = filtered[i];
              
              // Wrapper for hover effects
              var wrapper = document.createElement("div");
              wrapper.className = "convo-item-wrapper";
              
              // Main item element
              var el = document.createElement("div");
              el.className = "convo-item";
              if (conversationId && item.id === conversationId) {
                el.className += " active";
              }
              
              var title = document.createElement("div");
              title.className = "convo-title";
              var text = item.last_message || "(no messages)";
              if (text.length > 60) {
                text = text.slice(0, 57) + "...";
              }
              title.textContent = text;
              
              var meta = document.createElement("div");
              meta.className = "convo-meta";
              meta.textContent = item.message_count + " message(s)";
              
              el.appendChild(title);
              el.appendChild(meta);
              el.setAttribute("role", "button");
              el.setAttribute("tabindex", "0");
              
              // Click to load conversation
              el.addEventListener("click", function () {
                conversationId = item.id;
                window.localStorage.setItem("jarvis_conversation_id", conversationId);
                messagesEl.innerHTML = "";
                loadHistory();
                renderFilteredConvos();
              });
              
              // Keyboard navigation
              el.addEventListener("keydown", function(e) {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  el.click();
                }
              });
              
              // Hover preview
              wrapper.addEventListener("mouseenter", function(e) {
                previewTooltip.innerHTML = "<div class='convo-preview-title'>" + (item.last_message || "No messages") + "</div>" +
                  "<div class='convo-preview-meta'>" + item.message_count + " messages • " + formatRelativeTime(item.created_at) + "</div>" +
                  "<div class='convo-preview-content'>" + (item.last_message || "") + "</div>";
                previewTooltip.className = "convo-preview-tooltip show";
                previewTooltip.style.left = (e.pageX + 10) + "px";
                previewTooltip.style.top = (e.pageY + 10) + "px";
              });
              
              wrapper.addEventListener("mousemove", function(e) {
                previewTooltip.style.left = (e.pageX + 10) + "px";
                previewTooltip.style.top = (e.pageY + 10) + "px";
              });
              
              wrapper.addEventListener("mouseleave", function() {
                previewTooltip.className = "convo-preview-tooltip";
              });
              
              // Action buttons
              var actions = document.createElement("div");
              actions.className = "convo-item-actions";
              
              var archiveBtn = document.createElement("button");
              archiveBtn.className = "convo-action-btn archive";
              archiveBtn.textContent = "\u2193";
              archiveBtn.title = "Archive";
              archiveBtn.addEventListener("click", function(e) {
                e.stopPropagation();
                if (confirm("Archive this conversation?")) {
                  // TODO: API call to archive
                  console.log("Archive conversation", item.id);
                  allConvos = allConvos.filter(function(c) { return c.id !== item.id; });
                  renderFilteredConvos();
                }
              });
              
              var deleteBtn = document.createElement("button");
              deleteBtn.className = "convo-action-btn delete";
              deleteBtn.textContent = "\u00d7";
              deleteBtn.title = "Delete";
              deleteBtn.addEventListener("click", function(e) {
                e.stopPropagation();
                if (confirm("Permanently delete this conversation?")) {
                  fetch("/api/conversations/" + item.id, { method: "DELETE" })
                    .then(function(resp) {
                      if (resp.ok) {
                        allConvos = allConvos.filter(function(c) { return c.id !== item.id; });
                        renderFilteredConvos();
                        if (conversationId === item.id) {
                          conversationId = null;
                          window.localStorage.removeItem("jarvis_conversation_id");
                          messagesEl.innerHTML = "";
                        }
                      } else {
                        alert("Failed to delete conversation");
                      }
                    })
                    .catch(function() {
                      alert("Error deleting conversation");
                    });
                }
              });
              
              actions.appendChild(archiveBtn);
              actions.appendChild(deleteBtn);
              
              wrapper.appendChild(el);
              wrapper.appendChild(actions);
              convoListEl.appendChild(wrapper);
            })();
          }
        }

        function loadConversationsList(append) {
          if (!convoListEl || convoLoading) {
            return;
          }
          
          convoLoading = true;
          if (loadMoreConvosBtn) {
            loadMoreConvosBtn.disabled = true;
            loadMoreConvosBtn.textContent = "Loading...";
          }
          
          var offset = append ? convoOffset : 0;
          fetch("/api/conversations?limit=" + convoLimit + "&offset=" + offset)
            .then(function (resp) {
              if (!resp.ok) {
                throw new Error("Failed to list conversations");
              }
              return resp.json();
            })
            .then(function (items) {
              if (append) {
                allConvos = allConvos.concat(items || []);
              } else {
                allConvos = items || [];
                convoOffset = 0;
              }
              
              hasMoreConvos = items && items.length === convoLimit;
              convoOffset += (items || []).length;
              
              if (loadMoreConvosBtn) {
                loadMoreConvosBtn.style.display = hasMoreConvos ? "block" : "none";
                loadMoreConvosBtn.disabled = false;
                loadMoreConvosBtn.textContent = "Load More...";
              }
              
              renderFilteredConvos();
            })
            .catch(function (err) {
              console.error("Failed to load conversations:", err);
              if (loadMoreConvosBtn) {
                loadMoreConvosBtn.disabled = false;
                loadMoreConvosBtn.textContent = "Load More...";
              }
            })
            .finally(function() {
              convoLoading = false;
            });
        }

        // Search input with debounce
        if (convoSearchEl) {
          var debouncedSearch = debounce(function() {
            convoSearchTerm = convoSearchEl.value.toLowerCase();
            renderFilteredConvos();
          }, 300);
          
          convoSearchEl.addEventListener("input", debouncedSearch);
        }
        
        // Load More button
        if (loadMoreConvosBtn) {
          loadMoreConvosBtn.addEventListener("click", function() {
            loadConversationsList(true); // append = true
          });
        }

        function sendMessage(content) {
          if (!content || !content.trim() || busy) {
            return;
          }
          // Capture checkbox states at function scope for use in promise callbacks
          var autoGrounding = autoGroundingCheckbox ? autoGroundingCheckbox.checked : true;
          var showConfidence = showConfidenceCheckbox ? showConfidenceCheckbox.checked : false;
          // Use selectedDomains from checkbox UI instead of deprecated sourceInput (Story 4.5.7)
          var sourceDomain = selectedDomains.length > 0 ? selectedDomains.join(",") : "";
          var useResearch = researchCheckbox ? researchCheckbox.checked : false;
          var filterTags = selectedTags.length > 0 ? selectedTags : [];

          ensureConversation()
            .then(function () {
              appendMessage("user", content);
              inputEl.value = "";
              lastUserMessage = content;

              busy = true;
              sendBtn.disabled = true;
              statusPill.textContent = "Thinking | memory+llm";
              if (useResearch) {
                startResearchProgress();
                researchController = new AbortController();
              } else {
                hideResearchProgress();
                researchController = null;
              }
              var payload = {
                message: content,
                conversation_id: conversationId,
                user_id: "web-ui",
                k: 15,  // Maxed for better context
                expand: 3,
                source: sourceDomain || null,
                tags: filterTags.length > 0 ? filterTags : null,
                auto_grounding: autoGrounding,
                show_confidence: showConfidence,
                grounding_level: null,  // Let auto-grounding decide
                enable_research: useResearch,
              };
              return fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
                signal: researchController ? researchController.signal : undefined,
              });
            })
            .then(function (resp) {
              if (!resp) {
                return;
              }
              if (!resp.ok) {
                var status = resp.status;
                return resp.text().then(function (txt) {
                  var message = txt || "Request failed";
                  throw new Error(status + "::" + message);
                });
              }
              return resp.json();
            })
            .then(function (data) {
              if (!data) {
                return;
              }
              if (!data.conversation_id) {
                throw new Error("Invalid response from server");
              }
              conversationId = data.conversation_id;
              window.localStorage.setItem("jarvis_conversation_id", conversationId);

              if (data.response === null) {
                appendSystem(
                  "Jarvis could not find enough grounded context yet. Try broadening your question or ingesting more docs.",
                  false
                );
              } else {
                appendMessage("assistant", data.response);

                // AC5 - Planner Actions Display (Story 4.5.7)
                if (data.trace_id) {
                  fetch("/traces/" + data.trace_id)
                    .then(function(resp) { return resp.ok ? resp.json() : null; })
                    .then(function(trace) {
                      if (trace && trace.planner_actions && trace.planner_actions.length > 0) {
                        appendPlannerActions(trace.planner_actions, data.trace_id);
                      } else if (trace) {
                        // Still show trace button even if no planner actions
                        appendTraceButton(data.trace_id);
                      }
                    })
                    .catch(function() { /* ignore trace errors */ });
                }

                if (data.metadata && data.metadata.gap_analysis) {
                  appendGapAnalysis(data.metadata.gap_analysis);
                }
                if (data.metadata && data.metadata.research_summary) {
                  appendResearchSummaryCard(data.metadata.research_summary, data.metadata);
                }
                if (data.sources && data.sources.length) {
                  appendSourcesRow(data.sources);
                }
                // Story 4-9: Primary document viewer
                if (data.primary_doc) {
                  // Story 4-13: Persist primary doc in localStorage
                  window.localStorage.setItem("jarvis_primary_doc_" + conversationId, JSON.stringify(data.primary_doc));
                  appendPrimaryDocViewer(data.primary_doc);
                }
              }
              if (data.metadata && data.metadata.gap_analysis && !useResearch) {
                var ga = data.metadata.gap_analysis;
                if (ga.coverage_gap || ga.recency_gap || ga.contradictory) {
                  pushSuggestion(
                    "Gaps detected (" +
                      (ga.recency_status || "STALE") +
                      "). Enable research to auto-fill missing knowledge."
                  );
                }
              }
              if (
                data.metadata &&
                data.metadata.research_summary &&
                data.metadata.research_summary.triggered &&
                data.metadata.research_summary.executed_queries <
                  data.metadata.research_summary.planned_queries.length
              ) {
                appendSystem(
                  "Research partially completed (" +
                    data.metadata.research_summary.executed_queries +
                    "/" +
                    data.metadata.research_summary.planned_queries.length +
                    "). You can retry to complete remaining queries.",
                  true
                );
                pushSuggestion("Research partially failed; click Retry last to attempt again.");
              }
              if (data.metadata && data.metadata.research_summary && data.metadata.research_summary.triggered) {
                completeResearchProgress("Research complete");
                updateHealth(0, 0, "Research healthy");
                timeSensitiveHits = 0;
                window.localStorage.setItem("jarvis_time_sensitive_hits", "0");
              } else {
                hideResearchProgress();
              }
            })
            .catch(function (err) {
              if (err && err.name === "AbortError") {
                appendSystem("Research request cancelled.", true);
              } else {
                var message = err && err.message ? err.message : "";
                if (message.indexOf("429::") === 0) {
                  appendSystem(
                    "Research rate limit reached for this hour. Try again later or lower queries.",
                    true
                  );
                  pushSuggestion("Rate limit hit — reduce max queries or wait to retry.");
                  updateHealth(100, null, "Rate limit reached");
                } else if (message.indexOf("402::") === 0) {
                  appendSystem(
                    "Research cost cap exceeded for this session. Increase cap or retry later.",
                    true
                  );
                  pushSuggestion("Cost cap reached — raise cap in settings if needed.");
                  updateHealth(null, 100, "Cost cap reached");
                } else {
                  appendSystem(
                    "Something went wrong talking to Jarvis. Check that the API is up and Postgres/Qdrant are reachable.",
                    true
                  );
                }
                appendSystem(
                  "Details: " + (message || "Unknown error"),
                  true
                );
              }
              hideResearchProgress();
            })
            .finally(function () {
              busy = false;
              sendBtn.disabled = false;
              statusPill.textContent = "Connected | memory+llm";
              loadConversationsList();
            });
        }

        if (formEl) {
          formEl.addEventListener("submit", function (e) {
            e.preventDefault();
            if (busy) {
              return;
            }
            var text = inputEl.value;
            sendMessage(text);
          });
        }

        if (inputEl) {
          inputEl.addEventListener("keydown", function (e) {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (!busy) {
                var text = inputEl.value;
                sendMessage(text);
              }
            }
            if (e.ctrlKey || e.metaKey) {
              if (e.key.toLowerCase() === "r") {
                e.preventDefault();
                if (researchCheckbox) {
                  researchCheckbox.checked = !researchCheckbox.checked;
                  window.localStorage.setItem(
                    "jarvis_enable_research",
                    researchCheckbox.checked ? "true" : "false"
                  );
                  pushSuggestion(
                    researchCheckbox.checked
                      ? "Research enabled — gap detection will trigger autonomous research."
                      : "Research disabled — responses will use memory only."
                  );
                  timeSensitiveHits = 0;
                  window.localStorage.setItem("jarvis_time_sensitive_hits", "0");
                }
              }
              if (e.shiftKey && e.key.toLowerCase() === "s") {
                e.preventDefault();
                if (researchSettingsBtn) {
                  researchSettingsBtn.click();
                }
              }
            }
          });
          inputEl.addEventListener("input", function () {
            if (!researchCheckbox || researchCheckbox.checked) {
              return;
            }
            var text = inputEl.value.toLowerCase();
            if (text.indexOf("latest") !== -1 || text.indexOf("current") !== -1 || text.match(/\\b20\\d{2}\\b/)) {
              pushSuggestion("This looks time-sensitive. Consider enabling research for fresher sources.");
              timeSensitiveHits += 1;
              window.localStorage.setItem("jarvis_time_sensitive_hits", String(timeSensitiveHits));
              if (!autoEnabledFromLearning && timeSensitiveHits >= autoEnableThreshold) {
                autoEnabledFromLearning = true;
                if (researchCheckbox) {
                  researchCheckbox.checked = true;
                  window.localStorage.setItem("jarvis_enable_research", "true");
                  appendSystem("Research auto-enabled based on your recent queries.", false);
                  announce("Research enabled automatically based on query pattern.");
                }
              }
            }
          });
        }

        // Search/filter for conversations
        if (convoSearchEl) {
          convoSearchEl.addEventListener("input", function() {
            renderFilteredConvos();
          });
        }
        
        // Load More button
        if (loadMoreConvosBtn) {
          loadMoreConvosBtn.addEventListener("click", function() {
            loadConversationsList(true); // append = true
          });
        }

        // Panel collapse/expand functionality
        var panelHeaders = document.querySelectorAll('.info-card-header[data-panel]');
        panelHeaders.forEach(function(header) {
          var panelId = header.dataset.panel;
          var bodyEl = header.nextElementSibling;
          
          // Load collapse state from localStorage
          var isCollapsed = window.localStorage.getItem('jarvis_panel_' + panelId + '_collapsed') === 'true';
          
          if (isCollapsed) {
            bodyEl.classList.remove('open');
            header.setAttribute('aria-expanded', 'false');
          } else {
            bodyEl.classList.add('open');
            header.setAttribute('aria-expanded', 'true');
          }
          
          // Click handler to toggle
          header.addEventListener('click', function(e) {
            // Don't toggle if clicking on a button
            if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
              return;
            }
            
            var isOpen = bodyEl.classList.contains('open');
            
            if (isOpen) {
              bodyEl.classList.remove('open');
              header.setAttribute('aria-expanded', 'false');
              window.localStorage.setItem('jarvis_panel_' + panelId + '_collapsed', 'true');
            } else {
              bodyEl.classList.add('open');
              header.setAttribute('aria-expanded', 'true');
              window.localStorage.setItem('jarvis_panel_' + panelId + '_collapsed', 'false');
            }
          });
        });
        
        // Collapse for mobile helper
        function collapseForMobile() {
          if (window.innerWidth <= 640) {
            document.querySelectorAll('.info-card-body.open').forEach(function(bodyEl) {
              bodyEl.classList.add('mobile-collapsed');
            });
          } else {
            document.querySelectorAll('.info-card-body.mobile-collapsed').forEach(function(bodyEl) {
              bodyEl.classList.remove('mobile-collapsed');
            });
          }
        }

        // Search input with debounce
        if (convoSearchEl) {
          var debouncedSearch = debounce(function() {
            convoSearchTerm = convoSearchEl.value.toLowerCase();
            renderFilteredConvos();
          }, 300);
          
          convoSearchEl.addEventListener("input", debouncedSearch);
        }
        
        // Filter dropdowns
        if (convoSortEl) {
          convoSortEl.addEventListener("change", function() {
            convoSortBy = convoSortEl.value;
            renderFilteredConvos();
          });
        }
        
        if (convoDateFilterEl) {
          convoDateFilterEl.addEventListener("change", function() {
            convoDateFilter = convoDateFilterEl.value;
            renderFilteredConvos();
          });
        }
        
        if (convoPersonaFilterEl) {
          convoPersonaFilterEl.addEventListener("change", function() {
            convoPersonaFilter = convoPersonaFilterEl.value;
            renderFilteredConvos();
          });
        }
        
        // Load More button
        if (loadMoreConvosBtn) {
          loadMoreConvosBtn.addEventListener("click", function() {
            loadConversationsList(true); // append = true
          });
        }
        
        // Ctrl+F keyboard shortcut
        document.addEventListener("keydown", function(e) {
          if ((e.ctrlKey || e.metaKey) && e.key === "f" && convoSearchEl) {
            // Only intercept if not already in an input
            if (document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") {
              e.preventDefault();
              convoSearchEl.focus();
              convoSearchEl.select();
            }
          }
        });

        // Initial load
        loadHistory();
        loadConversationsList();
        refreshHistory();
        collapseForMobile();
        window.addEventListener("resize", collapseForMobile);

        // Load saved filters from localStorage
        var savedDomains = window.localStorage.getItem("jarvis_domains");
        if (savedDomains) {
          selectedDomains = savedDomains.split(",").filter(function(d) { return d.length > 0; });
        }
        var savedTags = window.localStorage.getItem("jarvis_tags");
        if (savedTags) {
          selectedTags = savedTags.split(",").filter(function(t) { return t.length > 0; });
        }

        loadDomains();
        loadTags();

        // Render active filters after a short delay to ensure DOM is ready
        setTimeout(function() {
          updateSelectedDomainsCount();
          updateSelectedTagsCount();
          renderActiveFilters();
        }, 100);

        // Session Auto-Update (AC7 - Story 4.5.7)
        var cachedDomains = [];
        var cachedTags = [];
        var AUTO_UPDATE_INTERVAL = 30000; // 30 seconds

        function checkForDomainUpdates() {
          fetch("/api/memory/domains/metadata")
            .then(function(resp) { return resp.ok ? resp.json() : null; })
            .then(function(data) {
              if (!data || !Array.isArray(data.domains)) return;

              var newDomainNames = data.domains.map(function(d) { return d.name; }).sort();

              // Check for new domains
              if (cachedDomains.length > 0) {
                var added = newDomainNames.filter(function(d) { return cachedDomains.indexOf(d) < 0; });
                if (added.length > 0) {
                  showNotification("🆕 New domains available: " + added.join(", "));
                  // Update domain list preserving selections
                  domainMetadata = {};
                  var domainNames = [];
                  data.domains.forEach(function(item) {
                    domainNames.push(item.name);
                    domainMetadata[item.name] = {
                      description: item.description,
                      count: item.chunk_count
                    };
                  });
                  renderDomainCheckboxes(domainNames);
                }
              }

              cachedDomains = newDomainNames;
            })
            .catch(function() { /* ignore polling errors */ });
        }

        function checkForTagUpdates() {
          fetch("/api/memory/tags/metadata")
            .then(function(resp) { return resp.ok ? resp.json() : null; })
            .then(function(data) {
              if (!data || !Array.isArray(data.tags)) return;

              var newTagNames = data.tags.map(function(t) { return t.tag; }).sort();

              // Check for new tags
              if (cachedTags.length > 0) {
                var added = newTagNames.filter(function(t) { return cachedTags.indexOf(t) < 0; });
                if (added.length > 0) {
                  showNotification("🆕 New tags available: " + added.join(", "));
                  // Update tag list preserving selections
                  tagMetadata = {};
                  var tagNames = [];
                  data.tags.forEach(function(item) {
                    tagNames.push(item.tag);
                    tagMetadata[item.tag] = {
                      description: item.description,
                      count: item.count
                    };
                  });
                  renderTagsCheckboxes(tagNames);
                }
              }

              cachedTags = newTagNames;
            })
            .catch(function() { /* ignore polling errors */ });
        }

        function showNotification(message) {
          // Show a toast-style notification
          var notification = document.createElement("div");
          notification.style.position = "fixed";
          notification.style.top = "20px";
          notification.style.right = "20px";
          notification.style.background = "rgba(15, 23, 42, 0.98)";
          notification.style.border = "1px solid rgba(56, 189, 248, 0.5)";
          notification.style.borderRadius = "8px";
          notification.style.padding = "12px 16px";
          notification.style.color = "var(--text-main)";
          notification.style.fontSize = "13px";
          notification.style.zIndex = "3000";
          notification.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.5)";
          notification.style.maxWidth = "400px";
          notification.textContent = message;
          document.body.appendChild(notification);

          // Auto-remove after 5 seconds
          setTimeout(function() {
            notification.style.transition = "opacity 0.3s";
            notification.style.opacity = "0";
            setTimeout(function() {
              document.body.removeChild(notification);
            }, 300);
          }, 5000);
        }


          // Start polling
          setInterval(checkForDomainUpdates, AUTO_UPDATE_INTERVAL);
          setInterval(checkForTagUpdates, AUTO_UPDATE_INTERVAL);
          checkForDomainUpdates();
          checkForTagUpdates();
        })();
