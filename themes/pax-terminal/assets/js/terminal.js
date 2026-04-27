// pax-terminal client bundle
// modules: copy, search-redirect, palette-switcher
//
// Note: a localStorage-backed install bag / cart system was removed in Wave 6.
// We have no install endpoint yet, so the bag was prototype-only. If a real
// "saved paxes" feature is wanted later, it can be reintroduced as a separate
// module — keep cost / install-command framing out of it.
(function () {
  'use strict';

  // ==========================================================================
  // ----- module: copy buttons -----
  // ==========================================================================
  // Finds every .t-copy-btn[data-copy-target] button inside .t-code-block.
  // Reads target via the `data-copy-target` id, copies to clipboard,
  // briefly swaps button text to [ copied ] for 1.5s.
  // ==========================================================================

  function initCopyButtons() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.t-copy-btn[data-copy-target]');
      if (!btn) return;

      var targetId = btn.getAttribute('data-copy-target');
      var target   = targetId ? document.getElementById(targetId) : null;
      if (!target) return;

      var text = target.textContent || '';

      navigator.clipboard.writeText(text).then(function () {
        flashButton(btn, '[ copied ]');
      }).catch(function () {
        flashButton(btn, '[ copy failed ]');
      });
    });
  }

  function flashButton(btn, msg) {
    var orig = btn.textContent;
    btn.textContent = msg;
    setTimeout(function () {
      btn.textContent = orig;
    }, 1500);
  }

  // ==========================================================================
  // ----- module: search redirect -----
  // ==========================================================================
  // Header search input (.t-search-input). Enter is handled by an inline
  // onkeydown handler in header.html that redirects to /pax/?q=<value>.
  // Browse page reads the ?q= parameter and prefills its filter input.
  // Cmd+K / Ctrl+K focuses the search input from anywhere.
  // ==========================================================================

  function initSearchRedirect() {
    var input = document.querySelector('.t-search-input');
    if (!input) return;

    document.addEventListener('keydown', function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        input.focus();
        input.select();
      }
    });
  }

  // ==========================================================================
  // ----- module: palette switcher -----
  // ==========================================================================
  // Public API: window.paxSetTheme(name)
  // Valid names: cobalt | lime | amber | coral
  // Persisted in localStorage under 'pax_theme'.
  // On init, restores saved theme (default cobalt).
  // ==========================================================================

  var VALID_THEMES = ['cobalt', 'lime', 'amber', 'coral'];
  var THEME_KEY    = 'pax_theme';

  window.paxSetTheme = function (name) {
    if (!VALID_THEMES.includes(name)) return;
    document.documentElement.setAttribute('data-pt-theme', name);
    try { localStorage.setItem(THEME_KEY, name); } catch (e) {}
  };

  function initPaletteSwitcher() {
    var saved = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch (e) {}
    if (saved && VALID_THEMES.includes(saved)) {
      document.documentElement.setAttribute('data-pt-theme', saved);
    } else {
      document.documentElement.setAttribute('data-pt-theme', 'cobalt');
    }
  }

  // ==========================================================================
  // ----- init on DOMContentLoaded -----
  // ==========================================================================

  function init() {
    initPaletteSwitcher(); // first — applies theme before paint
    initCopyButtons();
    initSearchRedirect();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
