// JS modular para catálogo de repuestos: AJAX y filtrado seguro

// Función para mostrar notificaciones toast
function showToast(type, message) {
  const toastContainer = document.getElementById('toastContainer');
  if (!toastContainer) {
    console.error('No se encontró el contenedor de toasts');
    return;
  }

  const toastId = 'toast-' + Date.now();
  const toast = document.createElement('div');
  toast.id = toastId;
  toast.className = `toast align-items-center text-white bg-${type} border-0`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');
  toast.setAttribute('aria-atomic', 'true');
  
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        ${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;

  toastContainer.appendChild(toast);
  
  const bsToast = new bootstrap.Toast(toast, {
    autohide: true,
    delay: 3000
  });
  
  toast.addEventListener('hidden.bs.toast', function() {
    toast.remove();
  });
  
  bsToast.show();
}

document.addEventListener('DOMContentLoaded', function() {
  // Filtrado por categoría
  const filtroCategoria = document.getElementById('filtroCategoria');
  if (filtroCategoria) {
    filtroCategoria.addEventListener('change', function() {
      const categoria = this.value;
      const tarjetas = document.querySelectorAll('.repuesto-card');
      
      tarjetas.forEach(tarjeta => {
        if (!categoria || tarjeta.getAttribute('data-categoria') === categoria) {
          tarjeta.style.display = '';
        } else {
          tarjeta.style.display = 'none';
        }
      });
    });
  }

  // Función auxiliar para agregar un nuevo modal al DOM
  function addNewModal(html) {
    // Crear contenedor para el modal
    const modalDiv = document.createElement('div');
    modalDiv.id = 'modalRepuesto';
    modalDiv.className = 'modal fade';
    modalDiv.tabIndex = '-1';
    modalDiv.setAttribute('aria-hidden', 'true');
    
    // Insertar el HTML del modal
    modalDiv.innerHTML = html;
    
    // Agregar el modal al body
    document.body.appendChild(modalDiv);
    
    // Inicializar el modal de Bootstrap
    const modal = new bootstrap.Modal(modalDiv);
    
    // Configurar el evento para limpiar el modal al cerrar
    modalDiv.addEventListener('hidden.bs.modal', function() {
      // Esperar a que termine la animación antes de eliminar
      setTimeout(() => {
        if (document.body.contains(modalDiv)) {
          document.body.removeChild(modalDiv);
        }
      }, 300);
    });
    
    // Mostrar el modal
    modal.show();
    
    // Inicializar select2 si está presente
    if (window.jQuery && jQuery.fn.select2) {
      jQuery(modalDiv).find('select.select2').select2({
        dropdownParent: modalDiv,
        theme: 'bootstrap-5',
        width: '100%'
      });
    }
    
    return modal;
  }

  // Función para mostrar el modal de repuesto
  function mostrarModalRepuesto(url, title = '') {
    console.log('Solicitando formulario desde:', url);
    
    // Mostrar indicador de carga
    const loadingHtml = `
      <div class="modal fade" id="modalLoading" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">${title || 'Cargando...'}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body text-center py-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
              </div>
              <p class="mt-3 mb-0">Cargando formulario, por favor espere...</p>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // Crear y mostrar el modal de carga
    const loadingDiv = document.createElement('div');
    loadingDiv.innerHTML = loadingHtml;
    document.body.appendChild(loadingDiv);
    const loadingModal = new bootstrap.Modal(loadingDiv.querySelector('#modalLoading'));
    loadingModal.show();
    
    // Asegurarse de que la URL sea absoluta
    let requestUrl = url;
    if (!url.startsWith('http') && !url.startsWith('/')) {
      requestUrl = `/${url}`;
    }
    
    fetch(requestUrl, {
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'text/html, application/json'
      },
      credentials: 'same-origin'
    })
    .then(async response => {
      console.log('Respuesta recibida, estado:', response.status);
      
      // Cerrar el modal de carga
      loadingModal.hide();
      document.body.removeChild(loadingDiv);
      
      // Verificar si hay un error en la respuesta
      if (!response.ok) {
        let errorMessage = `Error en la petición. Estado: ${response.status}`;
        
        // Intentar obtener más detalles del error si es JSON
        try {
          const errorData = await response.json();
          if (errorData.message) {
            errorMessage = errorData.message;
          }
        } catch (e) {
          // Si no se puede parsear como JSON, usar el mensaje de error estándar
          console.error('No se pudo parsear la respuesta de error:', e);
        }
        
        console.error('Error en la petición:', errorMessage);
        throw new Error(errorMessage);
      }
      
      // Si la respuesta es JSON, manejarla como error inesperado
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        throw new Error(data.message || 'Error inesperado del servidor');
      }
      
      return response.text();
    })
    .then(html => {
      // Cerrar y eliminar el modal existente si hay uno
      const modalExistente = document.getElementById('modalRepuesto');
      if (modalExistente) {
        const bsModal = bootstrap.Modal.getInstance(modalExistente);
        if (bsModal) {
          bsModal.hide();
          modalExistente.addEventListener('hidden.bs.modal', function handler() {
            modalExistente.remove();
            addNewModal(html);
            modalExistente.removeEventListener('hidden.bs.modal', handler);
          });
        } else {
          modalExistente.remove();
          addNewModal(html);
        }
      } else {
        addNewModal(html);
      }
    })
    .catch(error => {
      console.error('Error al cargar el formulario:', error);
      showToast('danger', error.message || 'No se pudo cargar el formulario.');
    });
  }

  // Manejador para el botón de nuevo repuesto
  document.addEventListener('click', function(e) {
    const btnNuevo = e.target.closest('#btnNuevoRepuesto');
    if (btnNuevo) {
      e.preventDefault();
      // Usar la URL correcta para nuevo repuesto
      const url = '/repuestos/nuevo/';
      mostrarModalRepuesto(url, 'Nuevo Repuesto');
    }
  });

  // Manejador para el botón de editar repuesto
  document.addEventListener('click', function(e) {
    const btnEditar = e.target.closest('.btn-editar-repuesto');
    if (btnEditar) {
      e.preventDefault();
      const repuestoId = btnEditar.getAttribute('data-id');
      if (repuestoId) {
        const url = `/repuestos/editar/${repuestoId}/`;
        mostrarModalRepuesto(url, 'Editar Repuesto');
      }
    }
  });

  // Envío del formulario de repuesto
  document.addEventListener('submit', function(e) {
    const form = e.target;
    if (form.id !== 'formRepuesto') return;
    
    e.preventDefault();
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn ? submitBtn.innerHTML : '';
    
    // Mostrar indicador de carga en el botón
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        Guardando...
      `;
    }
    
    // Determinar si es una edición (tiene un ID) o un nuevo registro
    const repuestoId = form.querySelector('[name="id"]')?.value;
    
    // Construir la URL correcta según sea edición o creación
    let actionUrl, method;
    
    if (repuestoId) {
      // Edición: PUT a /repuestos/editar/<id>/
      actionUrl = `/repuestos/editar/${repuestoId}/`;
      method = 'POST';
      // Agregar el método real como parámetro para Django
      formData.append('_method', 'PUT');
    } else {
      // Nuevo: POST a /repuestos/nuevo/
      actionUrl = '/repuestos/nuevo/';
      method = 'POST';
    }
    
    console.log('Enviando formulario a:', actionUrl, 'Método:', method, 'ID:', repuestoId || 'nuevo');
    
    // Obtener el token CSRF de las cookies
    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
    
    const csrftoken = getCookie('csrftoken');
    
    // Enviar la solicitud al servidor
    fetch(actionUrl, {
      method: method,
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrftoken || ''
      },
      credentials: 'same-origin'
    })
    .then(async response => {
      const contentType = response.headers.get('content-type');
      let responseData;
      
      // Intentar parsear la respuesta como JSON
      if (contentType && contentType.includes('application/json')) {
        responseData = await response.json();
      } else {
        const text = await response.text();
        console.error('Respuesta inesperada del servidor:', text);
        throw new Error('Formato de respuesta no válido');
      }
      
      if (!response.ok) {
        // Si hay errores de validación, mostrarlos en el formulario
        if (response.status === 400 && responseData.errors) {
          // Limpiar errores anteriores
          form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
          form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
          
          // Mostrar errores de validación
          Object.entries(responseData.errors).forEach(([field, messages]) => {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) {
              input.classList.add('is-invalid');
              const errorDiv = document.createElement('div');
              errorDiv.className = 'invalid-feedback';
              errorDiv.textContent = Array.isArray(messages) ? messages.join(' ') : messages;
              input.parentNode.appendChild(errorDiv);
            }
          });
          
          throw new Error('Por favor corrija los errores en el formulario');
        }
        
        // Otros tipos de errores
        throw new Error(responseData.message || `Error en la solicitud (${response.status})`);
      }
      
      return responseData;
    })
    .then(data => {
      if (data && data.success) {
        // Mostrar mensaje de éxito
        showToast('success', data.message || 'Operación exitosa');
        
        // Cerrar el modal
        const modal = document.getElementById('modalRepuesto');
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) {
          bsModal.hide();
        }
        
        // Recargar la página después de un breve retraso
        setTimeout(() => {
          if (data.redirect) {
            window.location.href = data.redirect;
          } else {
            window.location.reload();
          }
        }, 800);
      } else {
        throw new Error(data?.message || 'La operación no se completó correctamente');
      }
    })
    .catch(error => {
      console.error('Error en la solicitud:', error);
      
      // Mostrar mensaje de error
      showToast('danger', error.message || 'Error al procesar la solicitud');
      
      // Restaurar el botón
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
      }
      
      // Si es un error de red, mostrar un mensaje más descriptivo
      if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
        showToast('danger', 'Error de conexión. Por favor, verifique su conexión a internet.');
      }
    });
  });
});
