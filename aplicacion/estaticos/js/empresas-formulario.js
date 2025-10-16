/**
 * Script para Gestión de Empresas - Formulario de Creación/Edición
 * ==================================================================
 *
 * Funcionalidades:
 * - Validación de formulario
 * - Formateo automático de RUT
 * - Envío asíncrono (AJAX)
 * - Manejo de respuestas y errores
 */

/**
 * Formatea el RUT mientras se escribe
 * @param {Event} e - Evento del input
 */
function formatearRUT(e) {
  let valor = e.target.value.replace(/[^0-9kK]/g, '');

  if (valor.length > 1) {
    const cuerpo = valor.slice(0, -1);
    const dv = valor.slice(-1);
    e.target.value = cuerpo + '-' + dv;
  } else {
    e.target.value = valor;
  }
}

/**
 * Valida que el RUT tenga el formato correcto
 * @param {string} rut - RUT a validar
 * @returns {boolean} True si el formato es válido
 */
function validarFormatoRUT(rut) {
  // Formato: XXXXXXXX-X o XX.XXX.XXX-X
  const patron = /^[0-9]+-[0-9kK]$/;
  return patron.test(rut);
}

/**
 * Maneja el envío del formulario
 * @param {Event} e - Evento del formulario
 */
async function manejarEnvioFormulario(e) {
  e.preventDefault();

  // Obtener datos del formulario
  const datos = {
    run_rut: document.getElementById('run_rut').value.trim(),
    empresa: document.getElementById('empresa').value.trim(),
    auditor: document.getElementById('auditor').value.trim(),
    grupo: document.getElementById('grupo').value.trim()
  };

  // Validar RUT
  if (!datos.run_rut) {
    alert('ERROR: El RUT es obligatorio');
    document.getElementById('run_rut').focus();
    return;
  }

  if (!validarFormatoRUT(datos.run_rut)) {
    alert('ERROR: El formato del RUT no es valido.\\n\\nFormato correcto: 12345678-9');
    document.getElementById('run_rut').focus();
    return;
  }

  // Validar nombre empresa
  if (!datos.empresa) {
    alert('ERROR: El nombre de la empresa es obligatorio');
    document.getElementById('empresa').focus();
    return;
  }

  if (datos.empresa.length < 3) {
    alert('ERROR: El nombre de la empresa debe tener al menos 3 caracteres');
    document.getElementById('empresa').focus();
    return;
  }

  // Determinar si es edición o creación
  const esEdicion = window.esEdicion || false;
  const baseDatos = window.baseDatos || 'stratex';

  const url = esEdicion
    ? `/${baseDatos}/empresas/api/actualizar/${datos.run_rut}`
    : `/${baseDatos}/empresas/api/crear`;

  // Mostrar indicador de carga
  const btnSubmit = e.target.querySelector('button[type="submit"]');
  const textoOriginal = btnSubmit.innerHTML;
  btnSubmit.disabled = true;
  btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.csrfToken
      },
      body: JSON.stringify(datos)
    });

    const data = await response.json();

    if (data.exito) {
      // Mostrar mensaje de éxito
      const mensaje = data.mensaje || (esEdicion
        ? 'OK: Empresa actualizada correctamente'
        : 'OK: Empresa creada correctamente');

      alert(mensaje);

      // Remover el listener de beforeunload para evitar advertencia
      window.removeEventListener('beforeunload', beforeUnloadHandler);

      // Redirigir al listado
      window.location.href = `/${baseDatos}/empresas`;
    } else {
      // Mostrar error
      alert('ERROR: ' + (data.error || 'No se pudo guardar la empresa'));

      // Restaurar botón
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = textoOriginal;
    }
  } catch (error) {
    console.error('Error guardando empresa:', error);
    alert('ERROR: Error de conexion. Por favor, intente nuevamente.');

    // Restaurar botón
    btnSubmit.disabled = false;
    btnSubmit.innerHTML = textoOriginal;
  }
}

/**
 * Confirma la cancelación si hay cambios sin guardar
 * @param {Event} e - Evento del enlace
 */
function confirmarCancelacion(e) {
  // Verificar si hay cambios en el formulario
  const formulario = document.getElementById('formEmpresa');
  const datosOriginales = window.datosOriginales || {};

  const datosActuales = {
    run_rut: document.getElementById('run_rut').value.trim(),
    empresa: document.getElementById('empresa').value.trim(),
    auditor: document.getElementById('auditor').value.trim(),
    grupo: document.getElementById('grupo').value.trim()
  };

  // Comparar si hay cambios
  const hayCambios = Object.keys(datosActuales).some(
    key => datosActuales[key] !== (datosOriginales[key] || '')
  );

  if (hayCambios) {
    if (!confirm('¿Está seguro de cancelar?\n\nLos cambios no guardados se perderán.')) {
      e.preventDefault();
    }
  }
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function () {
  console.log(' Script de empresas-formulario.js cargado correctamente');

  // Validar que tenemos el token CSRF
  if (!window.csrfToken) {
    console.warn('  Token CSRF no encontrado');
  }

  // Vincular evento submit del formulario
  const formulario = document.getElementById('formEmpresa');
  if (formulario) {
    formulario.addEventListener('submit', manejarEnvioFormulario);
  }

  // Formatear RUT mientras se escribe (solo si es nueva empresa)
  const inputRUT = document.getElementById('run_rut');
  if (inputRUT && !inputRUT.readOnly) {
    inputRUT.addEventListener('input', formatearRUT);
  }

  // Vincular confirmación de cancelación a los botones cancelar
  const botonesCancelar = document.querySelectorAll('a[href*="/empresas"]');
  botonesCancelar.forEach(boton => {
    // Solo si no es el botón "Volver al Listado" del header
    if (!boton.classList.contains('btn-action-secondary') || boton.closest('.empresas-header')) {
      boton.addEventListener('click', confirmarCancelacion);
    }
  });

  // Guardar datos originales para detectar cambios
  window.datosOriginales = {
    run_rut: document.getElementById('run_rut').value.trim(),
    empresa: document.getElementById('empresa').value.trim(),
    auditor: document.getElementById('auditor').value.trim(),
    grupo: document.getElementById('grupo').value.trim()
  };
});

// Advertencia al salir con cambios sin guardar
function beforeUnloadHandler(e) {
  const formulario = document.getElementById('formEmpresa');
  if (!formulario) return;

  const datosOriginales = window.datosOriginales || {};
  const datosActuales = {
    run_rut: document.getElementById('run_rut').value.trim(),
    empresa: document.getElementById('empresa').value.trim(),
    auditor: document.getElementById('auditor').value.trim(),
    grupo: document.getElementById('grupo').value.trim()
  };

  // Verificar si hay cambios
  const hayCambios = Object.keys(datosActuales).some(
    key => datosActuales[key] !== (datosOriginales[key] || '')
  );

  if (hayCambios) {
    e.preventDefault();
    e.returnValue = '¿Está seguro de salir? Los cambios no guardados se perderán.';
    return e.returnValue;
  }
}

window.addEventListener('beforeunload', beforeUnloadHandler);
