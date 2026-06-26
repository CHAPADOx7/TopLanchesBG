const socket = io();
socket.on('connected', data => console.log(data.message));
socket.on('new_order', data => {
  console.log('Novo pedido recebido', data);
  if (document.title.includes('Dashboard') || document.body.classList.contains('dashboard-shell')) {
    Toastify({ text: '🔔 Novo pedido recebido', duration: 3000, close: true, gravity: 'top', position: 'right', style: { background: '#D2740C', color: '#FFF5E8' } }).showToast();
  }
});
socket.on('status_update', data => {
  console.log('Status atualizado', data);
  Toastify({ text: `Status do pedido ${data.order_id} atualizado para ${data.status}.`, duration: 3000, close: true, gravity: 'top', position: 'right', style: { background: '#D2740C', color: '#FFF5E8' } }).showToast();
});
