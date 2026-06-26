(async function syncNavbarSession() {
  try {
    const response = await fetch('/api/session');
    if (!response.ok) return;
    const sessionData = await response.json();
    if (!sessionData.logged_in) return;

    const desktopItems = document.querySelector('.navbar .content .items');
    const mobileItems = document.querySelector('.navbar .itemsMobile');
    const desktopIcons = document.querySelector('.navbar .content .icons');
    const mobileIcons = document.querySelector('.navbar .itemsMobile .icons');

    const myOrdersLink = '<a href="/client/orders">Meus Pedidos</a>';
    const deliveryLink = '<a href="/delivery/panel">Entregas</a>';
    const adminLink = '<a href="/admin/dashboard">Painel Admin</a>';

    if (desktopItems) {
      if (sessionData.role === 'client') desktopItems.insertAdjacentHTML('beforeend', myOrdersLink);
      if (sessionData.role === 'delivery') desktopItems.insertAdjacentHTML('beforeend', deliveryLink);
      if (sessionData.role === 'admin') desktopItems.insertAdjacentHTML('beforeend', adminLink);
      desktopItems.insertAdjacentHTML('beforeend', '<a href="/logout">Sair</a>');
    }

    if (mobileItems) {
      if (sessionData.role === 'client') mobileItems.insertAdjacentHTML('afterbegin', myOrdersLink);
      if (sessionData.role === 'delivery') mobileItems.insertAdjacentHTML('afterbegin', deliveryLink);
      if (sessionData.role === 'admin') mobileItems.insertAdjacentHTML('afterbegin', adminLink);
      mobileItems.insertAdjacentHTML('beforeend', '<a href="/logout">Sair</a>');
    }

    [desktopIcons, mobileIcons].forEach(iconBox => {
      if (!iconBox) return;
      const loginLink = iconBox.querySelector('a.login-link');
      if (loginLink) loginLink.remove();
    });
  } catch (error) {
    console.error(error);
  }
})();
