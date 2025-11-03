/**
 * JavaScript para funcionalidades de DJ Integral
 * Maneja expansión de tablas y filtros dinámicos
 */

console.log('Cargando dj-integral.js...');

// Variables globales
let empresasExpandidas = new Set();

/**
 * Alterna la expansión de una empresa (mostrar/ocultar DJ)
 * @param {HTMLElement} boton - El botón que se clickeó
 */
function alternarEmpresa(boton) {
  try {
    const fila = boton.closest('tr');
    if (!fila) {
      console.error('No se pudo encontrar la fila padre del botón');
      return;
    }

    const rut = fila.dataset.rut || boton.dataset.empresa;
    if (!rut) {
      console.error('No se pudo encontrar el RUT de la empresa');
      return;
    }

    // Buscar todas las filas de detalle de DJ de esta empresa
    const filasDetalle = document.querySelectorAll(`tr.fila-dj-detalle[data-empresa="${rut}"]`);

    if (!filasDetalle || filasDetalle.length === 0) {
      console.error(`No se encontraron filas de detalle para RUT: ${rut}`);
      return;
    }

    if (empresasExpandidas.has(rut)) {
      // Colapsar todas: ocultar con display none y remover clase visible
      filasDetalle.forEach(filaDetalle => {
        filaDetalle.classList.remove('visible');
        filaDetalle.style.display = 'none'; // Forzar display none inline
      });
      empresasExpandidas.delete(rut);

      // Cambiar ícono del botón y aria
      const icono = boton.querySelector('i');
      if (icono) {
        icono.className = 'fas fa-plus';
      }
      boton.classList.remove('expandido');
      boton.setAttribute('aria-expanded', 'false');
      boton.title = 'Expandir detalles';

      console.log(`Empresa ${rut} colapsada`);
    } else {
      // Expandir todas: mostrar con display table-row y agregar clase visible
      filasDetalle.forEach(filaDetalle => {
        filaDetalle.classList.add('visible');
        filaDetalle.style.display = 'table-row'; // Forzar display table-row inline
      });
      empresasExpandidas.add(rut);

      // Cambiar ícono del botón y aria
      const icono = boton.querySelector('i');
      if (icono) {
        icono.className = 'fas fa-minus';
      }
      boton.classList.add('expandido');
      boton.setAttribute('aria-expanded', 'true');
      boton.title = 'Contraer detalles';

      console.log(`Empresa ${rut} expandida`);
    }
  } catch (error) {
    console.error('Error en alternarEmpresa:', error);
  }
}

/**
 * Expandir todas las empresas
 */
function expandirTodas() {
  try {
    const botones = document.querySelectorAll('.boton-expandir-empresa');

    botones.forEach(boton => {
      const rut = boton.dataset.empresa;
      // Si no está expandida, expandir mediante alternarEmpresa
      if (!empresasExpandidas.has(rut)) {
        alternarEmpresa(boton);
      } else {
        // Asegurar que el botón y el aria-expanded estén sincronizados
        boton.classList.add('expandido');
        boton.setAttribute('aria-expanded', 'true');
        boton.title = 'Contraer detalles';
        const icono = boton.querySelector('i');
        if (icono) icono.className = 'fas fa-minus';

        // Asegurar que las filas de detalle estén visibles
        const filasDetalle = document.querySelectorAll(`tr.fila-dj-detalle[data-empresa="${rut}"]`);
        filasDetalle.forEach(fd => {
          fd.classList.add('visible');
          fd.style.display = 'table-row';
        });
      }
    });

    console.log('Todas las empresas expandidas');
  } catch (error) {
    console.error('Error expandiendo todas:', error);
  }
}

/**
 * Contraer todas las empresas
 */
function contraerTodas() {
  try {
    const botones = document.querySelectorAll('.boton-expandir-empresa');

    botones.forEach(boton => {
      const rut = boton.dataset.empresa;
      if (empresasExpandidas.has(rut)) {
        alternarEmpresa(boton);
      } else {
        // Asegurar estado visual de botón
        boton.classList.remove('expandido');
        boton.setAttribute('aria-expanded', 'false');
        boton.title = 'Expandir detalles';
        const icono = boton.querySelector('i');
        if (icono) icono.className = 'fas fa-plus';

        // Asegurar que las filas de detalle estén ocultas
        const filasDetalle = document.querySelectorAll(`tr.fila-dj-detalle[data-empresa="${rut}"]`);
        filasDetalle.forEach(fd => {
          fd.classList.remove('visible');
          fd.style.display = 'none';
        });
      }
    });

    console.log('Todas las empresas contraídas');
  } catch (error) {
    console.error('Error contrayendo todas:', error);
  }
}

