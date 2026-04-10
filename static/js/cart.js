// Shopping Cart Logic for Gordin Lanches

let cart = JSON.parse(localStorage.getItem('gordin_cart')) || [];

function updateCartCount() {
    const countElement = document.getElementById('cart-count');
    if (countElement) {
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
        countElement.innerText = totalItems;
    }
}

function saveCart() {
    localStorage.setItem('gordin_cart', JSON.stringify(cart));
    updateCartCount();
}

function addToCart(productId, name, price, image, obs="") {
    let finalName = name;
    let cartId = productId;

    if (obs && obs.trim() !== "") {
        finalName = name + ` (Obs: ${obs.trim()})`;
        // Create a unique temporary numeric-looking string or just replace spaces.
        // Actually, we can just use a string ID.
        cartId = productId + "_" + btoa(encodeURIComponent(obs.trim())).replace(/[=+-]/g, '');
    }

    const existingItem = cart.find(item => item.id == cartId);
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: cartId,
            name: finalName,
            price: price,
            image: image,
            quantity: 1
        });
    }
    saveCart();
    
    // Simple toast notification
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: var(--success);
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    toast.innerText = `${name} adicionado ao carrinho!`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.id != productId);
    saveCart();
    renderCart();
}

function updateQuantity(productId, delta) {
    const item = cart.find(item => item.id == productId);
    if (item) {
        item.quantity += delta;
        if (item.quantity <= 0) {
            removeFromCart(productId);
        } else {
            saveCart();
            renderCart();
        }
    }
}

function renderCart() {
    const cartItemsContainer = document.getElementById('cart-items');
    const cartSummaryContainer = document.getElementById('cart-summary');
    
    if (!cartItemsContainer) return;

    if (cart.length === 0) {
        cartItemsContainer.innerHTML = '<p style="text-align: center; margin: 4rem 0;">Seu carrinho está vazio.</p>';
        if (cartSummaryContainer) cartSummaryContainer.style.display = 'none';
        return;
    }

    if (cartSummaryContainer) cartSummaryContainer.style.display = 'block';

    cartItemsContainer.innerHTML = cart.map(item => `
        <div class="cart-item" style="display: flex; align-items: center; justify-content: space-between; background: white; padding: 1rem; border-radius: 15px; margin-bottom: 1rem; box-shadow: var(--shadow);">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <img src="${item.image}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 10px;">
                <div>
                    <h4 style="margin: 0;">${item.name}</h4>
                    <p style="margin: 0; color: var(--primary); font-weight: bold;">R$ ${item.price.toFixed(2)}</p>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="display: flex; align-items: center; background: #eee; border-radius: 20px; padding: 0.2rem 0.8rem;">
                    <button onclick="updateQuantity('${item.id}', -1)" style="border: none; background: none; cursor: pointer; padding: 0.5rem;"><i class="fas fa-minus"></i></button>
                    <span style="font-weight: bold; width: 30px; text-align: center;">${item.quantity}</span>
                    <button onclick="updateQuantity('${item.id}', 1)" style="border: none; background: none; cursor: pointer; padding: 0.5rem;"><i class="fas fa-plus"></i></button>
                </div>
                <button onclick="removeFromCart('${item.id}')" style="border: none; background: none; color: #ff5252; cursor: pointer; font-size: 1.2rem;"><i class="fas fa-trash"></i></button>
            </div>
        </div>
    `).join('');

    // Calculate Totals
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const neighborhoodSelect = document.getElementById('neighborhood');
    const deliveryFee = neighborhoodSelect ? parseFloat(neighborhoodSelect.options[neighborhoodSelect.selectedIndex]?.dataset.fee || 0) : 0;
    const total = subtotal + deliveryFee;

    document.getElementById('subtotal').innerText = `R$ ${subtotal.toFixed(2)}`;
    document.getElementById('delivery-fee').innerText = `R$ ${deliveryFee.toFixed(2)}`;
    document.getElementById('total').innerText = `R$ ${total.toFixed(2)}`;
}

document.addEventListener('DOMContentLoaded', () => {
    updateCartCount();
    renderCart();

    const neighborhoodSelect = document.getElementById('neighborhood');
    if (neighborhoodSelect) {
        neighborhoodSelect.addEventListener('change', renderCart);
    }
});

function checkout() {
    const address = document.getElementById('address')?.value;
    const neighborhoodSelect = document.getElementById('neighborhood');
    const neighborhood = neighborhoodSelect?.options[neighborhoodSelect.selectedIndex].text;
    const deliveryFee = neighborhoodSelect ? parseFloat(neighborhoodSelect.options[neighborhoodSelect.selectedIndex]?.dataset.fee || 0) : 0;
    
    if (!address || !neighborhoodSelect.value) {
        alert('Por favor, preencha o endereço e selecione o bairro.');
        return;
    }

    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const total = subtotal + deliveryFee;

    let message = `*Pedido Gordin Lanches*%0A%0A`;
    message += `*Itens:*%0A`;
    cart.forEach(item => {
        message += `- ${item.quantity}x ${item.name} (R$ ${(item.price * item.quantity).toFixed(2)})%0A`;
    });
    
    message += `%0A*Subtotal:* R$ ${subtotal.toFixed(2)}`;
    message += `%0A*Entrega:* R$ ${deliveryFee.toFixed(2)} (${neighborhood})`;
    message += `%0A*Total:* R$ ${total.toFixed(2)}`;
    message += `%0A%0A*Endereço:* ${address}`;
    message += `%0A*Bairro:* ${neighborhood}`;

    const whatsappNumber = "553173524487";
    const whatsappUrl = `https://wa.me/${whatsappNumber}?text=${message}`;
    
    // Clear cart after redirect
    localStorage.removeItem('gordin_cart');
    
    window.open(whatsappUrl, '_blank');
}
