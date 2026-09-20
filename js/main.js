/* ============================================================
   THE WEITZMAN ARCHIVE — main.js
   Shared interactions: nav dropdowns, accordion, copy buttons
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── NAV DROPDOWNS (click-toggle) ────────────────────────── */
  const navBtns = document.querySelectorAll('.nav-btn');

  navBtns.forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const item = btn.closest('.nav-item');
      const wasOpen = item.classList.contains('open');

      // Close all dropdowns
      document.querySelectorAll('.nav-item').forEach(i => {
        i.classList.remove('open');
        const b = i.querySelector('.nav-btn');
        if (b) b.setAttribute('aria-expanded', 'false');
      });

      // Toggle this one
      if (!wasOpen) {
        item.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });

  // Close dropdowns when clicking anywhere outside
  document.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(i => {
      i.classList.remove('open');
      const b = i.querySelector('.nav-btn');
      if (b) b.setAttribute('aria-expanded', 'false');
    });
  });

  // Prevent dropdown clicks from bubbling up and closing
  document.querySelectorAll('.nav-dropdown').forEach(d => {
    d.addEventListener('click', e => e.stopPropagation());
  });

  // Close on Escape key
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.nav-item').forEach(i => {
        i.classList.remove('open');
        const b = i.querySelector('.nav-btn');
        if (b) b.setAttribute('aria-expanded', 'false');
      });
    }
  });

  /* ── FILTER BUTTONS ──────────────────────────────────────── */
  document.querySelectorAll('.filter-bar').forEach(bar => {
    bar.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        bar.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        // TODO: wire up actual filtering once papers.json is populated
      });
    });
  });

  /* ── ACCORDION ───────────────────────────────────────────── */
  // Used on article pages for In Plain English / Short Summary / Marshall Notes
  document.querySelectorAll('.acc-trigger').forEach(btn => {
    btn.addEventListener('click', () => {
      const expanded = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!expanded));
      const body = btn.nextElementSibling;
      if (body) body.classList.toggle('open', !expanded);
    });
  });

  /* ── COPY BUTTONS ────────────────────────────────────────── */
  // Generic: data-copy-target="#element-id" or copies sibling .cite-box-text
  document.querySelectorAll('.copy-btn, .cite-copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.copyTarget;
      let text = '';

      if (targetId) {
        const el = document.querySelector(targetId);
        if (el) text = el.textContent.trim();
      } else {
        // Fall back to previous sibling with cite text
        const sibling = btn.previousElementSibling;
        if (sibling) text = sibling.textContent.trim();
      }

      if (!text) return;

      navigator.clipboard.writeText(text).then(() => {
        const original = btn.textContent;
        btn.textContent = 'Copied';
        setTimeout(() => { btn.textContent = original; }, 2000);
      }).catch(() => {
        // Fallback for older browsers
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        const original = btn.textContent;
        btn.textContent = 'Copied';
        setTimeout(() => { btn.textContent = original; }, 2000);
      });
    });
  });

  /* ── KATEX AUTO-RENDER ───────────────────────────────────── */
  // Only runs if KaTeX is loaded (article pages)
  if (typeof renderMathInElement !== 'undefined') {
    renderMathInElement(document.body, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '\\[', right: '\\]', display: true },
        { left: '$',  right: '$',  display: false },
        { left: '\\(', right: '\\)', display: false }
      ],
      throwOnError: false
    });
  }

  // Also handle explicit .katex-inline and .katex-block elements
  if (typeof katex !== 'undefined') {
    document.querySelectorAll('.katex-inline').forEach(el => {
      try {
        katex.render(el.textContent, el, { throwOnError: false, displayMode: false });
      } catch (e) { /* skip malformed */ }
    });
    document.querySelectorAll('.katex-block').forEach(el => {
      try {
        katex.render(
          el.textContent.replace(/\$\$/g, '').trim(),
          el,
          { throwOnError: false, displayMode: true }
        );
      } catch (e) { /* skip malformed */ }
    });
  }

});