/**
 * Helper para obtener valor seguro de input/select
 */
function getVal(id) {
  const el = document.getElementById(id);
  return el ? el.value.toLowerCase().trim() : '';
}

/**
 * Debounce para optimizar el rendimiento de los filtros
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Filtra las empresas según los criterios seleccionados
 */
function filtrarEmpresas() {
  try {
    const usuarioFiltro = getVal('usuarioSelect');
    const grupoFiltro = getVal('grupoSelect');
    const empresaFiltro = getVal('empresaInput');
    const estadoFiltro = getVal('estadoSelect');

    const filasEmpresas = document.querySelectorAll('tr.fila-empresa');
    let empresasVisibles = 0;

    filasEmpresas.forEach(fila => {
      const usuario = (fila.dataset.usuario || '').toLowerCase();
      const grupo = (fila.dataset.grupo || '').toLowerCase();
      const nombreEmpresa = (fila.querySelector('.nombre-empresa .fw-semibold')?.textContent || '').toLowerCase();
      const rut = fila.dataset.rut;

      let mostrarFila = true;

      // Filtro de usuario
      if (usuarioFiltro && usuario !== usuarioFiltro) {
        mostrarFila = false;
      }

      // Filtro de grupo
      if (grupoFiltro && grupo !== grupoFiltro) {
        mostrarFila = false;
      }

      // Filtro de empresa
      if (empresaFiltro && !nombreEmpresa.includes(empresaFiltro)) {
        mostrarFila = false;
      }

      // Filtro de estado (buscar en la fila de detalle)
      if (estadoFiltro) {
        const filaDetalle = document.querySelector(`tr.fila-dj-detalle[data-empresa="${rut}"]`);
        if (filaDetalle) {
          const badges = filaDetalle.querySelectorAll('.badge');
          let tieneEstado = false;

          badges.forEach(badge => {
            const textoEstado = badge.textContent.toLowerCase().trim();
            if (textoEstado.includes(estadoFiltro)) {
              tieneEstado = true;
            }
          });

          if (!tieneEstado) {
            mostrarFila = false;
          }
        } else {
          mostrarFila = false;
        }
      }

      // Mostrar/ocultar fila principal
      if (mostrarFila) {
        fila.style.display = '';
        empresasVisibles++;
      } else {
        fila.style.display = 'none';

        // También ocultar la(s) fila(s) de detalle si estaban expandida(s)
        const filasDetalleLocal = document.querySelectorAll(`tr.fila-dj-detalle[data-empresa="${rut}"]`);
        filasDetalleLocal.forEach(fd => {
          fd.classList.remove('visible');
          fd.style.display = 'none'; // Forzar display none inline
        });
        // Asegurar que el estado interno refleja que la empresa no está expandida
        if (empresasExpandidas.has(rut)) empresasExpandidas.delete(rut);
      }
    });

    // Actualizar contador de resultados
    const contador = document.querySelector('.results-count');
    if (contador) {
      contador.innerHTML = `<i class="fas fa-building me-2"></i>${empresasVisibles} empresas encontradas`;
    }

    console.log(`Filtrado completado: ${empresasVisibles} empresas visibles`);
  } catch (error) {
    console.error('Error en filtrarEmpresas:', error);
  }
}

/**
 * Limpia todos los filtros
 */
function clearAllFilters() {
  try {
    // Limpiar selects
    const usuarioSelect = document.getElementById('usuarioSelect');
    const grupoSelect = document.getElementById('grupoSelect');
    const estadoSelect = document.getElementById('estadoSelect');

    if (usuarioSelect) usuarioSelect.value = '';
    if (grupoSelect) grupoSelect.value = '';
    if (estadoSelect) estadoSelect.value = '';

    // Limpiar input de empresa
    const empresaInput = document.getElementById('empresaInput');
    if (empresaInput) empresaInput.value = '';

    // Aplicar filtros (mostrar todas)
    filtrarEmpresas();

    console.log('Filtros limpiados');
  } catch (error) {
    console.error('Error limpiando filtros:', error);
  }
}


