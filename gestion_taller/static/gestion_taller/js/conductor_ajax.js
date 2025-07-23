// Función para abrir el modal de edición de conductor
document.addEventListener('DOMContentLoaded', function() {
  document.addEventListener('click', function(e) {
    const btnEditar = e.target.closest('.btn-editar-conductor');
    if (btnEditar) {
      e.preventDefault();
      const url = btnEditar.getAttribute('href');
      
      // Mostrar indicador de carga
      const modal = document.getElementById('modalConductorEditar');
      if (modal) {
        const modalBody = modal.querySelector('.modal-body');
        if (modalBody) {
          modalBody.innerHTML = `
            <div class="text-center p-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
              </div>
              <p class="mt-2">Cargando formulario de edición...</p>
            </div>`;
        }
        
        // Mostrar el modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Cargar el formulario de edición
        fetch(url, {
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
        .then(response => response.text())
        .then(html => {
          // Crear un documento temporal para analizar el HTML
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, 'text/html');
          const formContent = doc.querySelector('.modal-dialog')?.parentNode?.innerHTML;
          
          if (formContent && modalBody) {
            modalBody.innerHTML = formContent;
            // Inicializar cualquier componente necesario
            initModalContent(modal);
          } else {
            throw new Error('No se pudo cargar el formulario de edición');
          }
        })
        .catch(error => {
          console.error('Error al cargar el formulario de edición:', error);
          if (modalBody) {
            modalBody.innerHTML = `
              <div class="alert alert-danger">
                <h5 class="alert-heading">Error</h5>
                <p>No se pudo cargar el formulario de edición. Por favor, intente nuevamente.</p>
                <button class="btn btn-sm btn-outline-secondary" onclick="window.location.reload()">
                  Recargar página
                </button>
              </div>`;
          }
        });
      }
    }
  });
});

// Función para inicializar el contenido del modal
function initModalContent(modalElement) {
  // Inicializar tooltips
  const tooltipTriggerList = [].slice.call(modalElement.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.forEach(function(tooltipTriggerEl) {
    new bootstrap.Tooltip(tooltipTriggerEl);
  });
  
  // Inicializar popovers
  const popoverTriggerList = [].slice.call(modalElement.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.forEach(function(popoverTriggerEl) {
    new bootstrap.Popover(popoverTriggerEl);
  });
}