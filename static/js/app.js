const productGrid = document.querySelector('#productGrid') || document.querySelector('#showMenu');
const promoGrid = document.querySelector('#promoGrid') || document.querySelector('#showPromotions');
const cartItemsContainer = document.querySelector('#cartItems');
const subtotalValue = document.querySelector('#subtotalValue');
const deliveryValue = document.querySelector('#deliveryValue');
const discountValue = document.querySelector('#discountValue');
const totalValue = document.querySelector('#totalValue');
const couponInput = document.querySelector('#couponInput');
const applyCoupon = document.querySelector('#applyCoupon');
const submitOrder = document.querySelector('#submitOrder');
const nameField = document.querySelector('#nameField');
const phoneField = document.querySelector('#phoneField');
const addressField = document.querySelector('#addressField');
const neighborhoodField = document.querySelector('#neighborhoodField');
const noteField = document.querySelector('#noteField');
const paymentField = document.querySelector('#paymentField');
const identityFields = document.querySelector('#identityFields');
const identityHint = document.querySelector('#identityHint');
const waitTimeDisplay = document.querySelector('#waitTimeDisplay');

let cart = JSON.parse(localStorage.getItem('toplanches_cart') || '[]');
let discount = 0;
let deliveryFee = 10;
let couponCode = '';
let clientProfile = null;
let themeLoaded = false;

const catalogProducts = [];
const catalogCombos = [];
const showAllBtn = document.querySelector('#showAll');
const showSnacksBtn = document.querySelector('#showSnacks');
const showCombosBtn = document.querySelector('#showCombos');
const showPortionsBtn = document.querySelector('#showPortions');
const showDrinksBtn = document.querySelector('#showDrinks');
let activeCategory = 'all';
const setCartStorage = () => localStorage.setItem('toplanches_cart', JSON.stringify(cart));

const normalizeCategory = value => (value || '')
  .toString()
  .toLowerCase()
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '');

const formatMoney = value => Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

const updateCartSummary = () => {
  const subtotal = cart.reduce((sum, item) => sum + item.preco * item.quantidade, 0);
  const discountAmount = subtotal * (discount / 100);
  const total = subtotal + deliveryFee - discountAmount;
  subtotalValue && (subtotalValue.textContent = formatMoney(subtotal));
  deliveryValue && (deliveryValue.textContent = formatMoney(deliveryFee));
  discountValue && (discountValue.textContent = formatMoney(discountAmount));
  totalValue && (totalValue.textContent = formatMoney(total));
};

const renderCart = () => {
  if (!cartItemsContainer) return;
  cartItemsContainer.innerHTML = cart.length === 0 ? '<p>Seu carrinho está vazio.</p>' : '';
  cart.forEach(item => {
    const card = document.createElement('div');
    card.className = 'cart-item';
    card.innerHTML = `
      <div class="item-meta">
        <div>
          <h4>${item.nome}</h4>
          <p>${item.descricao || ''}</p>
        </div>
        <span>${formatMoney(item.preco * item.quantidade)}</span>
      </div>
      <div class="item-meta">
        <span>Quantidade: ${item.quantidade}</span>
        <div>
          <button class="secondary-btn" onclick="changeQty(${item.id}, -1)">-</button>
          <button class="secondary-btn" onclick="changeQty(${item.id}, 1)">+</button>
        </div>
      </div>
    `;
    cartItemsContainer.appendChild(card);
  });
  updateCartSummary();
};

const changeQty = (id, delta) => {
  cart = cart.map(item => item.id === id ? { ...item, quantidade: Math.max(1, item.quantidade + delta) } : item);
  setCartStorage();
  renderCart();
};

window.changeQty = changeQty;

const addProductToCart = product => {
  const existing = cart.find(item => item.id === product.id && item.combo_id === product.combo_id);
  if (existing) {
    existing.quantidade += 1;
  } else {
    cart.push({ ...product, quantidade: 1 });
  }
  setCartStorage();
  renderCart();
  Toastify({ text: 'Produto adicionado ao carrinho', duration: 2500, close: true, gravity: 'bottom', position: 'right', style: { background: '#D2740C', color: '#FFF5E8' } }).showToast();
};

const isCategory = (item, category) => {
  const value = normalizeCategory(item.categoria);
  if (category === 'lanches') return value === 'lanches';
  if (category === 'bebidas') return value === 'bebidas';
  if (category === 'porcoes') return value === 'porcoes' || value === 'porcao';
  if (category === 'combos') return value === 'combos' || value === 'combo';
  if (category === 'promocao') return value === 'promocao' || value === 'promocoes';
  return true;
};