/**
 * Exportar observaciones DJ a Excel
 */
function exportarObservacionesDJExcel() {
  console.log('Iniciando exportación de observaciones DJ a Excel...');

  try {
    const boton = event ? (event.target.closest ? event.target.closest('button') : null) : null;
    const textoOriginal = boton ? boton.innerHTML : '';
    if (boton) {
      boton.disabled = true;
      boton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Exportando...';
    }

    // Obtener base de datos desde la URL
    const pathParts = window.location.pathname.split('/');
    const baseDatos = pathParts[1] || '';
    const url = `/${baseDatos}/api/exportar-dj-observaciones-excel`;
    console.log('🔗 URL de exportación DJ:', url);

    // Intentar con base de datos en la URL; si no existe, haremos un intento sin base
    // Añadimos `credentials: 'same-origin'` para enviar cookies de sesión cuando corresponda
    const fetchWithUrl = (u) => fetch(u, {
      method: 'GET',
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });

    fetchWithUrl(url)
      .then(response => {
        // Detectar redirecciones al login (cuando el servidor responde con redirect a /auth/iniciar-sesion)
        if (response.redirected || (response.url && response.url.includes('/auth/iniciar-sesion'))) {
          throw new Error('Sesión expirada o no autenticado. Por favor inicia sesión nuevamente.');
        }

        const contentType = response.headers.get('content-type') || '';
        if (!response.ok) {
          // Intentar parsear JSON si viene como tal
          if (contentType.includes('application/json')) {
            return response.json().then(data => {
              throw new Error(data.error || JSON.stringify(data));
            });
          }
          // Si viene HTML o texto, leer como texto y mostrar
          return response.text().then(text => {
            // Si recibimos HTML del login, avisar de sesión expirada
            if (text && text.toLowerCase().includes('redirecting') || text.toLowerCase().includes('iniciar-sesion')) {
              throw new Error('Sesión expirada o no autenticado. Por favor inicia sesión.');
            }
            throw new Error(text || 'Error al exportar DJ');
          });
        }

        // Si viene un JSON (posible error) pero response.ok, manejarlo
        if (contentType.includes('application/json')) {
          return response.json().then(data => {
            // Si hay campo error en JSON, lanzar
            if (data && data.error) throw new Error(data.error);
            throw new Error('Respuesta inesperada del servidor');
          });
        }

        // Si viene un blob (archivo), devolver el blob
        return response.blob();
      })
      .catch(err => {
        // Si fue 404 por URL con base, intentar sin base (ruta raíz)
        console.warn('Primera petición de exportación falló, intentando sin base en la URL...', err.message);
        const urlSinBase = `/api/exportar-dj-observaciones-excel`;
        return fetchWithUrl(urlSinBase).then(response => {
          const contentType = response.headers.get('content-type') || '';
          if (!response.ok) {
            if (contentType.includes('application/json')) {
              return response.json().then(data => { throw new Error(data.error || JSON.stringify(data)); });
            }
            return response.text().then(text => { throw new Error(text || 'Error al exportar DJ (sin base)'); });
          }
          if (contentType.includes('application/json')) {
            return response.json().then(data => { if (data && data.error) throw new Error(data.error); throw new Error('Respuesta inesperada del servidor'); });
          }
          return response.blob();
        });
      })
      .then(blob => {
        // Si 'blob' es un objeto JSON (error) habrá lanzado antes; asumimos blob
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        const fecha = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '_');
        a.download = `Observaciones_DJ_${fecha}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        alert('Excel de observaciones DJ descargado exitosamente');
      })
      .catch(error => {
        console.error('Error exportando observaciones DJ:', error);
        alert('Error al exportar DJ: ' + error.message);
      })
      .finally(() => {
        if (boton) {
          boton.disabled = false;
          boton.innerHTML = textoOriginal;
        }
      });

  } catch (error) {
    console.error('Error en exportarObservacionesDJExcel:', error);
    alert('Error al iniciar exportación DJ');
  }
}

// Exponer globalmente para uso en onclick
window.exportarObservacionesDJExcel = exportarObservacionesDJExcel;

/**
 * Inicialización cuando el DOM está listo
 */
document.addEventListener('DOMContentLoaded', function () {
  console.log('DJ Integral - DOM cargado, inicializando...');

  // Aplicar debounce a filtros
  const filtrarDebounced = debounce(filtrarEmpresas, 300);

  // Event listeners para filtros
  const usuarioSelect = document.getElementById('usuarioSelect');
  const grupoSelect = document.getElementById('grupoSelect');
  const empresaInput = document.getElementById('empresaInput');
  const estadoSelect = document.getElementById('estadoSelect');

  if (usuarioSelect) {
    usuarioSelect.addEventListener('change', filtrarEmpresas);
  }

  if (grupoSelect) {
    grupoSelect.addEventListener('change', filtrarEmpresas);
  }

  if (empresaInput) {
    empresaInput.addEventListener('input', filtrarDebounced);
  }

  if (estadoSelect) {
    estadoSelect.addEventListener('change', filtrarEmpresas);
  }

  // Inicializar tooltips de Bootstrap si existen
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  console.log('DJ Integral - Inicialización completada');
});

/**
 * Log de estado al cargar
 */
console.log('dj-integral.js cargado correctamente');

/**
 * Abre el modal de observaciones DJ y solicita las observaciones via API
 * @param {string} rut
 * @param {number} dj_numero
 * @param {number|string} periodo
 */
function abrirModalObservacionesDJ(rut, dj_numero, periodo) {
  try {
    console.log('abrirModalObservacionesDJ called', rut, dj_numero, periodo);
    const modal = document.getElementById('modalObservacionesDJ');
    const loading = document.getElementById('modalDJLoading');
    const content = document.getElementById('modalDJContent');
    const body = document.getElementById('observacionesDJBody');
    const titleRut = document.getElementById('modalDJRut');
    const titleNum = document.getElementById('modalDJNumero');
    const titlePer = document.getElementById('modalDJPeriodo');
    const totalEl = document.getElementById('modalDJTotal');

    if (!modal) return console.error('Modal DJ no encontrado');

    // Mostrar modal y loading (forzar visibilidad)
    modal.style.display = 'flex';
    modal.classList.add('modal-visible');
    // Evitar scroll de fondo
    try { document.body.style.overflow = 'hidden'; } catch (_) { }
    if (loading) loading.style.display = 'block';
    if (content) content.style.display = 'none';

    // Limpieza previa
    if (body) body.innerHTML = '';
    if (titleRut) titleRut.textContent = rut;
    if (titleNum) titleNum.textContent = dj_numero;
    if (titlePer) titlePer.textContent = periodo;
    if (totalEl) totalEl.textContent = '0';

    // Llamada a la API (ruta con base_datos desde la URL)
    const basePath = window.location.pathname.split('/')[1];
    const url = `/${basePath}/api/dj-observaciones?rut=${encodeURIComponent(rut)}&dj_numero=${encodeURIComponent(dj_numero)}&periodo=${encodeURIComponent(periodo)}`;

    fetch(url)
      .then(res => res.json())
      .then(data => {
        if (!data || !data.exito) {
          document.getElementById('modalDJErrorText').textContent = data.error || 'Error al cargar observaciones';
          document.getElementById('modalDJError').style.display = 'block';
          if (loading) loading.style.display = 'none';
          return;
        }

        const obs = data.observaciones || [];
        // Render vertical cards
        const listEl = document.getElementById('observacionesDJList');
        if (listEl) {
          listEl.innerHTML = '';
          obs.forEach((o, idx) => {
            const card = document.createElement('div');
            card.className = 'observacion-card';
            const header = document.createElement('div');
            header.className = 'observacion-card-header';
            header.textContent = `Observación ${o.observacion_code || ('#' + (idx + 1))}`;
            const desc = document.createElement('div');
            desc.className = 'observacion-card-body';
            desc.innerHTML = `<h6>Descripción</h6><p>${o.descripcion || ''}</p><h6>Orientación</h6><p>${o.orientacion || ''}</p>`;
            card.appendChild(header);
            card.appendChild(desc);
            listEl.appendChild(card);
          });
        }

        if (totalEl) totalEl.textContent = obs.length.toString();
        if (loading) loading.style.display = 'none';
        if (content) content.style.display = 'block';
      })
      .catch(err => {
        console.error('Error fetching observaciones DJ:', err);
        document.getElementById('modalDJErrorText').textContent = err.message || String(err);
        document.getElementById('modalDJError').style.display = 'block';
        if (loading) loading.style.display = 'none';
      });

  } catch (e) {
    console.error('Error abrirModalObservacionesDJ:', e);
  }
}
