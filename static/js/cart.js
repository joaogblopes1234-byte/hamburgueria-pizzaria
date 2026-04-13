// Shopping Cart Logic for Gordin Lanches

let cart = JSON.parse(sessionStorage.getItem('gordin_cart')) || [];

function updateCartCount() {
    // Sincroniza a variável cart com o sessionStorage para garantir dados frescos
    cart = JSON.parse(sessionStorage.getItem('gordin_cart')) || [];
    
    const countElement = document.getElementById('cart-count');
    const mobileCountElement = document.getElementById('mobile-cart-count');
    const floatingBar = document.getElementById('floating-cart-bar');
    const floatingCount = document.getElementById('floating-cart-count');
    const floatingTotal = document.getElementById('floating-cart-total');
    
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    const totalPrice = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

    if (countElement) {
        countElement.innerText = totalItems;
    }

    if (mobileCountElement) {
        mobileCountElement.innerText = totalItems;
        mobileCountElement.style.display = totalItems > 0 ? 'flex' : 'none';
    }

    if (floatingBar) {
        // Show floating bar only if there are items AND we are NOT on the cart page
        const isCartPage = window.location.pathname.includes('/cart');
        if (totalItems > 0 && !isCartPage) {
            floatingBar.style.display = 'flex';
            if (floatingCount) floatingCount.innerText = totalItems;
            if (floatingTotal) floatingTotal.innerText = `R$ ${totalPrice.toFixed(2)}`;
        } else {
            floatingBar.style.display = 'none';
        }
    }
}

