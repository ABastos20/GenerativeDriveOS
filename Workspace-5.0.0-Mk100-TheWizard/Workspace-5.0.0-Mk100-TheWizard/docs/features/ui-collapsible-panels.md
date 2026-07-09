# UI Collapsible Panels Feature

## Overview
Added minimize/expand functionality to Research History, Smart Suggestions, and Research Health panels in the JARVIS BMAD Console to reduce UI clutter.

## Changes

### User Interface (`src/jarvis/api/app.py`)

**Added Features**:
- **Chevron Indicators**: Visual indicators (▼/▶) show panel expand/collapse state
- **Click Headers to Toggle**: Click panel headers to expand or collapse content
- **Persistent State**: Panel state saved to localStorage per panel
- **Smooth Transitions**: CSS animations for smooth panel transitions
- **Button Click Prevention**: Clicking buttons within headers doesn't toggle panels
- **Mobile Responsive**: Auto-collapses panels on screens ≤640px

**Modified Panels**:
1. **Research History** - Collapsible research session history
2. **Smart Suggestions** - Collapsible AI suggestions
3. **Research Health** - Collapsible rate limit and cost monitoring

## User Experience

### How to Use
1. Click any panel header to minimize/expand
2. State persists across page refreshes
3. Buttons in headers (Refresh, Clear, etc.) still work independently

### Visual Feedback
- **Expanded**: Chevron points down (▼)
- **Collapsed**: Chevron points right (▶)
- Hover highlights chevron in accent color

## Technical Details

### CSS Changes
```css
.chevron {
  display: inline-block;
  transition: transform 0.25s ease;
  transform: rotate(-90deg); /* when collapsed */
}
```

### JavaScript Changes
```javascript
// Load state from localStorage
var isCollapsed = localStorage.getItem('jarvis_panel_' + panelId + '_collapsed');

// Toggle on click
header.addEventListener('click', function() {
  bodyEl.classList.toggle('open');
  localStorage.setItem('jarvis_panel_' + panelId + '_collapsed', !isOpen);
});
```

## Benefits
- **Reduced Clutter**: Users can hide panels they don't need
- **Persistent Preferences**: Remembers user's layout preferences
- **Better Mobile Experience**: Auto-collapses on small screens
- **Accessibility**: Maintains aria-expanded attributes for screen readers

## Testing
- ✅ Click headers to toggle panels
- ✅ State persists after page refresh
- ✅ Buttons (Refresh, Clear, etc.) still functional
- ✅ Mobile responsive behavior
- ✅ Keyboard accessible

## Future Enhancements (from user feedback)
- Pagination for conversation history
- "Load More" button for conversations
- Search/filter for conversation history
