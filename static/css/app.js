(() => {
  const menuToggle = document.querySelector('[data-menu-toggle]');
  const sidebar = document.querySelector('[data-sidebar]');
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => {
      const isOpen = sidebar.classList.toggle('sidebar-open');
      menuToggle.setAttribute('aria-expanded', String(isOpen));
      menuToggle.textContent = isOpen ? '×' : '☰';
    });
    document.addEventListener('click', (event) => {
      if (window.innerWidth <= 900 && sidebar.classList.contains('sidebar-open') &&
          !sidebar.contains(event.target) && !menuToggle.contains(event.target)) {
        sidebar.classList.remove('sidebar-open');
        menuToggle.setAttribute('aria-expanded', 'false');
        menuToggle.textContent = '☰';
      }
    });
  }

  document.querySelectorAll('[data-dismiss]').forEach((button) => {
    button.addEventListener('click', () => button.closest('.flash')?.remove());
  });

  document.querySelectorAll('[data-count]').forEach((textarea) => {
    const output = textarea.closest('.field')?.querySelector('[data-count-value]');
    const update = () => { if (output) output.textContent = String(textarea.value.length); };
    textarea.addEventListener('input', update);
    update();
  });

  document.querySelectorAll('[data-confirm-delete]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      const message = form.getAttribute('data-confirm-message') || 'Are you sure?';
      if (!window.confirm(message)) event.preventDefault();
    });
  });

  document.querySelectorAll('[data-idea-form]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!form.reportValidity()) {
        event.preventDefault();
        return;
      }
      const submit = form.querySelector('[data-submit-button]');
      if (submit) {
        submit.disabled = true;
        submit.classList.add('is-loading');
        submit.innerHTML = '<span class="button-spinner" aria-hidden="true"></span> Evaluating your idea…';
      }
    });
  });
})();
