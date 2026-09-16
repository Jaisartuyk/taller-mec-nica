// JS para envío seguro de formularios modales por AJAX en Django
document.addEventListener("DOMContentLoaded", function() {
    // Click en botón para abrir el modal y cargar contenido
    document.querySelectorAll('[data-modal-target][data-url]').forEach(btn => {
        btn.addEventListener('click', function() {
            const modalId = btn.getAttribute('data-modal-target');
            const url = btn.getAttribute('data-url');
            
            console.log('Cargando modal:', modalId, 'URL:', url);
            
            // Verifica que el modal existe antes de manipularlo
            const modal = document.getElementById(modalId);
            if (!modal) {
                console.error(`Modal con ID ${modalId} no encontrado`);
                return;
            }
            
            const modalBody = modal.querySelector('.modal-body');
            if (!modalBody) {
                console.error(`No se encontró el modal-body en el modal ${modalId}`);
                return;
            }

            // Muestra el spinner
            modalBody.innerHTML = `
                <div class="text-center text-muted">
                    <div class="spinner-border"></div> Cargando...
                </div>
            `;

            // Crea una instancia del modal
            const modalInstance = new bootstrap.Modal(modal);
            
            // Carga el contenido del modal
            fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error al cargar el formulario');
                }
                return response.text();
            })
            .then(html => {
                modalBody.innerHTML = html;

                // Asigna la URL correcta al formulario que acabamos de cargar
                const form = modalBody.querySelector('form');
                if (form) {
                    form.setAttribute('action', url);
                }
                
                // Adjunta el manejador de envío y muestra el modal
                attachModalFormHandler(modalId);
                modalInstance.show();
            })
            .catch(error => {
                modalBody.innerHTML = `
                    <div class="alert alert-danger">
                        Error: ${error.message}
                    </div>
                `;
                console.error(`Error al cargar el modal ${modalId}:`, error);
            });
        });
    });
});

function attachModalFormHandler(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    const form = modal.querySelector('form');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const url = form.getAttribute('action');
        const formData = new FormData(form);
        const modalBody = form.closest('.modal-body');

        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
        .then(response => {
            // Clona la respuesta para poder leerla como JSON y como texto si falla
            const clonedResponse = response.clone();
            return response.json().catch(() => clonedResponse.text());
        })
        .then(data => {
            if (typeof data === 'object' && data.success && data.tabla) {
                // Caso 1: Éxito con actualización de tabla (conductores)
                const modalInstance = bootstrap.Modal.getInstance(modal);
                modalInstance.hide();
                const tablaContainer = document.getElementById('contenedor-tabla-conductores') || 
                                       document.getElementById('contenedor-tabla-vehiculos') || 
                                       document.getElementById('tabla-conductores-container');
                if (tablaContainer) {
                    tablaContainer.innerHTML = data.tabla;
                } else {
                    location.reload(); // Fallback si no encuentra el contenedor
                }
            } else if (typeof data === 'object' && !data.success && data.form) {
                // Caso 2: Error de validación, se recibe un formulario con errores
                if (modalBody) modalBody.innerHTML = data.form;
                attachModalFormHandler(modalId); // Re-enganchar el handler al nuevo formulario
            } else if (typeof data === 'string') {
                // Caso 3: Se recibe HTML directamente (error de formulario sin JSON)
                if (modalBody) modalBody.innerHTML = data;
                attachModalFormHandler(modalId); // Re-enganchar el handler
            } else {
                // Caso 4: Comportamiento por defecto para otros modales (ej. éxito sin tabla)
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error en la petición AJAX:', error);
            alert('Ocurrió un error. Por favor, intenta de nuevo.');
        });
    });
}