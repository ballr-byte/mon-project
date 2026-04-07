// ── NAV scroll effect ──
const nav = document.querySelector('.nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 20);
});

// ── Mobile burger ──
const burger = document.querySelector('.nav__burger');
const navLinks = document.querySelector('.nav__links');
burger.addEventListener('click', () => {
  navLinks.classList.toggle('open');
});
// Close menu when a link is clicked
navLinks.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => navLinks.classList.remove('open'));
});

// ── Pricing toggle ──
const toggle = document.getElementById('billingToggle');
const amounts = document.querySelectorAll('.price__amount');
const labelMonthly = document.getElementById('label-monthly');
const labelAnnual  = document.getElementById('label-annual');

const periods = document.querySelectorAll('.price__period');

toggle.addEventListener('click', () => {
  const isAnnual = toggle.getAttribute('aria-pressed') === 'true';
  toggle.setAttribute('aria-pressed', String(!isAnnual));

  if (!isAnnual) {
    amounts.forEach(el => { el.textContent = '$' + el.dataset.annual; });
    periods.forEach(el => { el.textContent = '/year'; });
    labelAnnual.classList.add('active');
    labelMonthly.classList.remove('active');
  } else {
    amounts.forEach(el => { el.textContent = '$' + el.dataset.monthly; });
    periods.forEach(el => { el.textContent = '/month'; });
    labelMonthly.classList.add('active');
    labelAnnual.classList.remove('active');
  }
});
labelMonthly.classList.add('active');

// ── Contact form ──
document.getElementById('contactForm').addEventListener('submit', e => {
  e.preventDefault();
  const btn = e.target.querySelector('button[type="submit"]');
  btn.textContent = '✓ Request Received — We\'ll be in touch!';
  btn.style.background = '#16a34a';
  btn.disabled = true;
});
