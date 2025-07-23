// servicio_ajax.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('servicio_ajax.js cargado correctamente');
    
    // Función para mostrar notificaciones toast
    function showToast(type, message) {
        // Crear contenedor si no existe
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.position = 'fixed';
            toastContainer.style.top = '20px';
            toastContainer.style.right = '20px';
            toastContainer.style.zIndex = '1100';
            document.body.appendChild(toastContainer);
        }
        
        // Crear toast
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = 'toast';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.setAttribute('data-bs-delay', '5000');
        
        toast.innerHTML = `
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">${type === 'success' ? 'Éxito' : 'Error'}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Cerrar"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // Agregar y mostrar el toast
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Eliminar el toast cuando se oculte
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
    
    // Función para cargar un formulario en el modal
    function loadFormInModal(url) {
        console.log('Cargando formulario desde:', url);
        
        const modalElement = document.getElementById('modalServicio');
        const modalContent = modalElement ? modalElement.querySelector('.modal-content') : null;
        
        // Asegurarse de que el modal esté en el DOM
        if (!modalElement || !modalContent) {
            console.error('No se encontró el elemento del modal con ID modalServicio');
            showToast('error', 'Error al cargar el formulario');
            return;
        }
        
        // Inicializar el modal de Bootstrap
        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
        
        // Mostrar indicador de carga
        modalContent.innerHTML = `
            <div class="modal-header">
                <h5 class="modal-title">Cargando...</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
            </div>
            <div class="modal-body text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-2">Cargando formulario, por favor espere...</p>
            </div>
        `;
        
        // Mostrar el modal
        modal.show();
        
        // Cargar el formulario vía Fetch API
        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'text/html'
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Error en la petición');
            return response.text();
        })
        .then(html => {
            console.log('Formulario cargado correctamente');
            modalContent.innerHTML = html;
            
            // Inicializar selects con select2 si está disponible
            if (window.jQuery && jQuery.fn.select2) {
                const selects = modalContent.querySelectorAll('select');
                selects.forEach(select => {
                    jQuery(select).select2({
                        dropdownParent: document.getElementById('modalServicio'),
                        width: '100%',
                        theme: 'bootstrap-5'
                    });
                });
            }
            
            // Manejar el envío del formulario
            const form = modalContent.querySelector('form');
            if (form) {
                form.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const submitBtn = form.querySelector('button[type="submit"]');
                    const originalBtnText = submitBtn.innerHTML;
                    
                    // Deshabilitar el botón y mostrar spinner
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Guardando...';
                    
                    // Limpiar mensajes de error previos
                    form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
                    form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
                    
                    // Crear FormData para el envío
                    const formData = new FormData(form);
                    
                    // Enviar el formulario vía Fetch API
                    fetch(form.action, {
                        method: form.method,
                        body: formData,
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => response.json())
                    .then(response => {
                        if (response.success) {
                            // Mostrar mensaje de éxito
                            showToast('success', response.message || 'Servicio guardado correctamente');
                            
                            // Cerrar el modal después de un breve retraso
                            setTimeout(() => {
                                modal.hide();
                                
                                // Recargar la página si se especificó
                                if (response.redirect) {
                                    window.location.href = response.redirect;
                                } else if (response.reload) {
                                    window.location.reload();
                                }
                            }, 1500);
                        } else {
                            // Mostrar errores de validación
                            if (response.errors) {
                                Object.entries(response.errors).forEach(([field, errors]) => {
                                    const input = document.getElementById(`id_${field}`);
                                    if (input) {
                                        input.classList.add('is-invalid');
                                        const errorDiv = document.createElement('div');
                                        errorDiv.className = 'invalid-feedback d-block';
                                        errorDiv.textContent = Array.isArray(errors) ? errors.join(' ') : errors;
                                        input.parentNode.insertBefore(errorDiv, input.nextSibling);
                                    }
                                });
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error al guardar el servicio', error);
                        showToast('error', 'Error al guardar el servicio');
                    })
                    .finally(() => {
                        // Restaurar el botón
                        if (submitBtn) {
                            submitBtn.disabled = false;
                            submitBtn.innerHTML = originalBtnText;
                        }
                    });
                });
            }
        })
        .catch(error => {
            console.error('Error al cargar el formulario:', error);
            showToast('error', 'Error al cargar el formulario');
            modal.hide();
        });
    }
    
    // Manejar clic en botón de nuevo/editar servicio
    document.addEventListener('click', function(e) {
        const target = e.target.closest('.btn-edit-servicio, #btn-nuevo-servicio');
        if (target) {
            e.preventDefault();
            const url = target.getAttribute('data-url');
            if (url) {
                loadFormInModal(url);
            }
        }
    });
    
    // Manejar eliminación de servicio
    document.addEventListener('click', function(e) {
        const target = e.target.closest('.btn-delete-servicio');
        if (target) {
            e.preventDefault();
            const url = target.getAttribute('data-url');
            const servicioId = target.getAttribute('data-id');
            
            // Mostrar modal de confirmación
            const confirmModal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
            const confirmBtn = document.getElementById('confirmDeleteBtn');
            
            if (confirmBtn) {
                // Configurar el manejador de eventos para el botón de confirmación
                const handleConfirm = function() {
                    const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]').value;
                    
                    fetch(url, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-CSRFToken': csrfToken
                        },
                        body: `servicio_id=${encodeURIComponent(servicioId)}`
                    })
                    .then(response => response.json())
                    .then(response => {
                        if (response.success) {
                            showToast('success', response.message || 'Servicio eliminado correctamente');
                            
                            // Cerrar el modal de confirmación
                            confirmModal.hide();
                            
                            // Recargar la página después de un breve retraso
                            setTimeout(() => {
                                if (response.redirect) {
                                    window.location.href = response.redirect;
                                } else {
                                    window.location.reload();
                                }
                            }, 1000);
                        } else {
                            showToast('error', response.message || 'Error al eliminar el servicio');
                        }
                    })
                    .catch(error => {
                        console.error('Error al eliminar el servicio', error);
                        showToast('error', 'Error al eliminar el servicio');
                    });
                };
                
                // Eliminar manejadores anteriores y agregar uno nuevo
                confirmBtn.removeEventListener('click', handleConfirm);
                confirmBtn.addEventListener('click', handleConfirm);
                
                // Mostrar el modal de confirmación
                confirmModal.show();
            }
        }
    });
});
