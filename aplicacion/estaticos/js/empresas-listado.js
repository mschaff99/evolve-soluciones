/**
 * Script para Gestión de Empresas - Vista de Listado
 * ====================================================
 *
 * Funcionalidades:
 * - Editar empresa
 * - Gestionar credenciales SII (crear, actualizar, eliminar)
 * - Toggle de visibilidad de contraseña
 * - Validaciones de formulario
 */

/**
 * Redirige a la página de edición de empresa
 * @param {string} rut - RUT de la empresa a editar
 */
function editarEmpresa(rut) {
  const baseDatos = window.baseDatos || 'stratex';
  window.location.href = `/${baseDatos}/empresas/editar/${rut}`;
}

/**
 * Abre el modal de gestión de credencial SII
 * @param {string} rut - RUT de la empresa
 * @param {string} empresa - Nombre de la empresa
 * @param {boolean} tieneCredencial - Indica si ya tiene credencial configurada
 */
function gestionarCredencial(rut, empresa, tieneCredencial) {
  // Obtener el modal directamente
  const modalElement = document.getElementById('modalCredencial');
  if (!modalElement) {
    console.error('Modal no encontrado');
    return;
  }

  // Inicializar modal si no existe
  let modalCredencial = bootstrap.Modal.getInstance(modalElement);
  if (!modalCredencial) {
    modalCredencial = new bootstrap.Modal(modalElement);
  }

  // Configurar datos del formulario
  document.getElementById('credencial_rut').value = rut;
  document.getElementById('credencial_empresa').value = empresa;
  document.getElementById('credencial_clave').value = '';

  // Resetear el tipo de input a password
  const inputClave = document.getElementById('credencial_clave');
  inputClave.type = 'password';

  const icon = document.getElementById('toggleIcon');
  if (icon) {
    icon.classList.remove('fa-eye-slash');
    icon.classList.add('fa-eye');
  }

  // Mostrar/ocultar botón eliminar según si tiene credencial
  const btnEliminar = document.getElementById('btnEliminarCredencial');
  if (tieneCredencial) {
    btnEliminar.style.display = 'inline-block';
    btnEliminar.onclick = () => eliminarCredencial(rut);
  } else {
    btnEliminar.style.display = 'none';
  }

  modalCredencial.show();
}

/**
 * Alterna la visibilidad de la contraseña en el modal
 */
function togglePassword() {
  const input = document.getElementById('credencial_clave');
  const icon = document.getElementById('toggleIcon');

  if (input.type === 'password') {
    input.type = 'text';
    icon.classList.remove('fa-eye');
    icon.classList.add('fa-eye-slash');
  } else {
    input.type = 'password';
    icon.classList.remove('fa-eye-slash');
    icon.classList.add('fa-eye');
  }
}

/**
 * Guarda la credencial SII (crear o actualizar)
 */
async function guardarCredencial() {
  const rut = document.getElementById('credencial_rut').value;
  const clave = document.getElementById('credencial_clave').value.trim();
  const baseDatos = window.baseDatos || 'stratex';

  // Validar que la clave no esté vacía
  if (!clave) {
    alert('Por favor ingrese la clave SII');
    document.getElementById('credencial_clave').focus();
    return;
  }

  // Validar longitud mínima (opcional pero recomendado)
  if (clave.length < 4) {
    alert('La clave debe tener al menos 4 caracteres');
    return;
  }

  try {
    const response = await fetch(`/${baseDatos}/empresas/api/credencial/${rut}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.csrfToken
      },
      body: JSON.stringify({ clave })
    });

    const data = await response.json();

    if (data.exito) {
      // Cerrar el modal
      const modalElement = document.getElementById('modalCredencial');
      const modalInstance = bootstrap.Modal.getInstance(modalElement);
      if (modalInstance) {
        modalInstance.hide();
      }

      // Mostrar mensaje de éxito
      alert('contraseña ingresada');

      // Recargar la página para mostrar los cambios
      location.reload();
    } else {
      alert('❌ Error: ' + (data.error || 'No se pudo guardar la credencial'));
    }
  } catch (error) {
    console.error('Error guardando credencial:', error);
    alert('❌ Error de conexión. Por favor, intente nuevamente.');
  }
}

/**
 * Elimina la credencial SII de una empresa
 * @param {string} rut - RUT de la empresa
 */
async function eliminarCredencial(rut) {
  if (!confirm('¿Está seguro de eliminar la credencial SII de esta empresa?\n\nEsta acción no se puede deshacer.')) {
    return;
  }

  const baseDatos = window.baseDatos || 'stratex';

  try {
    const response = await fetch(`/${baseDatos}/empresas/api/credencial/${rut}`, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': window.csrfToken
      }
    });

    const data = await response.json();

    if (data.exito) {
      // Cerrar el modal
      const modalElement = document.getElementById('modalCredencial');
      const modalInstance = bootstrap.Modal.getInstance(modalElement);
      if (modalInstance) {
        modalInstance.hide();
      }

      // Mostrar mensaje de éxito
      alert(' Credencial eliminada exitosamente');

      // Recargar la página
      location.reload();
    } else {
      alert('❌ Error: ' + (data.error || 'No se pudo eliminar la credencial'));
    }
  } catch (error) {
    console.error('Error eliminando credencial:', error);
    alert('❌ Error de conexión. Por favor, intente nuevamente.');
  }
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function () {
  console.log(' Script de empresas-listado.js cargado correctamente');

  // Validar que tenemos el token CSRF
  if (!window.csrfToken) {
    console.warn('⚠️  Token CSRF no encontrado');
  }
});
