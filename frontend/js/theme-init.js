// Runs before the page paints so there is no flash of the wrong theme (FR-33).
(function () {
  var theme = null;
  try { theme = localStorage.getItem('studyflow.theme'); } catch (e) { /* storage blocked */ }
  if (theme !== 'light' && theme !== 'dark') {
    theme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  document.documentElement.setAttribute('data-theme', theme);
})();
