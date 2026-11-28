// The list view (owner, 2026-11-28): the list fills the window, at #list-view, as the map
// does at #map-view (dist/components/map/map.js). The button is in the tree's toolbar
// (list_view_button() in tools/components/list_view.py); it opens the explorer's list
// (.explore-view, dist/components/explorer/explorer.js) or, on a record page without one,
// the tree's own box (.workspace). Back, Escape and the button close it.
(function () {
  'use strict';
  var HASH = '#list-view'; // address of the list view
  var OPEN_LABEL = 'List view';
  var CLOSE_LABEL = 'Close list view';
  var buttons = Array.prototype.slice.call(document.querySelectorAll('.list-view-btn'));
  if (!buttons.length) return;
  var shown = null, // the button whose list is open
    pushed = false; // whether opening added a history entry

  function box(btn) {
    return btn.closest('.explore-view') || btn.closest('.workspace');
  }

  function label(btn, open) {
    var t = open ? CLOSE_LABEL : OPEN_LABEL;
    btn.setAttribute('aria-label', t);
    btn.title = t;
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  function open(btn, push) {
    if (shown) return;
    shown = btn;
    box(btn).classList.add('list-full');
    document.documentElement.classList.add('list-full-open');
    label(btn, true);
    if (push && location.hash !== HASH) {
      try {
        history.pushState({ list: 1 }, '', location.pathname + location.search + HASH);
        pushed = true;
      } catch {
        /* no history entry: Back leaves the page */
      }
    }
    btn.focus();
  }

  function close(fromHistory) {
    if (!shown) return;
    var btn = shown;
    shown = null;
    box(btn).classList.remove('list-full');
    document.documentElement.classList.remove('list-full-open');
    label(btn, false);
    if (!fromHistory && location.hash === HASH) {
      // Leave the entry the list view added, or drop the mark from an address that came with it.
      if (pushed) history.back();
      else
        try {
          history.replaceState(history.state, '', location.pathname + location.search);
        } catch {
          /* keep the address as it is */
        }
    }
    pushed = false;
    btn.focus();
  }

  buttons.forEach(function (btn) {
    if (!box(btn)) return;
    btn.hidden = false;
    btn.addEventListener('click', function () {
      if (shown === btn) close(false);
      else open(btn, true);
    });
  });

  // Back and Forward move between the page and its list view.
  window.addEventListener('popstate', function () {
    if (location.hash === HASH) {
      if (!shown && !buttons[0].hidden) open(buttons[0], false);
    } else close(true);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && shown && !e.defaultPrevented) close(false);
  });
  // An address with #list-view opens the first list in the list view.
  if (location.hash === HASH && !buttons[0].hidden) open(buttons[0], false);
})();
