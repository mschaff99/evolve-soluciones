document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('formBusqueda');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    // Dejar que el GET haga el render lado servidor
    // Aquí podríamos hacer fetch a /api si se quiere SPA
  });

  // Verificar que Bootstrap esté disponible
  if (typeof bootstrap === 'undefined') {
    console.error('Bootstrap no está cargado');
  } else {
    console.log('Bootstrap cargado correctamente');
  }
});

/**
 * Abre el modal para consultar una nueva empresa
 */
function abrirModalConsultaNueva() {
  console.log('Intentando abrir modal...');

  // Verificar que Bootstrap esté disponible
  if (typeof bootstrap === 'undefined') {
    console.error('Bootstrap no está disponible');
    alert('Error: Bootstrap no está cargado. Por favor recargue la página.');
    return;
  }

  const modalElement = document.getElementById('modalConsultaNueva');
  if (!modalElement) {
    console.error('Modal de consulta nueva no encontrado');
    alert('Error: No se pudo encontrar el modal. Recargue la página.');
    return;
  }

  console.log('Modal element encontrado:', modalElement);

  // Limpiar formulario
  const inputRut = document.getElementById('consulta_rut');
  const inputClave = document.getElementById('consulta_clave');

  if (inputRut) inputRut.value = '';
  if (inputClave) {
    inputClave.value = '';
    inputClave.type = 'password';
  }

  const icon = document.getElementById('toggleIconConsulta');
  if (icon) {
    icon.classList.remove('fa-eye-slash');
    icon.classList.add('fa-eye');
  }

  // Eliminar cualquier backdrop anterior
  const existingBackdrops = document.querySelectorAll('.modal-backdrop');
  existingBackdrops.forEach(backdrop => backdrop.remove());

  // Destruir instancia previa si existe
  const existingModal = bootstrap.Modal.getInstance(modalElement);
  if (existingModal) {
    console.log('Destruyendo modal existente...');
    existingModal.dispose();
  }

  // Asegurar que el modal no tenga clases residuales
  modalElement.classList.remove('show');
  modalElement.style.display = 'none';
  document.body.classList.remove('modal-open');
  document.body.style.removeProperty('overflow');
  document.body.style.removeProperty('padding-right');

  // Crear y mostrar modal con un pequeño delay
  setTimeout(() => {
    try {
      console.log('Creando instancia del modal...');

      const modal = new bootstrap.Modal(modalElement, {
        backdrop: false,  // Sin backdrop
        keyboard: true,
        focus: true
      });

      console.log('Mostrando modal...');
      modal.show();
      console.log('Modal mostrado correctamente');

    } catch (error) {
      console.error('Error al mostrar modal:', error);
      alert('Error al abrir el modal: ' + error.message);
    }
  }, 100);
}

/**
 * Alterna la visibilidad de la contraseña en el modal de consulta
 */
