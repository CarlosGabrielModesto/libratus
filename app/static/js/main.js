/**
 * main.js — Scripts globais da aplicação Libratus.
 *
 * Responsabilidades:
 *   1. Auto-fechar alertas flash após 4s
 *   2. Indicador de carregamento nos formulários (evita double-submit)
 *   3. Tooltip Bootstrap nos elementos com data-bs-toggle="tooltip"
 *   4. Confirmação via dataset em links/botões destrutivos simples
 *   5. Highlight da linha da tabela ao passar o mouse (acessibilidade)
 *   6. Animar elementos com .animate-on-scroll ao entrar no viewport
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {

  // ── 1. Auto-fechar alertas flash ────────────────────────────────────────
  document.querySelectorAll('.alert.alert-dismissible').forEach(alertEl => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
      bsAlert.close();
    }, 4200);
  });


  // ── 2. Proteção contra double-submit ────────────────────────────────────
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function () {
      const submitBtn = this.querySelector('[type="submit"]');
      if (!submitBtn) return;

      // Guarda o HTML original para restaurar em caso de erro de validação
      const original = submitBtn.innerHTML;
      const originalDisabled = submitBtn.disabled;

      submitBtn.disabled = true;
      submitBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>'
        + 'Aguarde...';

      // Restaura após 8s (fallback de segurança — evita travar o botão para sempre)
      setTimeout(() => {
        submitBtn.disabled = originalDisabled;
        submitBtn.innerHTML = original;
      }, 8000);
    });
  });


  // ── 3. Ativar tooltips Bootstrap ────────────────────────────────────────
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    bootstrap.Tooltip.getOrCreateInstance(el, { trigger: 'hover' });
  });


  // ── 4. Animação de entrada nas stat-cards do dashboard ──────────────────
  const observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );

  document.querySelectorAll('.stat-card').forEach(card => observer.observe(card));


  // ── 5. Realce de linha ativa na tabela (acessibilidade por teclado) ──────
  document.querySelectorAll('.custom-table tbody tr').forEach(row => {
    row.setAttribute('tabindex', '0');
    row.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        const primaryAction = row.querySelector('a.btn, button.btn');
        if (primaryAction) primaryAction.click();
      }
    });
  });


  // ── 6. Contador animado nos stat-values ─────────────────────────────────
  function animateCounter(el, target, duration = 900) {
    const start     = performance.now();
    const startVal  = 0;

    function update(timestamp) {
      const elapsed  = timestamp - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased    = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(startVal + eased * (target - startVal));
      if (progress < 1) requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
  }

  document.querySelectorAll('.stat-value').forEach(el => {
    const target = parseInt(el.textContent.trim(), 10);
    if (!isNaN(target) && target > 0) {
      el.textContent = '0';
      // Dispara após um pequeno delay para ser visível após o fade-in
      setTimeout(() => animateCounter(el, target), 300);
    }
  });

});
