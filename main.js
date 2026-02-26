// ==========================================
// 1. CONFIGURACIÓN Y VARIABLES GLOBALES
// ==========================================
const API_URL = 'https://valle-verde-plataforma-dev.onrender.com/api';
const contenedorPropiedades = document.getElementById('lista-propiedades');
const modal = document.getElementById('modal-lead');
let propiedadesGlobales = []; // Caché para filtrar instantáneamente sin gastar red

// ==========================================
// 2. COMPONENTES UI (El Patrón Yankee Clean)
// ==========================================
const UI = {
    loader: () => `<div style="text-align: center; padding: 2rem; color: #2e7d32;">Cargando propiedades de Valle Verde... ⏳</div>`,
    error: (msg) => `<div style="text-align: center; color: #d32f2f; padding: 2rem;">⚠️ ${msg}</div>`,
    sinResultados: () => `<div style="text-align: center; padding: 2rem; width: 100%;">No se encontraron propiedades con estos filtros.</div>`,
    
    tarjeta: (prop) => {
        const imagenUrl = prop.imagenes?.[0]?.url || 'https://via.placeholder.com/400x300?text=Valle+Verde';
        // Formateo de moneda profesional
        const precio = new Intl.NumberFormat('es-MX', { style: 'currency', currency: prop.moneda || 'MXN' }).format(prop.precio);
        
        // Evitar errores de comillas en títulos al pasarlos por onclick
        const tituloSeguro = prop.titulo.replace(/'/g, "\\'");

        return `
            <article class="card">
                <img src="${imagenUrl}" alt="Foto de ${prop.titulo}">
                <div class="card-content">
                    <span class="badge badge-${prop.operacion.toLowerCase()}">${prop.operacion.toUpperCase()}</span>
                    <h3>${prop.titulo}</h3>
                    <p class="precio">${precio}</p>
                    <p class="ubicacion">📍 ${prop.colonia}</p>
                    <button class="btn-primary" onclick="abrirModal(${prop.id}, '${tituloSeguro}')" style="width: 100%; margin-top: 1rem;">Me interesa</button>
                </div>
            </article>
        `;
    }
};

// ==========================================
// 3. LÓGICA DE DATOS Y RENDERIZADO
// ==========================================
async function obtenerPropiedades() {
    contenedorPropiedades.innerHTML = UI.loader(); // UX: Mostrar que estamos cargando
    
    try {
        const respuesta = await fetch(`${API_URL}/propiedades`);
        if (!respuesta.ok) throw new Error('Servidor de Render no responde');
        
        propiedadesGlobales = await respuesta.json(); // Guardamos en caché local
        dibujarTarjetas(propiedadesGlobales);
    } catch (error) {
        console.error("Error de Red:", error);
        contenedorPropiedades.innerHTML = UI.error('No pudimos conectar con el inventario. Intenta más tarde.');
    }
}

function dibujarTarjetas(propiedades) {
    if (propiedades.length === 0) {
        contenedorPropiedades.innerHTML = UI.sinResultados();
        return;
    }
    
    // RENDERIZADO ÓPTIMO: .map() crea un array de HTMLs y .join('') lo vuelve un solo string
    // Esto evita el "DOM Trashing" y hace que la página sea rapidísima
    contenedorPropiedades.innerHTML = propiedades.map(prop => UI.tarjeta(prop)).join('');
}

// ==========================================
// 4. FILTROS EN MEMORIA (Instantáneos)
// ==========================================
function aplicarFiltros() {
    const tipo = document.getElementById('filtro-tipo').value;
    const operacion = document.getElementById('filtro-operacion').value;
    
    let propiedadesFiltradas = propiedadesGlobales;
    
    if (tipo !== 'todos') {
        propiedadesFiltradas = propiedadesFiltradas.filter(p => p.tipo.toLowerCase() === tipo.toLowerCase());
    }
    if (operacion !== 'todos') {
        propiedadesFiltradas = propiedadesFiltradas.filter(p => p.operacion.toLowerCase() === operacion.toLowerCase());
    }
    
    dibujarTarjetas(propiedadesFiltradas);
}

// ==========================================
// 5. LÓGICA DEL FORMULARIO Y MODAL
// ==========================================
function abrirModal(id, titulo) {
    document.getElementById('propiedad-id').value = id;
    document.getElementById('propiedad-seleccionada-nombre').innerText = titulo;
    modal.style.display = "flex"; // "flex" centra mejor el modal que "block" si usamos CSS moderno
}

function cerrarModal() {
    modal.style.display = "none";
    document.getElementById('form-lead').reset(); // Limpiar el formulario al cerrar
}

document.getElementById('form-lead').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const btnSubmit = e.target.querySelector('button[type="submit"]');
    const textoOriginal = btnSubmit.innerText;
    
    // UX: Desactivar botón mientras carga para evitar envíos dobles
    btnSubmit.innerText = 'Enviando... ⏳';
    btnSubmit.disabled = true;
    
    const nuevoLead = {
        nombre: document.getElementById('nombre').value,
        email: document.getElementById('email').value,
        telefono: document.getElementById('telefono').value,
        notas: document.getElementById('notas').value,
        propiedad_interes_id: document.getElementById('propiedad-id').value
    };

    try {
        const res = await fetch(`${API_URL}/leads`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(nuevoLead)
        });

        if (res.ok) {
            alert("¡Gracias! Un asesor de Inmobiliaria Valle Verde te contactará pronto.");
            cerrarModal();
        } else {
            throw new Error('Error en el servidor');
        }
    } catch (error) {
        alert("Hubo un error al enviar tus datos. Por favor, intenta de nuevo.");
    } finally {
        // Restaurar el botón
        btnSubmit.innerText = textoOriginal;
        btnSubmit.disabled = false;
    }
});

// ==========================================
// 6. INICIALIZADOR GLOBAL (Lógica del Header)
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    // 6.1 Cargar inventario al abrir la página
    obtenerPropiedades();

    // 6.2 Lógica del Menú Móvil
    const mobileBtn = document.getElementById('mobile-menu-btn');
    const mainNav = document.getElementById('main-nav');

    if (mobileBtn && mainNav) {
        mobileBtn.addEventListener('click', () => {
            mainNav.classList.toggle('is-active');
        });
    }
});