// JS modular para catálogo de repuestos: AJAX y filtrado seguro

// Función para obtener el token CSRF de las cookies
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
    try {
      console.log('Agregando nuevo modal al DOM');
      
      // Cerrar cualquier modal existente primero
      const existingModal = document.getElementById('modalRepuesto');
      if (existingModal) {
        try {
          const bsModal = bootstrap.Modal.getInstance(existingModal);
          if (bsModal) {
            bsModal.hide();
          }
          existingModal.remove();
        } catch (e) {
          console.warn('Error al cerrar el modal existente:', e);
          existingModal.remove();
        }
      }
      
      // Crear la estructura completa del modal
      const modalHtml = `
        <div class="modal fade" id="modalRepuesto" tabindex="-1" aria-labelledby="modalRepuestoLabel" aria-hidden="true">
          <div class="modal-dialog modal-lg">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title" id="modalRepuestoLabel">Nuevo Repuesto</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
              </div>
              <div class="modal-body">
                ${html}
              </div>
            </div>
          </div>
        </div>
      `;
      
      // Crear un contenedor temporal para el HTML
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = modalHtml;
      
      // Obtener el elemento del modal
      const modalElement = tempDiv.firstElementChild;
      if (!modalElement) {
        throw new Error('No se pudo crear el elemento del modal');
      }
      
      // Agregar el modal al body
      document.body.appendChild(modalElement);
      
      // Inicializar el modal de Bootstrap
      const modal = new bootstrap.Modal(modalElement, {
        backdrop: 'static',
        keyboard: false
      });
      
      // Configurar el evento para limpiar el modal al cerrar
      const onHidden = function() {
        try {
          modal.dispose();
          if (document.body.contains(modalElement)) {
            document.body.removeChild(modalElement);
          }
        } catch (e) {
          console.warn('Error al limpiar el modal:', e);
        }
      };
      
      modalElement.addEventListener('hidden.bs.modal', onHidden);
      
      // Mostrar el modal
      try {
        modal.show();
        
        // Inicializar select2 si está presente
        if (window.jQuery && jQuery.fn.select2) {
          jQuery(modalElement).find('select.select2').select2({
            dropdownParent: modalElement,
            theme: 'bootstrap-5',
            width: '100%',
            dropdownAutoWidth: true
          });
        }
        
        // Configurar el envío del formulario
        const form = modalElement.querySelector('form');
        if (form) {
          form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Mostrar indicador de carga
            const submitButton = form.querySelector('button[type="submit"]');
            const originalButtonText = submitButton ? submitButton.innerHTML : '';
            
            if (submitButton) {
              submitButton.disabled = true;
              submitButton.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                Guardando...
              `;
            }
            
            // Enviar el formulario vía AJAX
            const formData = new FormData(form);
            
            fetch(form.action, {
              method: 'POST',
              body: formData,
              headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
              },
              credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
              if (data.success) {
                // Mostrar mensaje de éxito
                showToast('success', data.message || 'Operación exitosa');
                
                // Cerrar el modal
                modal.hide();
                
                // Recargar la página o redirigir
                if (data.redirect) {
                  window.location.href = data.redirect;
                } else {
                  window.location.reload();
                }
              } else {
                // Mostrar errores de validación
                if (data.errors) {
                  // Aquí podrías mostrar los errores en el formulario
                  console.error('Errores de validación:', data.errors);
                  showToast('danger', 'Por favor corrige los errores en el formulario');
                } else {
                  showToast('danger', data.message || 'Error al guardar el repuesto');
                }
                
                // Restaurar el botón de envío
                if (submitButton) {
                  submitButton.disabled = false;
                  submitButton.innerHTML = originalButtonText;
                }
              }
            })
            .catch(error => {
              console.error('Error al enviar el formulario:', error);
              showToast('danger', 'Error al procesar la solicitud');
              
              // Restaurar el botón de envío
              if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = originalButtonText;
              }
            });
          });
        }
      } catch (error) {
        console.error('Error al mostrar el modal:', error);
        showToast('danger', 'Error al cargar el formulario');
        throw error;
      }
      
      return modal;
    } catch (error) {
      console.error('Error en addNewModal:', error);
      showToast('danger', 'Error al cargar el formulario. Por favor, recarga la página e inténtalo de nuevo.');
      return null;
    }
  }

  // Función para mostrar el modal de repuesto
  function mostrarModalRepuesto(url, title = '') {
    console.log('Solicitando formulario desde:', url);
    
    // Cerrar cualquier modal existente primero
    const existingModal = document.getElementById('modalRepuesto');
    if (existingModal) {
      const bsModal = bootstrap.Modal.getInstance(existingModal);
      if (bsModal) {
        bsModal.hide();
      }
      existingModal.remove();
    }
    
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
    
    try {
      const loadingModalElement = loadingDiv.querySelector('#modalLoading');
      if (!loadingModalElement) {
        throw new Error('No se pudo crear el modal de carga');
      }
      
      const loadingModal = new bootstrap.Modal(loadingModalElement, {
        backdrop: 'static',
        keyboard: false
      });
      
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
        // Verificar si el HTML recibido es válido
        if (!html || typeof html !== 'string') {
          throw new Error('Respuesta del servidor no válida');
        }
        
        // Agregar el nuevo modal
        addNewModal(html);
      })
      .catch(error => {
        console.error('Error al cargar el formulario:', error);
        showToast('danger', error.message || 'No se pudo cargar el formulario.');
      });
      
    } catch (error) {
      console.error('Error al inicializar el modal de carga:', error);
      if (document.body.contains(loadingDiv)) {
        document.body.removeChild(loadingDiv);
      }
      showToast('danger', 'Error al inicializar el formulario. Por favor, inténtalo de nuevo.');
    }
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
    const btnEditar = e.target.closest('.btn-editar');
    if (btnEditar) {
      e.preventDefault();
      const url = btnEditar.getAttribute('data-url');
      if (url) {
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
    
    // Función para obtener el token CSRF de las cookies
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
    
    // Obtener el token CSRF del formulario o de las cookies
    let csrftoken = form.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrftoken) {
      csrftoken = getCookie('csrftoken');
    }
    
    // Si estamos en modo edición, asegurarse de incluir el ID
    if (repuestoId && !formData.has('id')) {
      formData.append('id', repuestoId);
    }
    
    // Configurar las cabeceras
    const headers = {
      'X-Requested-With': 'XMLHttpRequest'
    };
    
    // Agregar el token CSRF solo si existe
    if (csrftoken) {
      headers['X-CSRFToken'] = csrftoken;
    }
    
    // Enviar la solicitud al servidor
    fetch(actionUrl, {
      method: method,
      body: formData,
      headers: headers,
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
        console.log('Respuesta de error del servidor:', responseData);
        
        // Si hay errores de validación, mostrarlos en el formulario
        if (response.status === 400 && responseData.errors) {
          // Limpiar errores anteriores
          form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
          form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
          
          // Mostrar errores de validación
          if (typeof responseData.errors === 'object') {
            Object.entries(responseData.errors).forEach(([field, messages]) => {
              console.log(`Error en campo ${field}:`, messages);
              const input = form.querySelector(`[name="${field}"]`);
              if (input) {
                input.classList.add('is-invalid');
                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.textContent = Array.isArray(messages) ? messages.join(' ') : messages;
                input.parentNode.appendChild(errorDiv);
              } else {
                console.warn(`No se encontró el campo ${field} en el formulario`);
              }
            });
          } else {
            console.error('Formato de errores inesperado:', responseData.errors);
          }
          
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
