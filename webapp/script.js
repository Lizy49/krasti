// Безопасное получение Telegram WebApp
let tg = null;
if (typeof window.Telegram !== 'undefined' && window.Telegram.WebApp) {
    tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    console.log('Telegram WebApp инициализирован');
} else {
    console.log('Работа вне Telegram — функции корзины работают локально');
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    const icon = document.getElementById('theme-icon');
    if (icon) icon.textContent = theme === 'light' ? 'dark_mode' : 'light_mode';
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    applyTheme(current === 'light' ? 'dark' : 'light');
}

document.addEventListener('DOMContentLoaded', () => {
    applyTheme(localStorage.getItem('theme') || 'dark');
    updateCartBadge();
    console.log('DOM загружен, всё работает');
});

let currentCategory = '';
let cart = JSON.parse(localStorage.getItem('cart')) || [];
let currentProduct = null;

const productsData = {
    'odnorazki': [
        { id: 1, name: 'ELF BAR PLANET 25000', price: 1450, img: '/images/odno/elfbar.jpg', flavors: 'Освежающий цитрусовый сплэш, Голубая малина со льдом, Клюква, апельсин и Баха Сплэш, Двойное яблоко, Двойной персик с лаймом, Виноград, Жасмин и малина, Лимон и лайм, Персик плюс, Ананас, маракуйя и Баха' },
        { id: 2, name: 'PUFFMI FLORA 25000', price: 1900, img: '/images/odno/puff.jpg', flavors: 'Ананас Арбузная Конфета, Ананасовый Лимонад, Ванильное Мороженое, Виноград Клюква, Виноград Медовая Дыня, Вишня Лимон, Гранатовый Сок, Двойное Яблоко, Красный Грейпфрут, Чернично-Розовый Лимонад' },
        { id: 3, name: 'SNOOPYSMOKE 25000', price: 900, img: '/images/odno/ssmoke20.jpg', flavors: 'Ананас Лёд, Арбуз Лёд, Виноград Лёд, Вишнёвая Кола, Ледяная Мята, Лето Лёд, Мамаша с Багам, Мармелад, Мексиканское Манго Лёд, Персик Арбуз Лёд, Пина Колада, Розовый Лимонад, Тройные Ягоды Лёд, Тропический Радужный Взрыв, Черника Малина Лёд, Черника Малина'},
        { id: 7, name: 'SNOOPYSMOKE 50000', price: 1200, img: '/images/odno/ssmoke50.jpg', flavors: 'Арбуз Лёд, Ледяная Мята, Лето Лёд'},
        { id: 11, name: 'VOZOL VISTA 20000', price: 1400, img: '/images/odno/vozol.png', flavors: 'Собираем Миксом' }
    ],
    'zhidkosti': [
        { id: 8, name: 'Анархия V2 HARD', price: 500, img: '/images/shid/anarhia.png', flavors: 'Ананас Вишня, Арбуз Персик, Арбузно-Клубничный коктейль, Арбузный Фреш, Бабл-Гам Арбуз, Вишня Лайм, Голубая Малина Розовая Малина Арбуз, Жвачка Арбуз Дыня, Зеленое Яблоко, Киви Драгонфрут, Клубничный Мохито, Клюква Брусника, Клюква Смородина, Энергетик с лесными Ягодами, Яблочно-виноградный холс, Ягодный микс', strength: '70 мг' },
        { id: 12, name: 'Грех Самоубийца', price: 550, img: '/images/shid/grex.png', flavors: 'Ежевика Ледяная Груша, Зеленый Виноград Ледяной Лайм Черника Мята, Земляничный Энергетик Лед, Морозные Лесные Ягоды, Редбул Ледяная Черника Мята, Сок Земляники и Смородиновый Лед, Черная Смородина Вишня Лайм', strength: '80 мг' }
    ],
    'rasxodniki': [
        { id: 5, name: 'Испаритель GEEKVAPE', price: 300, img: 'images/isp/aegis.jpg', flavors: '0.2Ω 50-58w' },
        { id: 9, name: 'Испаритель SMOANT K-1 - K5', price: 300, img: '/images/isp/k1.jpg', flavors: '0.3Ω - 0.15Ω' },
        { id: 13, name: 'Картридж VAPORESSO XROS', price: 300, img: '/images/ips/xros.jpg', flavors: '0.8Ω 3ml Top Fill' }
    ],
    'plastinki': [
        { id: 6, name: 'Elf Bar', price: 350, img: '/images/loop/elf.jpg', flavors: 'Клубника', strength: '20 мг' },
        { id: 14, name: 'LOOP', price: 400, img: '/images/loop/loop.jpg', flavors: 'Кактус, Клубника, Криспи Айс', strength: '200 мг' }
    ],
    'snyus': [],
    'podsistemy': []
};

function openCategory(key) {
    console.log('Открываем категорию:', key);
    currentCategory = key;
    const home = document.getElementById('home-screen');
    const catalog = document.getElementById('catalog-screen');
    const empty = document.getElementById('empty-screen');

    if (home) home.classList.remove('active');
    if (catalog) catalog.classList.remove('active');
    if (empty) empty.classList.remove('active');

    const titles = {
        'odnorazki': 'Одноразки', 'zhidkosti': 'Жидкости', 'rasxodniki': 'Расходники',
        'plastinki': 'Пластинки', 'snyus': 'Снюс', 'podsistemy': 'Под-системы'
    };
    const items = productsData[key] || [];
    if (items.length === 0) {
        if (empty) {
            empty.classList.add('active');
            const t = document.getElementById('empty-title'); if (t) t.textContent = titles[key];
        }
        return;
    }
    if (catalog) {
        catalog.classList.add('active');
        const title = document.getElementById('catalog-title'); if (title) title.textContent = titles[key];
        renderProducts(items);
    }
}

