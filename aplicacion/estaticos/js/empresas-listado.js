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

  // Validaciones básicas
  if (!clave) {
    alert('Por favor ingrese la clave SII');
    document.getElementById('credencial_clave').focus();
    return;
  }
  if (clave.length < 4) {
    alert('La clave debe tener al menos 4 caracteres');
    return;
  }

  const enEdicion = typeof window.esEdicion !== 'undefined' ? !!window.esEdicion : true;

  try {
    // Si no estamos en edición, crear la empresa primero
    if (!enEdicion) {
      const run_rut = document.getElementById('run_rut') ? document.getElementById('run_rut').value : '';
      const empresaNombre = document.getElementById('empresa') ? document.getElementById('empresa').value : '';
      const auditor = document.getElementById('auditor') ? document.getElementById('auditor').value : '';
      const grupo = document.getElementById('grupo') ? document.getElementById('grupo').value : '';

      const payload = { run_rut: run_rut, empresa: empresaNombre, auditor: auditor, grupo: grupo };
      const crearResp = await fetch(`/${baseDatos}/empresas/api/crear`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': window.csrfToken
        },
        body: JSON.stringify(payload)
      });

      const crearJson = await crearResp.json();
      if (!crearResp.ok || !crearJson.exito) {
        alert('ERROR al crear la empresa: ' + (crearJson.error || crearJson.mensaje || crearResp.status));
        return;
      }
    }

    // Guardar credencial (dispara GCI en backend)
    const response = await fetch(`/${baseDatos}/empresas/api/credencial/${rut}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.csrfToken
      },
      body: JSON.stringify({ clave })
    });

    const data = await response.json();
    if (!data.exito) {
      alert('ERROR: ' + (data.error || 'No se pudo guardar la credencial'));
      return;
    }

    // Mostrar modal de progreso
    const modalCred = document.getElementById('modalCredencial');
    const modalCredInst = modalCred ? (bootstrap.Modal.getInstance(modalCred) || new bootstrap.Modal(modalCred)) : null;
    if (modalCredInst) modalCredInst.hide();

    const modalPro = document.getElementById('modalProgreso');
    if (!modalPro) {
      alert('OK: Credencial guardada. (Modal de progreso no disponible)');
      location.reload();
      return;
    }

    const modalProInst = bootstrap.Modal.getOrCreateInstance ? bootstrap.Modal.getOrCreateInstance(modalPro) : new bootstrap.Modal(modalPro);
    document.getElementById('progresoTitulo').innerText = 'Cargando datos de F29...';
    document.getElementById('progresoDescripcion').innerText = 'Por favor espere mientras se descargan los datos desde el SII (F29).';
    const barra = document.getElementById('progresoBarra'); if (barra) barra.style.width = '10%';
    const detalle = document.getElementById('progresoDetalle'); if (detalle) detalle.style.display = 'none';
    const btnCerrar = document.getElementById('btnCerrarProgreso'); if (btnCerrar) btnCerrar.style.display = 'none';
    modalProInst.show();

    // Polling para estado GCI
    const rutPol = rut;
    const base = baseDatos;
    let esperadoOp1 = true;
    let esperadoOp3 = true;
    let esperadoOp5 = true; // Proceso combinado (F29 + DJ)
    const maxTimeoutMs = 5 * 60 * 1000; // 5 minutos
    const startTime = Date.now();
    let pollingTimer = null;

    async function checkStatus() {
      try {
        const resp = await fetch(`/${base}/empresas/api/gci_status/${rutPol}`);
        if (resp.status === 404) {
          clearTimeout(pollingTimer);
          console.warn('[guardarCredencial] endpoint /api/gci_status no encontrado (404)');
          document.getElementById('progresoTitulo').innerText = 'Servicio no disponible';
          document.getElementById('progresoDescripcion').innerText = 'El servidor no tiene disponible el endpoint de estado GCI. Reinicie la aplicación backend.';
          const btnCerrar = document.getElementById('btnCerrarProgreso'); if (btnCerrar) btnCerrar.style.display = 'inline-block';
          return;
        }
        if (!resp.ok) {
          clearTimeout(pollingTimer);
          console.error('[guardarCredencial] error en respuesta de gci_status:', resp.status);
          document.getElementById('progresoTitulo').innerText = 'Error consultando estado';
          document.getElementById('progresoDescripcion').innerText = `Error ${resp.status} al consultar el estado. Revise el servidor.`;
          const btnCerrar2 = document.getElementById('btnCerrarProgreso'); if (btnCerrar2) btnCerrar2.style.display = 'inline-block';
          return;
        }

        const st = await resp.json();
        console.log('[POLLING] Estado actual:', st);

        // CASO 1: Proceso combinado (opción 5) - F29 + DJ en un solo paso
        if (st.op5 && st.op5.exists) {
          if (!st.op5.finished) {
            // Proceso combinado en ejecución
            if (barra) barra.style.width = '50%';
            document.getElementById('progresoTitulo').innerText = 'Cargando F29 y DJ...';
            document.getElementById('progresoDescripcion').innerText = 'Procesamiento combinado en curso. Por favor espere.';

            // Mostrar log si está disponible
            if (st.op5.log && detalle) {
              detalle.style.display = 'block';
              document.getElementById('progresoLog').innerText = st.op5.log.slice(-2000);
            }
          } else if (esperadoOp5) {
            // Proceso combinado finalizado
            clearTimeout(pollingTimer);
            esperadoOp5 = false;
            if (barra) barra.style.width = '100%';
            document.getElementById('progresoTitulo').innerText = 'Procesos finalizados';
            document.getElementById('progresoDescripcion').innerText = 'F29 y DJ cargados correctamente (proceso combinado).';
            if (detalle) detalle.style.display = 'none';
            const btnCerrar = document.getElementById('btnCerrarProgreso');
            if (btnCerrar) btnCerrar.style.display = 'inline-block';

            setTimeout(() => {
              modalProInst.hide();
              alert('Empresa cargada exitosamente');
              location.reload();
            }, 800);
            return;
          }
        }
        // CASO 2: Procesos separados (opciones 1 y 3)
        else {
          // Opción 1: F29
          if (st.op1 && st.op1.exists && !st.op1.finished) {
            if (barra) barra.style.width = '30%';
            document.getElementById('progresoTitulo').innerText = 'Cargando datos de F29...';

            // Mostrar log de op1
            if (st.op1.log && detalle) {
              detalle.style.display = 'block';
              document.getElementById('progresoLog').innerText = st.op1.log.slice(-2000);
            }
          }

          if (st.op1 && st.op1.finished && esperadoOp1) {
            esperadoOp1 = false;
            if (barra) barra.style.width = '60%';
            document.getElementById('progresoTitulo').innerText = 'F29 cargado. Iniciando DJ...';
            document.getElementById('progresoDescripcion').innerText = 'Ahora se están cargando los datos DJ. Espere por favor.';
          }

          // Opción 3: DJ
          if (st.op3 && st.op3.exists && !st.op3.finished && !esperadoOp1) {
            if (barra) barra.style.width = '80%';

            // Mostrar log de op3
            if (st.op3.log && detalle) {
              detalle.style.display = 'block';
              document.getElementById('progresoLog').innerText = st.op3.log.slice(-2000);
            }
          }

          if (st.op3 && st.op3.finished && esperadoOp3 && !esperadoOp1) {
            clearTimeout(pollingTimer);
            esperadoOp3 = false;
            if (barra) barra.style.width = '100%';
            document.getElementById('progresoTitulo').innerText = 'Procesos finalizados';
            document.getElementById('progresoDescripcion').innerText = 'F29 y DJ cargados correctamente.';
            if (detalle) detalle.style.display = 'none';
            const btnCerrar3 = document.getElementById('btnCerrarProgreso');
            if (btnCerrar3) btnCerrar3.style.display = 'inline-block';

            setTimeout(() => {
              modalProInst.hide();
              alert('Empresa cargada exitosamente');
              location.reload();
            }, 800);
            return;
          }
        }

        // Timeout general
        if (Date.now() - startTime > maxTimeoutMs) {
          clearTimeout(pollingTimer);
          document.getElementById('progresoTitulo').innerText = 'Tiempo de espera excedido';
          document.getElementById('progresoDescripcion').innerText = 'El procesamiento está tomando demasiado tiempo. Revise los logs del servidor.';
          const btnCerrar4 = document.getElementById('btnCerrarProgreso');
          if (btnCerrar4) btnCerrar4.style.display = 'inline-block';
          return;
        }

      } catch (e) {
        clearTimeout(pollingTimer);
        console.error('Error consultando estado GCI:', e);
        document.getElementById('progresoTitulo').innerText = 'Error de conexión';
        document.getElementById('progresoDescripcion').innerText = 'No se pudo consultar el estado del proceso. Verifique su conexión.';
        const btnCerrar5 = document.getElementById('btnCerrarProgreso');
        if (btnCerrar5) btnCerrar5.style.display = 'inline-block';
      }

      pollingTimer = setTimeout(checkStatus, 2000);
    }

    pollingTimer = setTimeout(checkStatus, 1000);

  } catch (error) {
    console.error('Error guardando credencial:', error);
    alert('ERROR: Error de conexion. Por favor, intente nuevamente.');
  }
}

/**
 * Elimina la credencial SII de una empresa
 * @param {string} rut - RUT de la empresa
 */
async function eliminarCredencial(rut) {
  if (!confirm('¿Está seguro de eliminar la credencial SII de esta empresa?\\n\\nEsta acción no se puede deshacer.')) {
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
      alert('OK: Credencial eliminada exitosamente');

      // Recargar la página
      location.reload();
    } else {
      alert('ERROR: ' + (data.error || 'No se pudo eliminar la credencial'));
    }
  } catch (error) {
    console.error('Error eliminando credencial:', error);
    alert('ERROR: Error de conexion. Por favor, intente nuevamente.');
  }
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function () {
  console.log(' Script de empresas-listado.js cargado correctamente');

  // Validar que tenemos el token CSRF
  if (!window.csrfToken) {
    console.warn('  Token CSRF no encontrado');
  }
});
