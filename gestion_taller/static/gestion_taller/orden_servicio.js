// JS para mejorar la experiencia en el listado y detalle de órdenes de servicio
// (agrega aquí lógica futura para AJAX, impresión, validaciones, etc)

document.addEventListener('DOMContentLoaded', function() {
  // Sugerencia dinámica de servicios por kilometraje
  const vehiculoSelect = document.getElementById('id_vehiculo');
  const kilometrajeInput = document.getElementById('id_kilometraje');
  const serviciosSelect = document.getElementById('id_servicios');
  let mensajeSugerencia = document.getElementById('sugerencia-servicios');
  if (!mensajeSugerencia) {
    mensajeSugerencia = document.createElement('div');
    mensajeSugerencia.id = 'sugerencia-servicios';
    mensajeSugerencia.className = 'alert alert-info mt-2';
    serviciosSelect.parentNode.insertBefore(mensajeSugerencia, serviciosSelect);
  }
  function sugerirServicios() {
    const vehiculoId = vehiculoSelect.value;
    const kilometraje = kilometrajeInput.value;
    if (!vehiculoId || !kilometraje) {
      mensajeSugerencia.style.display = 'none';
      return;
    }
    fetch(`/ajax/sugerir-servicios/?vehiculo_id=${vehiculoId}&kilometraje=${kilometraje}`)
      .then(response => response.json())
      .then(data => {
        const sugeridos = data.sugeridos || [];
        // Des-selecciona todos
        for (const option of serviciosSelect.options) {
          option.selected = false;
        }
        if (sugeridos.length > 0) {
          // Preselecciona sugeridos
          for (const option of serviciosSelect.options) {
            if (sugeridos.includes(parseInt(option.value))) {
              option.selected = true;
            }
          }
          mensajeSugerencia.innerHTML = '<strong>Servicios recomendados:</strong> Se han preseleccionado los servicios sugeridos según el kilometraje actual.';
          mensajeSugerencia.style.display = 'block';
        } else {
          mensajeSugerencia.innerHTML = 'No hay servicios recomendados para el kilometraje actual.';
          mensajeSugerencia.style.display = 'block';
        }
        // Si usas select2, actualiza
        if ($(serviciosSelect).hasClass('select2')) {
          $(serviciosSelect).trigger('change');
        }
      })
      .catch(() => {
        mensajeSugerencia.innerHTML = 'No se pudo obtener la sugerencia de servicios.';
        mensajeSugerencia.style.display = 'block';
      });
  }
  if (vehiculoSelect && kilometrajeInput && serviciosSelect) {
    vehiculoSelect.addEventListener('change', sugerirServicios);
    kilometrajeInput.addEventListener('input', sugerirServicios);
  }
});