function renderProducts(items) {
    const container = document.getElementById('products-container');
    if (!container) return;
    container.innerHTML = '';
    items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.addEventListener('click', (e) => {
            e.stopPropagation();
            openProductDetail(item);
        });

        const bgStyle = item.img ? `background-image: url('${item.img}');` : '';
        card.innerHTML = `
            <div class="product-img" style="${bgStyle}"></div>
            <div class="product-name">${item.name}</div>
            <div class="product-price">${item.price === 0 ? 'По запросу' : item.price + ' ₽'}</div>
        `;
        container.appendChild(card);
    });
}

function openProductDetail(product) {
    console.log('Открываем товар:', product.name);
    currentProduct = product;
    const catalogScreen = document.getElementById('catalog-screen');
    const detailScreen = document.getElementById('product-detail-screen');
    if (catalogScreen) catalogScreen.classList.remove('active');
    if (detailScreen) detailScreen.classList.add('active');

    const nameEl = document.getElementById('detail-name');
    const priceEl = document.getElementById('detail-price');
    const imgEl = document.getElementById('detail-img');
    const flavorLabel = document.getElementById('flavor-label');
    const strengthLabel = document.getElementById('strength-label');
    const flavorText = document.getElementById('detail-flavors');
    const strengthText = document.getElementById('detail-strength');

    if (nameEl) nameEl.textContent = product.name;
    if (priceEl) priceEl.textContent = product.price === 0 ? 'Цена по запросу' : product.price + ' ₽';
    if (imgEl) imgEl.style.backgroundImage = product.img ? `url('${product.img}')` : 'none';

    const isConsumable = currentCategory === 'rasxodniki';
    if (flavorLabel) flavorLabel.textContent = isConsumable ? 'Сопротивление / Мощность:' : 'Наличие вкусов:';
    if (strengthLabel) strengthLabel.textContent = isConsumable ? 'Кол-во в уп.' : 'Крепкость:';
    if (flavorText) flavorText.textContent = product.flavors || (isConsumable ? 'Нет данных' : 'Уточняйте');
    if (strengthText) strengthText.textContent = product.strength || (isConsumable ? 'N/A' : 'Не указано');
}

function closeProductDetail() {
    const detailScreen = document.getElementById('product-detail-screen');
    const catalogScreen = document.getElementById('catalog-screen');
    if (detailScreen) detailScreen.classList.remove('active');
    if (catalogScreen) catalogScreen.classList.add('active');
    currentProduct = null;
}

function addToCartFromDetail() {
    if (!currentProduct) return;
    const existing = cart.find(i => i.productId === currentProduct.id);
    if (existing) existing.qty++;
    else cart.push({ id: Date.now(), productId: currentProduct.id, name: currentProduct.name, price: currentProduct.price, qty: 1 });
    saveCart(); updateCartBadge(); closeProductDetail();
}

function goHome() {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const home = document.getElementById('home-screen');
    if (home) home.classList.add('active');
}

function openCart() {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const cartScreen = document.getElementById('cart-screen');
    if (cartScreen) cartScreen.classList.add('active');
    renderCart();
}

function renderCart() {
    const container = document.getElementById('cart-items-container');
    const totalEl = document.getElementById('total-price');
    const footer = document.getElementById('cart-footer');
    if (!container || !totalEl || !footer) return;
    container.innerHTML = '';

    if (cart.length === 0) {
        container.innerHTML = '<p class="empty-msg">Корзина пуста</p>';
        totalEl.textContent = '0 ₽';
        footer.style.display = 'none';
        return;
    }

    let total = 0;
    cart.forEach((item, index) => {
        total += item.price * item.qty;
        const row = document.createElement('div');
        row.className = 'cart-item';
        row.innerHTML = `
            <div class="cart-item-details">
                <div class="cart-item-name">${item.name}</div>
                <div class="cart-item-price">${(item.price * item.qty)} ₽</div>
            </div>
            <div class="qty-control">
                <button class="qty-btn" onclick="changeQty(${index},-1)">−</button>
                <span>${item.qty}</span>
                <button class="qty-btn" onclick="changeQty(${index},1)">+</button>
            </div>
            <button class="remove-btn material-icons" onclick="removeFromCart(${index})">delete</button>
        `;
        container.appendChild(row);
    });

    totalEl.textContent = total + ' ₽';
    footer.style.display = 'block';
}

function changeQty(index, delta) {
    cart[index].qty += delta;
    if (cart[index].qty <= 0) cart.splice(index, 1);
    saveCart(); renderCart(); updateCartBadge();
}

function removeFromCart(index) {
    cart.splice(index, 1);
    saveCart(); renderCart(); updateCartBadge();
}

function updateCartBadge() {
    const count = cart.reduce((sum, item) => sum + item.qty, 0);
    const badge = document.getElementById('cart-count');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
    }
}

function sendOrder() {
    if (cart.length === 0) return;
    const total = cart.reduce((sum, item) => sum + item.price * item.qty, 0);
    if (tg) {
        tg.sendData(JSON.stringify({ cart: cart, total: total }));
        tg.close();
    } else {
        alert(`Заказ отправлен (демо)\nСумма: ${total} ₽\nТовары: ${JSON.stringify(cart)}`);
        console.log('Order data:', { cart, total });
    }
}

function saveCart() {
    localStorage.setItem('cart', JSON.stringify(cart));
}

// Инициализация бейджа при загрузке
updateCartBadge();