const updateCategoryButtons = () => {
  if (!showAllBtn) return;
  [showAllBtn, showSnacksBtn, showCombosBtn, showPortionsBtn, showDrinksBtn].forEach(btn => btn && btn.classList.remove('active'));
  if (activeCategory === 'all') showAllBtn && showAllBtn.classList.add('active');
  if (activeCategory === 'lanches') showSnacksBtn && showSnacksBtn.classList.add('active');
  if (activeCategory === 'combos') showCombosBtn && showCombosBtn.classList.add('active');
  if (activeCategory === 'porcoes') showPortionsBtn && showPortionsBtn.classList.add('active');
  if (activeCategory === 'bebidas') showDrinksBtn && showDrinksBtn.classList.add('active');
};

const renderProductCards = () => {
  if (!productGrid || !promoGrid) return;
  const filteredProducts = catalogProducts.filter(prod => activeCategory === 'all' ? true : isCategory(prod, activeCategory));
  const showComboCards = activeCategory === 'all' || activeCategory === 'combos';
  const menuCombos = showComboCards ? catalogCombos : [];
  const menuCards = [
    ...filteredProducts.map(prod => ({ ...prod, __type: 'product' })),
    ...menuCombos.map(combo => ({ ...combo, __type: 'combo' }))
  ];

  productGrid.innerHTML = menuCards.length === 0 ? '<p>Nenhum produto encontrado nesta categoria.</p>' : menuCards.map(item => `
    <div class="card">
      <div>
        <div class="cardImg">${item.imagem ? `<img src="/static/img/${item.imagem}" alt="${item.nome}" />` : ''}</div>
        <h4>${item.nome}</h4>
        <p>${item.descricao || ''}</p>
      </div>
      <div>
        <p class="price">R$ <span>${parseFloat(item.preco).toFixed(2).replace('.', ',')}</span></p>
        <button class="btn" onclick="addProductToCartById(${item.id}, '${item.__type}')">
          <span class="iconify-inline" data-icon="mdi:cart-plus"></span> Adicionar
        </button>
      </div>
    </div>
  `).join('');

  const promotionProducts = catalogProducts.filter(prod => isCategory(prod, 'promocao'));
  promoGrid.innerHTML = promotionProducts.length === 0 ? '<p>Nenhuma promoção ativa no momento.</p>' : promotionProducts.map(prod => `
    <div class="promo-card">
      ${prod.imagem ? `<img src="/static/img/${prod.imagem}" alt="${prod.nome}" />` : ''}
      <div class="card-body">
        <h3>${prod.nome}</h3>
        <p>${prod.descricao || ''}</p>
        <div class="card-footer">
          <strong>R$ ${parseFloat(prod.preco).toFixed(2).replace('.', ',')}</strong>
          <button class="primary-btn" onclick="addProductToCartById(${prod.id}, 'product')">Adicionar</button>
        </div>
      </div>
    </div>
  `).join('');

  updateCategoryButtons();
};

const addProductToCartById = (id, type) => {
  const source = type === 'combo' ? catalogCombos : catalogProducts;
  const product = source.find(item => item.id === id);
  if (!product) return;
  addProductToCart({
    id: product.id,
    nome: product.nome,
    descricao: product.descricao,
    preco: parseFloat(product.preco),
    imagem: product.imagem,
    combo_id: type === 'combo' ? product.id : null
  });
};

const fetchCatalog = async () => {
  try {
    const response = await fetch('/api/products');
    const data = await response.json();
    catalogProducts.length = 0;
    catalogCombos.length = 0;
    data.produtos.forEach(prod => catalogProducts.push(prod));
    data.combos.forEach(combo => catalogCombos.push(combo));
    renderProductCards();
  } catch (err) {
    console.error(err);
  }
};

const loadPaymentOptions = async () => {
  if (!paymentField) return;
  try {
    const response = await fetch('/api/payments');
    if (!response.ok) return;
    const data = await response.json();
    paymentField.innerHTML = '';
    data.formas.forEach(forma => {
      const option = document.createElement('option');
      option.value = forma.nome;
      option.textContent = forma.nome;
      paymentField.appendChild(option);
    });
  } catch (err) {
    console.error(err);
  }
};

const loadClientProfile = async () => {
  if (!nameField || !phoneField) return;
  try {
    const response = await fetch('/api/client/profile');
    if (!response.ok) return;
    const data = await response.json();
    if (!data.logged_client) return;
    clientProfile = data;
    nameField.value = data.nome || '';
    phoneField.value = data.telefone || '';
    if (identityFields) identityFields.style.display = 'none';
    if (identityHint) identityHint.style.display = 'block';
  } catch (err) {
    console.error(err);
  }
};

