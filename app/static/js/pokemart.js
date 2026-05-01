(function () {
  function formatCountdown(seconds) {
    const safe = Math.max(0, seconds);
    const hours = String(Math.floor(safe / 3600)).padStart(2, '0');
    const minutes = String(Math.floor((safe % 3600) / 60)).padStart(2, '0');
    const secs = String(safe % 60).padStart(2, '0');
    return `Ends in ${hours}:${minutes}:${secs}`;
  }

  function initCountdowns() {
    document.querySelectorAll('[data-countdown-seconds]').forEach((card) => {
      let remaining = Number(card.getAttribute('data-countdown-seconds')) || 0;
      const label = card.querySelector('[data-countdown-label]');
      if (!label) {
        return;
      }

      label.textContent = formatCountdown(remaining);
      window.setInterval(() => {
        remaining = Math.max(0, remaining - 1);
        label.textContent = formatCountdown(remaining);
      }, 1000);
    });
  }

  function initHeroSlider() {
    const slider = document.querySelector('[data-hero-slider]');
    if (!slider) {
      return;
    }

    const slides = Array.from(slider.querySelectorAll('.hero-slide'));
    const dots = Array.from(slider.querySelectorAll('[data-hero-dot]'));
    const prev = slider.querySelector('[data-hero-prev]');
    const next = slider.querySelector('[data-hero-next]');
    let index = 0;
    let timer = null;

    function render(nextIndex) {
      index = (nextIndex + slides.length) % slides.length;
      slides.forEach((slide, slideIndex) => {
        slide.classList.toggle('is-active', slideIndex === index);
      });
      dots.forEach((dot, dotIndex) => {
        dot.classList.toggle('is-active', dotIndex === index);
      });
    }

    function restartTimer() {
      if (timer) {
        window.clearInterval(timer);
      }
      timer = window.setInterval(() => render(index + 1), 4500);
    }

    prev && prev.addEventListener('click', () => {
      render(index - 1);
      restartTimer();
    });

    next && next.addEventListener('click', () => {
      render(index + 1);
      restartTimer();
    });

    dots.forEach((dot, dotIndex) => {
      dot.addEventListener('click', () => {
        render(dotIndex);
        restartTimer();
      });
    });

    slider.addEventListener('mouseenter', () => {
      if (timer) {
        window.clearInterval(timer);
      }
    });

    slider.addEventListener('mouseleave', restartTimer);

    render(0);
    restartTimer();
  }

  function initShelfScrollers() {
    document.querySelectorAll('.shelf-scroller-wrap').forEach((wrap) => {
      const scroller = wrap.querySelector('[data-shelf-scroller]');
      const prev = wrap.querySelector('[data-shelf-prev]');
      const next = wrap.querySelector('[data-shelf-next]');
      if (!scroller) {
        return;
      }

      const amount = () => Math.max(240, Math.round(scroller.clientWidth * 0.82));
      prev && prev.addEventListener('click', () => scroller.scrollBy({ left: -amount(), behavior: 'smooth' }));
      next && next.addEventListener('click', () => scroller.scrollBy({ left: amount(), behavior: 'smooth' }));
    });
  }

  function initWishlist() {
    document.querySelectorAll('.wish-toggle').forEach((button) => {
      button.addEventListener('mouseenter', () => {
        button.classList.add('is-hovering');
      });
      button.addEventListener('mouseleave', () => {
        button.classList.remove('is-hovering');
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initHeroSlider();
    initShelfScrollers();
    initWishlist();
    initCountdowns();
  });
})();