function togglePasswordConsulta() {
  const input = document.getElementById('consulta_clave');
  const icon = document.getElementById('toggleIconConsulta');

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
 * Ejecuta la consulta de nueva empresa
 */
async function ejecutarConsultaNueva() {
  const rut = document.getElementById('consulta_rut').value.trim();
  const clave = document.getElementById('consulta_clave').value.trim();
  const baseDatos = window.baseDatos || 'stratex';

  // Validaciones básicas
  if (!rut) {
    alert('Por favor ingrese el RUT de la empresa');
    document.getElementById('consulta_rut').focus();
    return;
  }

  if (!clave) {
    alert('Por favor ingrese la clave SII');
    document.getElementById('consulta_clave').focus();
    return;
  }

  if (clave.length < 4) {
    alert('La clave debe tener al menos 4 caracteres');
    return;
  }

  try {
    // Cerrar modal de consulta
    const modalConsulta = document.getElementById('modalConsultaNueva');
    const modalConsultaInst = bootstrap.Modal.getInstance(modalConsulta);
    if (modalConsultaInst) modalConsultaInst.hide();

    // Abrir modal de progreso
    const modalPro = document.getElementById('modalProgresoConsulta');
    if (!modalPro) {
      alert('Modal de progreso no disponible');
      return;
    }

    const modalProInst = new bootstrap.Modal(modalPro);
    document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Guardando credencial...';
    document.getElementById('progresoConsultaDescripcion').innerText = 'Configurando acceso al SII...';

    const barra = document.getElementById('progresoConsultaBarra');
    if (barra) {
      barra.style.width = '10%';
      barra.innerText = '10%';
    }

    const detalle = document.getElementById('progresoConsultaDetalle');
    if (detalle) detalle.style.display = 'none';

    const btnCerrar = document.getElementById('btnCerrarProgresoConsulta');
    if (btnCerrar) btnCerrar.style.display = 'none';

    modalProInst.show();

    // Guardar credencial (esto dispara GCI en backend)
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
      document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-times-circle me-2 text-danger"></i>Error';
      document.getElementById('progresoConsultaDescripcion').innerText = 'ERROR: ' + (data.error || 'No se pudo guardar la credencial');
      if (btnCerrar) btnCerrar.style.display = 'inline-block';
      return;
    }

    // Iniciar polling para estado GCI
    const rutPol = rut;
    const base = baseDatos;
    let esperadoOp1 = true;
    let esperadoOp3 = true;
    const maxTimeoutMs = 5 * 60 * 1000; // 5 minutos
    const startTime = Date.now();
    let pollingTimer = null;

    async function checkStatus() {
      try {
        const resp = await fetch(`/${base}/empresas/api/gci_status/${rutPol}`);

        if (resp.status === 404) {
          clearTimeout(pollingTimer);
          console.warn('[ejecutarConsultaNueva] endpoint /api/gci_status no encontrado (404)');
          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-exclamation-triangle me-2 text-warning"></i>Servicio no disponible';
          document.getElementById('progresoConsultaDescripcion').innerText = 'El servidor no tiene disponible el endpoint de estado GCI. Reinicie la aplicación backend.';
          if (btnCerrar) btnCerrar.style.display = 'inline-block';
          return;
        }

        if (!resp.ok) {
          clearTimeout(pollingTimer);
          console.error('[ejecutarConsultaNueva] error en respuesta de gci_status:', resp.status);
          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-times-circle me-2 text-danger"></i>Error consultando estado';
          document.getElementById('progresoConsultaDescripcion').innerText = `Error ${resp.status} al consultar el estado. Revise el servidor.`;
          if (btnCerrar) btnCerrar.style.display = 'inline-block';
          return;
        }

        const st = await resp.json();

        // Fase 1: Cargando F29
        if (st.op1 && st.op1.exists && !st.op1.finished) {
          if (barra) {
            barra.style.width = '30%';
            barra.innerText = '30%';
          }
          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Cargando datos de F29...';
          document.getElementById('progresoConsultaDescripcion').innerText = 'Descargando información tributaria desde el SII...';
        }

        // Fase 2: F29 completado, iniciando DJ
        if (st.op1 && st.op1.finished && esperadoOp1) {
          esperadoOp1 = false;
          if (barra) {
            barra.style.width = '60%';
            barra.innerText = '60%';
          }
          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>F29 cargado. Iniciando DJ...';
          document.getElementById('progresoConsultaDescripcion').innerText = 'Ahora se están cargando los datos de Declaraciones Juradas. Espere por favor.';
        }

        // Fase 3: Cargando DJ
        if (st.op3 && st.op3.exists && !st.op3.finished && !esperadoOp1) {
          if (barra) {
            barra.style.width = '80%';
            barra.innerText = '80%';
          }
        }

        // Fase 4: Todo completado
        if (st.op3 && st.op3.finished && esperadoOp3 && !esperadoOp1) {
          clearTimeout(pollingTimer);
          esperadoOp3 = false;

          if (barra) {
            barra.style.width = '100%';
            barra.innerText = '100%';
          }

          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-check-circle me-2 text-success"></i>Procesos finalizados';
          document.getElementById('progresoConsultaDescripcion').innerText = 'F29 y DJ cargados correctamente. Redirigiendo a resultados...';

          if (detalle) detalle.style.display = 'none';
          if (btnCerrar) btnCerrar.style.display = 'inline-block';

          setTimeout(() => {
            modalProInst.hide();
            // Redirigir a la página de situación tributaria con el RUT consultado
            window.location.href = `/${base}/situacion-tributaria?rut=${encodeURIComponent(rutPol)}`;
          }, 1500);
          return;
        }

        // Mostrar logs si están disponibles
        if (st.op1 && st.op1.log && detalle) {
          detalle.style.display = 'block';
          document.getElementById('progresoConsultaLog').innerText = st.op1.log.slice(-2000);
        }

        // Timeout
        if (Date.now() - startTime > maxTimeoutMs) {
          clearTimeout(pollingTimer);
          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-clock me-2 text-warning"></i>Tiempo de espera excedido';
          document.getElementById('progresoConsultaDescripcion').innerText = 'El procesamiento está tomando demasiado tiempo. Revise los logs del servidor.';
          if (btnCerrar) btnCerrar.style.display = 'inline-block';
          return;
        }

      } catch (e) {
        clearTimeout(pollingTimer);
        console.error('Error consultando estado GCI:', e);
        document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-times-circle me-2 text-danger"></i>Error de conexión';
        document.getElementById('progresoConsultaDescripcion').innerText = 'Error al consultar el estado. Revise su conexión e intente nuevamente.';
        if (btnCerrar) btnCerrar.style.display = 'inline-block';
      }

      pollingTimer = setTimeout(checkStatus, 2000);
    }

    pollingTimer = setTimeout(checkStatus, 1000);

  } catch (error) {
    console.error('Error ejecutando consulta nueva:', error);
    alert('ERROR: Error de conexión. Por favor, intente nuevamente.');
  }
}

/**
 * Cierra el modal de progreso y recarga la página
 */
function cerrarModalYRecargar() {
  const modalPro = document.getElementById('modalProgresoConsulta');
  const modalProInst = bootstrap.Modal.getInstance(modalPro);
  if (modalProInst) {
    modalProInst.hide();
  }
  location.reload();
}