const updateWaitTime = async () => {
  if (!waitTimeDisplay) return;
  try {
    const response = await fetch('/api/wait-time');
    if (!response.ok) return;
    const data = await response.json();
    waitTimeDisplay.textContent = `${data.tempo_estimado_minutos} minutos`;
  } catch (err) {
    console.error(err);
  }
};

const applySiteTheme = async () => {
  if (themeLoaded || !document.body) return;
  themeLoaded = true;
  try {
    const response = await fetch('/api/theme');
    if (!response.ok) return;
    const data = await response.json();
    document.body.classList.remove('theme-normal', 'theme-dark', 'dark');
    if (data.theme === 'dark') {
      document.body.classList.add('theme-dark', 'dark');
    } else {
      document.body.classList.add('theme-normal');
    }
  } catch (err) {
    console.error(err);
  }
};

applyCoupon && applyCoupon.addEventListener('click', async () => {
  const code = couponInput.value.trim();
  if (!code) return;
  try {
    const resp = await fetch(`/api/coupons/${encodeURIComponent(code)}`);
    if (!resp.ok) throw new Error('Cupom inválido');
    const data = await resp.json();
    couponCode = code.toUpperCase();
    discount = data.cupom.tipo === 'percentual' ? data.cupom.valor : 0;
    Toastify({ text: 'Cupom aplicado com sucesso!', duration: 2500, close: true, gravity: 'bottom', position: 'right', style: { background: '#D2740C', color: '#FFF5E8' } }).showToast();
    renderCart();
  } catch (err) {
    Toastify({ text: 'Cupom inválido ou expirado', duration: 2500, close: true, gravity: 'bottom', position: 'right', style: { background: '#D2740C', color: '#FFF5E8' } }).showToast();
  }
});

submitOrder && submitOrder.addEventListener('click', async () => {
  if (cart.length === 0) {
    Toastify({ text: 'Adicione itens ao carrinho antes de finalizar.', duration: 2500, close: true, gravity: 'bottom', position: 'right', style: { background: '#D2740C', color: '#FFF5E8' } }).showToast();
    return;
  }
  const payload = {
    nome: clientProfile?.nome || nameField.value.trim(),
    telefone: clientProfile?.telefone || phoneField.value.trim(),
    endereco: addressField.value.trim(),
    bairro: neighborhoodField.value.trim(),
    observacao: noteField.value.trim(),
    forma_pagamento: paymentField.value,
    cupom: couponCode,
    items: cart.map(item => ({
      id: item.id,
      produto_id: item.combo_id ? null : item.id,
      combo_id: item.combo_id || null,
      nome: item.nome,
      preco: item.preco,
      quantidade: item.quantidade
    }))
  };
  const response = await fetch('/api/checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  if (response.ok && data.success) {
    localStorage.removeItem('toplanches_cart');
    cart = [];
    renderCart();
    Toastify({ text: 'Pedido enviado. Acompanhe no painel de pedidos.', duration: 2500, close: true, gravity: 'bottom', position: 'right', style: { background: '#D2740C', color: '#FFF5E8' } }).showToast();
  } else {
    Toastify({ text: data.error || 'Erro ao enviar pedido.', duration: 2500, close: true, gravity: 'bottom', position: 'right', style: { background: '#D2740C', color: '#FFF5E8' } }).showToast();
  }
});

showAllBtn && showAllBtn.addEventListener('click', event => {
  event.preventDefault();
  activeCategory = 'all';
  renderProductCards();
});

showSnacksBtn && showSnacksBtn.addEventListener('click', event => {
  event.preventDefault();
  activeCategory = 'lanches';
  renderProductCards();
});

showCombosBtn && showCombosBtn.addEventListener('click', event => {
  event.preventDefault();
  activeCategory = 'combos';
  renderProductCards();
});

showPortionsBtn && showPortionsBtn.addEventListener('click', event => {
  event.preventDefault();
  activeCategory = 'porcoes';
  renderProductCards();
});

showDrinksBtn && showDrinksBtn.addEventListener('click', event => {
  event.preventDefault();
  activeCategory = 'bebidas';
  renderProductCards();
});

fetchCatalog();
loadPaymentOptions();
loadClientProfile();
updateWaitTime();
applySiteTheme();
setInterval(updateWaitTime, 30000);
renderCart();