function saveCart() {
    sessionStorage.setItem('gordin_cart', JSON.stringify(cart));
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
            product_id: parseInt(productId),
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
    const neighborhoodInput = document.getElementById('neighborhood');
    const datalist = document.getElementById('neighborhoods-list');
    const checkoutBtn = document.querySelector('button[onclick="checkout()"]');
    const neighborhoodStatus = document.getElementById('neighborhood-status');
    
    let deliveryFee = 0;
    let isValidNeighborhood = false;
    let matchedName = "";

    if (neighborhoodInput && datalist) {
        let value = neighborhoodInput.value.trim().toLowerCase();
        const options = datalist.options;
        
        // 1. Tentar match exato (ignora case)
        for (let i = 0; i < options.length; i++) {
            if (options[i].value.toLowerCase() === value) {
                deliveryFee = parseFloat(options[i].dataset.fee || 0);
                isValidNeighborhood = true;
                matchedName = options[i].value;
                break;
            }
        }

        // 2. Se não encontrou match exato, tentar match parcial ou sugerir
        if (!isValidNeighborhood && value.length > 3) {
            for (let i = 0; i < options.length; i++) {
                const optName = options[i].value.toLowerCase();
                // Verifica se começa igual ou se é plural/singular (Laranjeira vs Laranjeiras)
                if (optName.startsWith(value) || value.startsWith(optName)) {
                    // Sugere o bairro correto se a diferença for pequena
                    if (Math.abs(optName.length - value.length) <= 2) {
                        neighborhoodStatus.innerHTML = `Você quis dizer <strong>${options[i].value}</strong>? <button onclick="selectNeighborhood('${options[i].value}')" style="background: var(--secondary); border: none; padding: 2px 8px; border-radius: 5px; cursor: pointer; font-size: 0.8rem; margin-left: 5px;">Sim</button>`;
                        neighborhoodStatus.style.color = "var(--primary)";
                        break;
                    }
                }
            }
        } else if (isValidNeighborhood) {
            if (neighborhoodStatus) neighborhoodStatus.innerText = "";
        }
        
        // Sempre habilitado para permitir que o usuário veja o que falta ao clicar (ou peça login)
        if (checkoutBtn) {
            checkoutBtn.disabled = false;
            checkoutBtn.innerHTML = 'Finalizar no WhatsApp <i class="fab fa-whatsapp"></i>';
            checkoutBtn.style.opacity = "1";
        }
    }

    const total = subtotal + deliveryFee;

    const subtotalEl = document.getElementById('subtotal');
    const deliveryFeeEl = document.getElementById('delivery-fee');
    const totalEl = document.getElementById('total');

    if (subtotalEl) subtotalEl.innerText = `R$ ${subtotal.toFixed(2)}`;
    
    if (deliveryFeeEl) {
        const oldFee = deliveryFeeEl.innerText;
        deliveryFeeEl.innerText = `R$ ${deliveryFee.toFixed(2)}`;
        if (oldFee !== `R$ ${deliveryFee.toFixed(2)}` && oldFee !== "R$ 0.00") {
            deliveryFeeEl.classList.add('price-updated');
            setTimeout(() => deliveryFeeEl.classList.remove('price-updated'), 800);
        }
    }

    if (totalEl) {
        const oldTotal = totalEl.innerText;
        totalEl.innerText = `R$ ${total.toFixed(2)}`;
        if (oldTotal !== `R$ ${total.toFixed(2)}` && oldTotal !== "R$ 0.00") {
            totalEl.classList.add('price-updated');
            setTimeout(() => totalEl.classList.remove('price-updated'), 800);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateCartCount();
    renderCart();
});

// Garante que o contador de itens e a barra flutuante sejam reinicializados se o usuário usar o botão "Voltar"
window.addEventListener('pageshow', (event) => {
    updateCartCount();
    renderCart();
});

document.addEventListener('DOMContentLoaded', () => {
    const neighborhoodSelect = document.getElementById('neighborhood');
    const streetInput = document.getElementById('street');
    const numberInput = document.getElementById('number');
    const complementInput = document.getElementById('complement');

    // Carregar dados salvos
    const savedStreet = sessionStorage.getItem('gordin_street');
    const savedNumber = sessionStorage.getItem('gordin_number');
    const savedComplement = sessionStorage.getItem('gordin_complement');
    const savedNeighborhood = sessionStorage.getItem('gordin_neighborhood');

    if (savedStreet && streetInput) streetInput.value = savedStreet;
    if (savedNumber && numberInput) numberInput.value = savedNumber;
    if (savedComplement && complementInput) complementInput.value = savedComplement;

    if (savedNeighborhood && neighborhoodSelect) {
        neighborhoodSelect.value = savedNeighborhood;
        renderCart();
    }

    if (streetInput) {
        streetInput.addEventListener('input', () => {
            sessionStorage.setItem('gordin_street', streetInput.value);
        });
    }

    if (numberInput) {
        numberInput.addEventListener('input', () => {
            sessionStorage.setItem('gordin_number', numberInput.value);
        });
    }

    if (complementInput) {
        complementInput.addEventListener('input', () => {
            sessionStorage.setItem('gordin_complement', complementInput.value);
        });
    }

    if (neighborhoodSelect) {
        neighborhoodSelect.addEventListener('input', () => {
            sessionStorage.setItem('gordin_neighborhood', neighborhoodSelect.value);
            renderCart();
        });
    }
});

function selectNeighborhood(name) {
    const neighborhoodInput = document.getElementById('neighborhood');
    if (neighborhoodInput) {
        neighborhoodInput.value = name;
        sessionStorage.setItem('gordin_neighborhood', name);
        renderCart();
    }
}

function checkout() {
    const checkoutBtn = document.querySelector('button[onclick="checkout()"]');
    if (checkoutBtn) {
        checkoutBtn.disabled = true;
        checkoutBtn.innerHTML = 'Processando... <i class="fas fa-spinner fa-spin"></i>';
    }

    const street = document.getElementById('street')?.value.trim();
    const number = document.getElementById('number')?.value.trim();
    const complement = document.getElementById('complement')?.value.trim();

    const neighborhoodInput = document.getElementById('neighborhood');
    const datalist = document.getElementById('neighborhoods-list');
    const customerName = document.getElementById('customer_name')?.value;
    const customerPhone = document.getElementById('customer_phone')?.value;
    
    let neighborhoodId = null;
    let neighborhoodName = null;
    let deliveryFee = 0;
    let found = false;

    if (neighborhoodInput && datalist) {
        const value = neighborhoodInput.value.trim().toLowerCase();
        const options = datalist.options;
        for (let i = 0; i < options.length; i++) {
            if (options[i].value.toLowerCase() === value) {
                neighborhoodId = options[i].dataset.id;
                neighborhoodName = options[i].value; // Nome oficial
                deliveryFee = parseFloat(options[i].dataset.fee || 0);
                found = true;
                break;
            }
        }
    }
    
    // Validação de campos obrigatórios
    if (!street || !number || !found) {
        alert('Por favor, preencha a Rua, o Número e selecione um bairro válido da lista.');
        if (checkoutBtn) {
            checkoutBtn.disabled = false;
            checkoutBtn.innerHTML = 'Finalizar no WhatsApp <i class="fab fa-whatsapp"></i>';
        }
        return;
    }

    // Concatenate address for DB
    const fullAddress = `${street}, ${number}${complement ? ' - ' + complement : ''}`;

    // Se o campo de nome/telefone estiver visível (visitante), eles são obrigatórios
    if (document.getElementById('customer_name') && (!customerName || !customerPhone)) {
        alert('Por favor, preencha seu Nome e WhatsApp para finalizar o pedido.');
        if (checkoutBtn) {
            checkoutBtn.disabled = false;
            checkoutBtn.innerHTML = 'Finalizar no WhatsApp <i class="fab fa-whatsapp"></i>';
        }
        return;
    }

    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const total = subtotal + deliveryFee;

    // Send to backend via AJAX
    fetch('/api/checkout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            address: fullAddress,
            neighborhood_id: parseInt(neighborhoodId),
            items: cart.map(item => ({
                product_id: item.product_id,
                quantity: item.quantity,
                price: item.price,
                name: item.name 
            })),
            delivery_fee: deliveryFee,
            total_price: total,
            customer_name: customerName,
            customer_phone: customerPhone
        })
    }).then(async response => {
        if (!response.ok) {
            // Se for 401 (Não autorizado), a sessão provavelmente expirou
            if (response.status === 401) {
                throw new Error('SESSION_EXPIRED');
            }
            
            // Tenta pegar a mensagem de erro do JSON se existir
            try {
                const errorData = await response.json();
                throw new Error(errorData.message || 'SERVER_ERROR');
            } catch (e) {
                if (e.message === 'SESSION_EXPIRED') throw e;
                throw new Error('SERVER_ERROR');
            }
        }
        return response.json();
    }).then(data => {
        if (data.success) {
            // Gera string para WhatsApp ANTES de limpar o carrinho
            const customerName = document.getElementById('customer_name')?.value;
            let message = `*Pedido Gordin Lanches (Pedido #${data.order_id})*\n`;
            if (customerName) {
                message += `*Cliente:* ${customerName}\n`;
            }
            message += `\n*Itens:*\n`;
            
            cart.forEach(item => {
                message += `- ${item.quantity}x ${item.name} (R$ ${(item.price * item.quantity).toFixed(2)})\n`;
            });
            
            message += `\n*Subtotal:* R$ ${subtotal.toFixed(2)}`;
            message += `\n*Entrega:* R$ ${deliveryFee.toFixed(2)} (${neighborhoodName})`;
            message += `\n*Total:* R$ ${total.toFixed(2)}`;
            message += `\n\n*Endereço:* ${fullAddress}`;
            message += `\n*Bairro:* ${neighborhoodName}`;

            // Limpa carrinho local e estado na memória AGORA
            sessionStorage.removeItem('gordin_cart');
            sessionStorage.removeItem('gordin_street');
            sessionStorage.removeItem('gordin_number');
            sessionStorage.removeItem('gordin_complement');
            sessionStorage.removeItem('gordin_neighborhood');
            cart = [];
            updateCartCount(); 

            const whatsappNumber = "5531994627746";
            const whatsappUrl = `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(message)}`;
            
            // window.open pode ser bloqueado em mobile se não for ação direta,
            // mas aqui estamos dentro de um then. Tentaremos location.href se falhar ou se preferir.
            try {
                const win = window.open(whatsappUrl, '_blank');
                if (!win) window.location.href = whatsappUrl;
            } catch (e) {
                window.location.href = whatsappUrl;
            }
            
            // Em vez de reload imediato, mostra mensagem e limpa a tela
            const container = document.querySelector('.container');
            if (container) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 4rem 2rem; background: white; border-radius: 20px; box-shadow: var(--shadow); margin-top: 2rem;">
                        <div style="font-size: 4rem; color: var(--success); margin-bottom: 1.5rem;"><i class="fas fa-check-circle"></i></div>
                        <h2 style="margin-bottom: 1rem;">Pedido Iniciado!</h2>
                        <p style="color: #666; margin-bottom: 2rem;">Seu pedido foi registrado no sistema e o WhatsApp foi aberto. Finalize o envio por lá!</p>
                        <a href="/" class="btn btn-primary">Voltar para o Início</a>
                    </div>
                `;
            }
        } else {
            alert("Ocorreu um erro ao processar seu pedido: " + (data.message || "Tente novamente ou contate o suporte."));
            if (checkoutBtn) {
                checkoutBtn.disabled = false;
                checkoutBtn.innerHTML = 'Finalizar no WhatsApp <i class="fab fa-whatsapp"></i>';
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        
        if (error.message === 'SESSION_EXPIRED') {
            alert("Sua sessão expirou. Por favor, faça login novamente para finalizar o pedido.");
            window.location.href = '/login?next=/cart';
        } else if (error.message === 'SERVER_ERROR') {
            alert("Ocorreu um erro interno no servidor ao processar seu pedido. Por favor, tente novamente mais tarde ou chame no WhatsApp direto.");
        } else {
            alert("Ocorreu um erro na conexão ou ao processar os dados. Verifique sua internet.");
        }

        if (checkoutBtn) {
            checkoutBtn.disabled = false;
            checkoutBtn.innerHTML = 'Finalizar no WhatsApp <i class="fab fa-whatsapp"></i>';
        }
    });
}
