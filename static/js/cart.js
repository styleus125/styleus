/**
 * DLO Store – Cart AJAX operations
 */

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

function updateCartBadge(count) {
  const badge = document.getElementById('cart-badge');
  if (!badge) return;
  badge.textContent = count;
  if (count > 0) {
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
}

function showToast(message, type = 'success') {
  // Remove existing toast
  const existing = document.getElementById('cart-toast');
  if (existing) existing.remove();

  const colors = {
    success: 'bg-green-600',
    error: 'bg-red-600',
    warning: 'bg-yellow-600',
    info: 'bg-blue-600',
  };

  const toast = document.createElement('div');
  toast.id = 'cart-toast';
  toast.className = `fixed bottom-6 right-6 z-50 ${colors[type] || colors.success} text-white px-5 py-3 rounded-xl shadow-lg text-sm font-medium transform translate-y-2 opacity-0 transition-all duration-300`;
  toast.textContent = message;
  document.body.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => {
    toast.style.transform = 'translateY(0)';
    toast.style.opacity = '1';
  });

  // Auto remove
  setTimeout(() => {
    toast.style.transform = 'translateY(10px)';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 2800);
}

function toggleLike(productId, btnEl) {
  fetch('/products/' + productId + '/like', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
  })
  .then(res => {
    if (res.status === 401) {
      window.location.href = '/auth/login';
      return null;
    }
    return res.json();
  })
  .then(data => {
    if (!data) return;
    const svg = btnEl.querySelector('svg');
    if (data.liked) {
      btnEl.classList.remove('border-gray-200', 'border-gray-300', 'text-gray-400', 'hover:border-red-300', 'hover:text-red-500');
      btnEl.classList.add('border-red-300', 'bg-red-50', 'text-red-500');
      if (svg) svg.setAttribute('fill', 'currentColor');
      btnEl.title = 'Unlike';
    } else {
      btnEl.classList.remove('border-red-300', 'bg-red-50', 'text-red-500');
      btnEl.classList.add('border-gray-200', 'text-gray-400', 'hover:border-red-300', 'hover:text-red-500');
      if (svg) svg.setAttribute('fill', 'none');
      btnEl.title = 'Like';
    }
  })
  .catch(() => showToast('Could not update like. Please try again.', 'error'));
}

function addToCart(productId, quantity, btnEl) {
  const btn = btnEl;
  const originalText = btn ? btn.textContent : '';
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Adding…';
  }

  fetch('/cart/add', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify({ product_id: productId, quantity: quantity }),
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      updateCartBadge(data.cart_count);
      showToast(data.message || 'Added to cart', 'success');
    } else {
      showToast(data.message || 'Could not add to cart', 'error');
    }
  })
  .catch(() => {
    showToast('Network error. Please try again.', 'error');
  })
  .finally(() => {
    if (btn) {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  });
}
