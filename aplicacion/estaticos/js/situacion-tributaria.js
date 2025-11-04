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

  // Leer base de datos desde variable global (configurada en el template)
  const baseDatos = window.baseDatos;

  if (!baseDatos) {
    console.error('ERROR: window.baseDatos no está definida');
    alert('ERROR: No se pudo determinar la base de datos. Recargue la página.');
    return;
  }

  console.log(`[ejecutarConsultaNueva] Base de datos: ${baseDatos}`);

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
    const maxTimeoutMs = 10 * 60 * 1000; // 10 minutos (aumentado para procesos lentos)
    const startTime = Date.now();
    let pollingTimer = null;
    let pollingActivo = true; // Flag para controlar el polling

    async function checkStatus() {
      // Si el polling ya no está activo, salir
      if (!pollingActivo) {
        if (pollingTimer) clearTimeout(pollingTimer);
        return;
      }

      try {
        const resp = await fetch(`/${base}/empresas/api/gci_status/${rutPol}`);

        if (resp.status === 404) {
          pollingActivo = false;
          if (pollingTimer) clearTimeout(pollingTimer);
          console.warn('[ejecutarConsultaNueva] endpoint /api/gci_status no encontrado (404)');
          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-exclamation-triangle me-2 text-warning"></i>Servicio no disponible';
          document.getElementById('progresoConsultaDescripcion').innerText = 'El servidor no tiene disponible el endpoint de estado GCI. Reinicie la aplicación backend.';
          if (btnCerrar) btnCerrar.style.display = 'inline-block';
          return;
        }

        if (!resp.ok) {
          pollingActivo = false;
          if (pollingTimer) clearTimeout(pollingTimer);
          console.error('[ejecutarConsultaNueva] error en respuesta de gci_status:', resp.status);
          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-times-circle me-2 text-danger"></i>Error consultando estado';
          document.getElementById('progresoConsultaDescripcion').innerText = `Error ${resp.status} al consultar el estado. Revise el servidor.`;
          if (btnCerrar) btnCerrar.style.display = 'inline-block';
          return;
        }

        const st = await resp.json();

        // Log para debugging
        if (st.logs_dir) {
          console.log('[GCI Status] Directorio de logs:', st.logs_dir);
        }
        console.log('[GCI Status] op1:', st.op1?.exists ? 'exists' : 'no existe', st.op1?.finished ? 'finished' : 'en proceso');
        console.log('[GCI Status] op3:', st.op3?.exists ? 'exists' : 'no existe', st.op3?.finished ? 'finished' : 'en proceso');
        console.log('[GCI Status] op5:', st.op5?.exists ? 'exists' : 'no existe', st.op5?.finished ? 'finished' : 'en proceso');

        // Debug: Mostrar el estado recibido
        console.log('[GCI Status]', st);

        // Verificar si hay proceso combinado (opción 5)
        const op5Terminado = st.op5 && st.op5.finished;
        const op5Existe = st.op5 && st.op5.exists;

        // Verificar procesos individuales (opción 1 y 3)
        const op1Terminado = st.op1 && st.op1.finished;
        const op3Terminado = st.op3 && st.op3.finished;
        const op1Existe = st.op1 && st.op1.exists;
        const op3Existe = st.op3 && st.op3.exists;

        // Si el proceso combinado (opción 5) terminó, finalizar inmediatamente
        if (op5Terminado) {
          pollingActivo = false;
          if (pollingTimer) clearTimeout(pollingTimer);

          if (barra) {
            barra.style.width = '100%';
            barra.innerText = '100%';
          }

          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-check-circle me-2 text-success"></i>Proceso combinado finalizado';
          document.getElementById('progresoConsultaDescripcion').innerText = 'F29 y DJ cargados correctamente. Redirigiendo a resultados...';

          if (detalle) detalle.style.display = 'none';
          if (btnCerrar) btnCerrar.style.display = 'inline-block';

          setTimeout(() => {
            modalProInst.hide();
            window.location.href = `/${base}/situacion-tributaria?rut=${encodeURIComponent(rutPol)}`;
          }, 1500);
          return;
        }

        // Si el proceso combinado está corriendo, mostrar progreso
        if (op5Existe && !op5Terminado) {
          if (barra) {
            barra.style.width = '50%';
            barra.innerText = '50%';
          }
          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando F29 y DJ...';
          document.getElementById('progresoConsultaDescripcion').innerText = 'Cargando información tributaria desde el SII (proceso combinado). Esto puede tomar varios minutos...';
        }

        // Si ambos procesos individuales terminaron, finalizar
        if (op1Terminado && op3Terminado) {
          pollingActivo = false;
          if (pollingTimer) clearTimeout(pollingTimer);

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
            window.location.href = `/${base}/situacion-tributaria?rut=${encodeURIComponent(rutPol)}`;
          }, 1500);
          return;
        }

        // Fase 1: Cargando F29
        if (op1Existe && !op1Terminado) {
          if (barra) {
            barra.style.width = '30%';
            barra.innerText = '30%';
          }
          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Cargando datos de F29...';
          document.getElementById('progresoConsultaDescripcion').innerText = 'Descargando información tributaria desde el SII...';
        }

        // Fase 2: F29 completado, iniciando DJ
        if (op1Terminado && esperadoOp1) {
          esperadoOp1 = false;
          if (barra) {
            barra.style.width = '60%';
            barra.innerText = '60%';
          }
          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>F29 cargado. Iniciando DJ...';
          document.getElementById('progresoConsultaDescripcion').innerText = 'Ahora se están cargando los datos de Declaraciones Juradas. Espere por favor.';
        }

        // Fase 3: Cargando DJ
        if (op3Existe && !op3Terminado) {
          if (barra) {
            barra.style.width = '80%';
            barra.innerText = '80%';
          }
          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Cargando Declaraciones Juradas...';
          document.getElementById('progresoConsultaDescripcion').innerText = 'Procesando información de DJ desde el SII...';
        }

        // Mostrar logs si están disponibles (priorizar op5, luego op1)
        let logToShow = '';
        if (st.op5 && st.op5.log) {
          logToShow = st.op5.log;
        } else if (st.op1 && st.op1.log) {
          logToShow = st.op1.log;
        }

        if (logToShow && detalle) {
          detalle.style.display = 'block';
          const logElement = document.getElementById('progresoConsultaLog');
          if (logElement) {
            logElement.innerText = logToShow.slice(-2000);
          }
        }

        // Verificar si no hay procesos activos (incluir op5)
        const hayProcesos = op1Existe || op3Existe || op5Existe;
        const tiempoTranscurrido = Date.now() - startTime;

        if (!hayProcesos) {
          // Si no hay procesos pero aún no ha pasado mucho tiempo, mostrar "Iniciando..."
          if (tiempoTranscurrido < 30000) { // Primeros 30 segundos
            document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Iniciando procesos...';
            document.getElementById('progresoConsultaDescripcion').innerText = 'Preparando la consulta al SII. Esto puede tomar unos segundos...';
            if (barra) {
              barra.style.width = '15%';
              barra.innerText = '15%';
            }
          }
          // Si ya pasaron 2 minutos sin procesos, mostrar advertencia
          else if (tiempoTranscurrido > 120000) { // Después de 2 minutos
            pollingActivo = false;
            if (pollingTimer) clearTimeout(pollingTimer);
            console.warn('[GCI] No se detectaron procesos después de 2 minutos');
            document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-exclamation-triangle me-2 text-warning"></i>Sin procesos detectados';
            document.getElementById('progresoConsultaDescripcion').innerText = 'No se detectaron procesos activos después de 2 minutos. Es posible que haya un problema en el servidor. Revise los logs o intente nuevamente.';
            if (btnCerrar) btnCerrar.style.display = 'inline-block';
            return;
          }
          // Entre 30 segundos y 2 minutos, seguir esperando pero informar
          else {
            document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-hourglass-half me-2 text-info"></i>Esperando inicio de procesos...';
            document.getElementById('progresoConsultaDescripcion').innerText = 'Los procesos están tomando más tiempo del esperado en iniciarse. Esperando...';
            if (barra) {
              barra.style.width = '20%';
              barra.innerText = '20%';
            }
          }
        }

        // Timeout
        if (Date.now() - startTime > maxTimeoutMs) {
          pollingActivo = false;
          if (pollingTimer) clearTimeout(pollingTimer);
          document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-clock me-2 text-warning"></i>Tiempo de espera excedido';
          document.getElementById('progresoConsultaDescripcion').innerText = 'El procesamiento está tomando demasiado tiempo. Revise los logs del servidor.';
          if (btnCerrar) btnCerrar.style.display = 'inline-block';
          return;
        }

      } catch (e) {
        pollingActivo = false;
        if (pollingTimer) clearTimeout(pollingTimer);
        console.error('Error consultando estado GCI:', e);
        document.getElementById('progresoConsultaTitulo').innerHTML = '<i class="fas fa-times-circle me-2 text-danger"></i>Error de conexión';
        document.getElementById('progresoConsultaDescripcion').innerText = 'Error al consultar el estado. Revise su conexión e intente nuevamente.';
        if (btnCerrar) btnCerrar.style.display = 'inline-block';
        return;
      }

      // Continuar polling solo si sigue activo
      if (pollingActivo) {
        pollingTimer = setTimeout(checkStatus, 3000); // 3 segundos entre checks (más tiempo para procesos pesados)
      }
    }

    // Iniciar polling
    pollingTimer = setTimeout(checkStatus, 2000); // Primer check después de 2 segundos

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

