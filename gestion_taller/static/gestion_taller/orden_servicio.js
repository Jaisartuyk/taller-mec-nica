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
  // Comentado temporalmente para evitar errores 404
  // if (vehiculoSelect && kilometrajeInput && serviciosSelect) {
  //   vehiculoSelect.addEventListener('change', sugerirServicios);
  //   kilometrajeInput.addEventListener('input', sugerirServicios);
  // }
  
  // Lógica para mostrar kilometraje actual del vehículo y validación
  if (vehiculoSelect && kilometrajeInput) {
    // Crear elemento para mostrar kilometraje actual
    let kilometrajeInfo = document.getElementById('kilometraje-info');
    if (!kilometrajeInfo) {
      kilometrajeInfo = document.createElement('div');
      kilometrajeInfo.id = 'kilometraje-info';
      kilometrajeInfo.className = 'form-text text-muted mt-1';
      kilometrajeInput.parentNode.appendChild(kilometrajeInfo);
    }
    
    // Crear elemento para advertencias
    let kilometrajeWarning = document.getElementById('kilometraje-warning');
    if (!kilometrajeWarning) {
      kilometrajeWarning = document.createElement('div');
      kilometrajeWarning.id = 'kilometraje-warning';
      kilometrajeWarning.className = 'alert alert-warning mt-2';
      kilometrajeWarning.style.display = 'none';
      kilometrajeInput.parentNode.appendChild(kilometrajeWarning);
    }
    
    let vehiculoKilometraje = 0;
    
    // Función para obtener y mostrar kilometraje del vehículo
    function actualizarKilometrajeInfo() {
      const vehiculoId = vehiculoSelect.value;
      console.log('Actualizando kilometraje para vehículo:', vehiculoId);
      
      if (vehiculoId) {
        console.log('Haciendo petición a:', `/api/vehiculo/kilometraje/?vehiculo_id=${vehiculoId}`);
        fetch(`/api/vehiculo/kilometraje/?vehiculo_id=${vehiculoId}`)
          .then(response => response.json())
          .then(data => {
            console.log('Respuesta del servidor:', data);
            if (data.success) {
              vehiculoKilometraje = data.kilometraje;
              console.log('Kilometraje del vehículo:', vehiculoKilometraje);
              kilometrajeInfo.innerHTML = `<i class="fas fa-tachometer-alt"></i> Kilometraje actual del vehículo: <strong>${data.kilometraje.toLocaleString()} km</strong>`;
              
              // Si el campo está vacío, sugerir el kilometraje actual con formato
              if (!kilometrajeInput.value) {
                kilometrajeInput.value = data.kilometraje.toLocaleString();
              }
              
              // Validar kilometraje actual
              validarKilometraje();
            } else {
              kilometrajeInfo.innerHTML = '<i class="fas fa-exclamation-triangle text-warning"></i> No se pudo obtener el kilometraje del vehículo';
            }
          })
          .catch(error => {
            console.error('Error al obtener kilometraje:', error);
            kilometrajeInfo.innerHTML = '<i class="fas fa-exclamation-triangle text-danger"></i> Error al obtener kilometraje del vehículo';
          });
      } else {
        kilometrajeInfo.innerHTML = '';
        kilometrajeWarning.style.display = 'none';
      }
    }
    
    // Función para validar kilometraje ingresado
    function validarKilometraje() {
      // Limpiar el valor ingresado: remover comas y espacios, manejar puntos como separadores de miles
      let valorLimpio = kilometrajeInput.value.trim();
      
      // Si contiene puntos como separadores de miles (ej: 50.000), convertir a formato sin separadores
      if (valorLimpio.includes('.') && !valorLimpio.includes(',')) {
        // Verificar si es separador de miles (más de 3 dígitos después del último punto)
        const partes = valorLimpio.split('.');
        if (partes.length > 1 && partes[partes.length - 1].length === 3) {
          valorLimpio = valorLimpio.replace(/\./g, '');
        }
      }
      
      // Remover comas (separadores de miles)
      valorLimpio = valorLimpio.replace(/,/g, '');
      
      const kilometrajeIngresado = parseFloat(valorLimpio) || 0;
      
      console.log('Validando kilometraje:', {
        valorIngresado: kilometrajeInput.value,
        valorLimpio: valorLimpio,
        kilometrajeIngresado: kilometrajeIngresado,
        vehiculoKilometraje: vehiculoKilometraje
      });
      
      if (vehiculoKilometraje > 0 && kilometrajeIngresado > 0) {
        if (kilometrajeIngresado < vehiculoKilometraje) {
          // Kilometraje menor al registrado - mostrar advertencia
          kilometrajeWarning.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i> 
            <strong>Advertencia:</strong> El kilometraje ingresado (${kilometrajeIngresado.toLocaleString()} km) 
            es menor al último registrado (${vehiculoKilometraje.toLocaleString()} km). 
            ¿Estás seguro de que es correcto?
          `;
          kilometrajeWarning.style.display = 'block';
          kilometrajeWarning.className = 'alert alert-warning mt-2';
          kilometrajeInput.classList.add('is-invalid');
        } else if (kilometrajeIngresado > vehiculoKilometraje) {
          // Kilometraje mayor al registrado - mostrar información
          kilometrajeWarning.innerHTML = `
            <i class="fas fa-info-circle"></i> 
            <strong>Información:</strong> El kilometraje ingresado (${kilometrajeIngresado.toLocaleString()} km) 
            es mayor al último registrado (${vehiculoKilometraje.toLocaleString()} km). 
            El kilometraje del vehículo se actualizará.
          `;
          kilometrajeWarning.style.display = 'block';
          kilometrajeWarning.className = 'alert alert-info mt-2';
          kilometrajeInput.classList.remove('is-invalid');
          kilometrajeInput.classList.add('is-valid');
        } else {
          // Kilometraje igual - sin advertencia
          kilometrajeWarning.style.display = 'none';
          kilometrajeInput.classList.remove('is-invalid', 'is-valid');
        }
      } else {
        kilometrajeWarning.style.display = 'none';
        kilometrajeInput.classList.remove('is-invalid', 'is-valid');
      }
    }
    
    // Event listeners
    vehiculoSelect.addEventListener('change', actualizarKilometrajeInfo);
    kilometrajeInput.addEventListener('input', validarKilometraje);
    kilometrajeInput.addEventListener('blur', validarKilometraje);
    
    // Inicializar si ya hay un vehículo seleccionado
    if (vehiculoSelect.value) {
      actualizarKilometrajeInfo();
    }
  }
});
