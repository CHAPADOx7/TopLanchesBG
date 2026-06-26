// Types:
// 1 = Snack
// 2 = Combos
// 3 = Portions
// 4 = Drinks

const products = [
    {
        id: 1,
        type: 1,
        name: 'X-Egg',
        description: 'Pão, hamburger, ovo, queijo prato, alface, tomate e molho especial.',
        price: 14.00,
        lastPrice: 0,
        img: 'burger.png'
    },
    {
        id: 2,
        type: 1,
        name: 'X-Salada',
        description: 'Pão, hamburger, presunto, picles, alface, tomate e molho especial.',
        price: 16.00,
        lastPrice: 0,
        img: 'burger.png'
    },
    {
        id: 3,
        type: 1,
        name: 'X-Bacon',
        description: 'Pão, hamburger, ovo, bacon, queijo prato, presunto, cebola caramelizada e molho especial.',
        price: 18.00,
        lastPrice: 0,
        img: 'burger.png'
    },
    {
        id: 4,
        type: 1,
        name: 'X-Tudo',
        description: 'Pão, hamburger, ovo, bacon, queijo prato, presunto, cebola caramelizada, picles, alface, tomate e molho especial.',
        price: 25.00,
        lastPrice: 0,
        img: 'xtudo.png'
    },
    {
        id: 4,
        type: 1,
        name: 'X-Promo',
        description: 'Pão, hamburger, ovo, bacon, queijo prato, presunto, cebola caramelizada, picles, alface, tomate e molho especial.',
        price: 19.99,
        lastPrice: 25.00,
        img: 'burger.png'
    },
    {
        id: 101,
        type: 2,
        name: 'Combo Simples',
        description: '2 x-saladas, 2 coca-cola lata e 2 batatas fritas pequenas.',
        price: 30.99,
        lastPrice: 0,
        img: 'combo.png'
    },
    {
        id: 102,
        type: 2,
        name: 'Combo Médio',
        description: '3 x-bacon, 3 coca-cola lata e 3 batatas fritas médias.',
        price: 45.99,
        lastPrice: 50.00,
        img: 'combo.png'
    },
    {
        id: 103,
        type: 2,
        name: 'Combo Grande',
        description: '4 x-tudo, 3 coca-cola lata e 3 batatas fritas grandes.',
        price: 68.99,
        lastPrice: 75.00,
        img: 'combo.png'
    },
    {
        id: 301,
        type: 4,
        name: 'Coca-Cola Lata',
        description: '1 coca-cola lata.',
        price: 6.00,
        lastPrice: 0,
        img: 'cocacola.png'
    },
    {
        id: 302,
        type: 4,
        name: 'Fanta Laranja Lata',
        description: '1 fanta laranja lata.',
        price: 5.00,
        lastPrice: 0,
        img: 'fanta.png'
    },
    {
        id: 303,
        type: 4,
        name: 'Pepsi Lata',
        description: '1 pepsi lata.',
        price: 4.50,
        lastPrice: 0,
        img: 'pepsi.png'
    },
]