(function () {
  const saved = localStorage.getItem('theme');
  if (saved) document.documentElement.dataset.theme = saved;
  document.addEventListener('click', (event) => {
    const target = event.target;
    if (target.matches('[data-theme-toggle]')) {
      const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      localStorage.setItem('theme', next);
    }
    if (target.matches('[data-filter]')) {
      const category = target.dataset.filter;
      document.querySelectorAll('[data-filter]').forEach((btn) => btn.classList.toggle('active', btn === target));
      document.querySelectorAll('[data-article-category]').forEach((card) => {
        card.hidden = category !== 'all' && card.dataset.articleCategory !== category;
      });
    }
  });
  const search = document.querySelector('[data-search]');
  if (search) {
    search.addEventListener('input', () => {
      const q = search.value.toLowerCase().trim();
      document.querySelectorAll('[data-article-category]').forEach((card) => {
        const text = card.textContent.toLowerCase();
        card.hidden = q && !text.includes(q);
      });
    });
  }
})();
