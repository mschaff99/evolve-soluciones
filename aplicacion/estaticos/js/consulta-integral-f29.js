/**
 * JavaScript para funcionalidades de Consulta Integral F29
 * Maneja expansión de tablas, filtros dinámicos y modal de observaciones
 */

console.log('Cargando consulta-integral-f29.js...');

// Variables globales
let empresasExpandidas = new Set();
let currentRutObservaciones = null;
let currentPeriodoObservaciones = null;

// ==================== DECLARACIÓN INMEDIATA DE FUNCIONES GLOBALES ====================
// Esto asegura que las funciones estén disponibles antes de que se renderice el HTML

/**
 * Mostrar modal de observaciones para un período específico
 * @param {string} rut - RUT de la empresa
 * @param {string} periodo - Período a consultar
 */
function mostrarObservaciones(rut, periodo) {
    console.log(`Abriendo modal de observaciones para RUT: ${rut}, Período: ${periodo}`);

    // Guardar RUT y período actuales para el botón de proveedores
    currentRutObservaciones = rut;
    currentPeriodoObservaciones = periodo;

    const modal = document.getElementById('modalObservaciones');
    const loading = document.getElementById('modalLoading');
    const content = document.getElementById('modalObservacionesContent');
    const error = document.getElementById('modalError');
    const btnBuscarProveedores = document.getElementById('btnBuscarProveedores');

    if (!modal) {
        console.error('Modal de observaciones no encontrado');
        return;
    }

    // Mostrar modal con flex para centrar el contenido
    modal.style.display = 'flex';
    loading.style.display = 'block';
    content.style.display = 'none';
    error.style.display = 'none';

    // Mostrar botón de buscar proveedores
    if (btnBuscarProveedores) {
        btnBuscarProveedores.style.display = 'inline-block';
    }

    // Actualizar título
    document.getElementById('modalTitle').textContent = `Observaciones - Período ${periodo}`;

    // Codificar el RUT para la URL (importante para RUTs con guiones)
    const rutCodificado = encodeURIComponent(rut);
    const url = `/consulta-integral-f29/api/observaciones/${rutCodificado}/${periodo}`;
    console.log(`Haciendo petición a: ${url}`);

    fetch(url)
        .then(response => {
            console.log(`Respuesta recibida: ${response.status} ${response.statusText}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Datos recibidos:', data);
            loading.style.display = 'none';

            if (data.exito) {
                // Actualizar información básica
                document.getElementById('modalRut').textContent = data.rut;
                document.getElementById('modalPeriodo').textContent = data.periodo;
                document.getElementById('modalTotal').textContent = data.total;

                // Llenar tabla de observaciones
                const tbody = document.getElementById('observacionesBody');
                tbody.innerHTML = '';

                if (data.observaciones && data.observaciones.length > 0) {
                    data.observaciones.forEach(obs => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td><span class="codigo-badge">${obs.codigo || '-'}</span></td>
                            <td class="descripcion-celda">${obs.descripcion || '-'}</td>
                            <td class="monto-celda">${obs.monto || '-'}</td>
                        `;
                        tbody.appendChild(row);
                    });
                } else {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="3" class="sin-observaciones">
                                <i class="fas fa-info-circle"></i>
                                No hay observaciones para este período
                            </td>
                        </tr>
                    `;
                }

                content.style.display = 'block';
            } else {
                mostrarError(data.error || 'Error desconocido al cargar observaciones');
            }
        })
        .catch(err => {
            console.error('Error al cargar observaciones:', err);
            loading.style.display = 'none';
            mostrarError('Error al cargar observaciones: ' + err.message);
        });
}

/**
 * Cerrar modal de observaciones
 */
function cerrarModalObservaciones() {
    const modal = document.getElementById('modalObservaciones');
    if (modal) {
        modal.style.display = 'none';
        console.log('Modal de observaciones cerrado');
    }
}

/**
 * Mostrar mensaje de error en el modal
 * @param {string} mensaje - Mensaje de error a mostrar
 */
function mostrarError(mensaje) {
    const error = document.getElementById('modalError');
    const errorText = document.getElementById('errorText');

    errorText.textContent = mensaje;
    error.style.display = 'block';
}

/**
 * Cerrar modal al hacer click fuera del contenido
 */
function setupModalClickOutside() {
    const modal = document.getElementById('modalObservaciones');
    if (modal) {
        modal.addEventListener('click', function (event) {
            // Solo cerrar si se hizo click en el overlay (no en el contenido del modal)
            if (event.target === modal) {
                cerrarModalObservaciones();
            }
        });
    }
}

/**
 * Abre el modal de proveedores con observaciones
 */
function buscarProveedores() {
    if (!currentRutObservaciones || !currentPeriodoObservaciones) {
        alert('ERROR: No hay datos de RUT y período disponibles');
        return;
    }

    console.log(`Buscando proveedores para RUT: ${currentRutObservaciones}, Período: ${currentPeriodoObservaciones}`);

    const modal = document.getElementById('modalProveedores');
    const loading = document.getElementById('modalProveedoresLoading');
    const content = document.getElementById('modalProveedoresContent');
    const error = document.getElementById('modalProveedoresError');

    if (!modal) {
        console.error('Modal de proveedores no encontrado');
        return;
    }

    // Mostrar modal con flex para centrar el contenido
    modal.style.display = 'flex';
    loading.style.display = 'block';
    content.style.display = 'none';
    error.style.display = 'none';

    // Actualizar título e información
    document.getElementById('modalProveedoresTitle').textContent = `Proveedores - Período ${currentPeriodoObservaciones}`;
    document.getElementById('modalProveedoresRut').textContent = currentRutObservaciones;
    document.getElementById('modalProveedoresPeriodo').textContent = currentPeriodoObservaciones;

    // Construir URL del endpoint (codificar RUT para URL)
    const rutCodificado = encodeURIComponent(currentRutObservaciones);
    const url = `/consulta-integral-f29/api/proveedores/${rutCodificado}/${currentPeriodoObservaciones}`;
    console.log(`Haciendo petición a: ${url}`);

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            loading.style.display = 'none';

            if (data.exito) {
                // Actualizar total
                document.getElementById('modalProveedoresTotal').textContent = data.total;

                // Llenar tabla de proveedores
                const tbody = document.getElementById('proveedoresBody');
                tbody.innerHTML = '';

                if (data.proveedores && data.proveedores.length > 0) {
                    data.proveedores.forEach(prov => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${prov.tipo_doc || '-'}</td>
                            <td>${prov.tipo_compra || '-'}</td>
                            <td>${prov.rut_proveedor || '-'}</td>
                            <td>${prov.razon_social || '-'}</td>
                            <td>${prov.folio || '-'}</td>
                            <td>${formatearFechaProveedor(prov.fecha_docto)}</td>
                            <td class="text-right">${formatearMonto(prov.monto_neto)}</td>
                            <td class="text-right">${formatearMonto(prov.monto_iva_recuperable)}</td>
                            <td class="text-right">${formatearMonto(prov.monto_total)}</td>
                        `;
                        tbody.appendChild(row);
                    });
                } else {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="9" class="sin-observaciones">
                                <i class="fas fa-info-circle"></i>
                                No se encontraron proveedores con observaciones para este período
                            </td>
                        </tr>
                    `;
                }

                content.style.display = 'block';
            } else {
                mostrarErrorProveedores(data.error || 'Error desconocido al cargar proveedores');
            }
        })
        .catch(err => {
            console.error('Error al cargar proveedores:', err);
            loading.style.display = 'none';
            mostrarErrorProveedores('Error de conexión al cargar proveedores');
        });
}

/**
 * Cierra el modal de proveedores
 */
function cerrarModalProveedores() {
    const modal = document.getElementById('modalProveedores');
    if (modal) {
        modal.style.display = 'none';
        console.log('Modal de proveedores cerrado');
    }
}

/**
 * Muestra un mensaje de error en el modal de proveedores
 * @param {string} mensaje - Mensaje de error a mostrar
 */
function mostrarErrorProveedores(mensaje) {
    const content = document.getElementById('modalProveedoresContent');
    const error = document.getElementById('modalProveedoresError');
    const errorText = document.getElementById('proveedoresErrorText');

    if (content) content.style.display = 'none';
    if (error) error.style.display = 'block';
    if (errorText) errorText.textContent = mensaje;
}

/**
 * Formatea una fecha para la tabla de proveedores
 * @param {string} fecha - Fecha en formato YYYY-MM-DD
 * @returns {string} - Fecha formateada DD-MM-YYYY
 */
function formatearFechaProveedor(fecha) {
    if (!fecha) return '-';

    try {
        // Si viene como string YYYY-MM-DD
        const partes = fecha.split('-');
        if (partes.length === 3) {
            return `${partes[2]}-${partes[1]}-${partes[0]}`;
        }
        return fecha;
    } catch (e) {
        return fecha;
    }
}

/**
 * Formatea un monto numérico con separador de miles
 * @param {number|string} monto - Monto a formatear
 * @returns {string} - Monto formateado con separador de miles
 */
function formatearMonto(monto) {
    if (monto === null || monto === undefined || monto === '') return '-';

    try {
        const numero = parseFloat(monto);
        if (isNaN(numero)) return '-';

        return numero.toLocaleString('es-CL', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    } catch (e) {
        return monto;
    }
}

// Asignar funciones al objeto window para que sean globales
window.mostrarObservaciones = mostrarObservaciones;
window.cerrarModalObservaciones = cerrarModalObservaciones;
window.setupModalClickOutside = setupModalClickOutside;
window.buscarProveedores = buscarProveedores;
window.cerrarModalProveedores = cerrarModalProveedores;

console.log('✓ Funciones del modal asignadas globalmente');

/**
 * Alterna la expansión de una empresa (mostrar/ocultar períodos)
 * @param {HTMLElement} boton - El botón que se clickeó
 */
function alternarEmpresa(boton) {
    try {
        const fila = boton.closest('tr');
        if (!fila) {
            console.error('No se pudo encontrar la fila padre del botón');
            return;
        }

        const rut = fila.dataset.rut || boton.dataset.rut;
        if (!rut) {
            console.error('No se pudo encontrar el RUT de la empresa');
            return;
        }

        // Buscar todas las filas de períodos de esta empresa
        const filasPeriodos = document.querySelectorAll(`tr[data-parent-rut="${rut}"]`);

        if (empresasExpandidas.has(rut)) {
            // Colapsar
            filasPeriodos.forEach(fila => fila.style.display = 'none');
            empresasExpandidas.delete(rut);

            // Cambiar ícono del botón
            const icono = boton.querySelector('i');
            if (icono) {
                icono.className = 'fas fa-chevron-right';
            }
            boton.title = 'Expandir períodos';

            console.log(`Empresa ${rut} colapsada`);
        } else {
            // Expandir
            filasPeriodos.forEach(fila => fila.style.display = '');
            empresasExpandidas.add(rut);

            // Cambiar ícono del botón
            const icono = boton.querySelector('i');
            if (icono) {
                icono.className = 'fas fa-chevron-down';
            }
            boton.title = 'Colapsar períodos';

            console.log(`Empresa ${rut} expandida`);
        }
    } catch (error) {
        console.error('Error en alternarEmpresa:', error);
    }
}

// Helper para obtener valor seguro de input/select
function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value : '';
}

// Debounce para optimizar el rendimiento de los filtros
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

// ==================== FUNCIONES DE EXPANSIÓN DE TABLAS ====================

/**
 * Expandir/contraer empresa individual
 * @param {HTMLElement} boton - Botón de expansión clickeado
 */
function alternarEmpresa(boton) {
    const empresaKey = boton.getAttribute('data-empresa');
    const icono = boton.querySelector('.icono-alternar');

    const filasDetalle = document.querySelectorAll(`.fila-mes-detalle[data-empresa="${empresaKey}"]`);
    if (filasDetalle.length === 0) return;

    const estaVisible = filasDetalle[0].style.display !== 'none';

    filasDetalle.forEach(fila => {
        fila.style.display = estaVisible ? 'none' : 'table-row';
    });

    if (estaVisible) {
        // Colapsar: cambiar a ícono de plus
        icono.className = 'fas fa-plus icono-alternar';
        boton.classList.remove('expandido');
        empresasExpandidas.delete(empresaKey);
    } else {
        // Expandir: cambiar a ícono de minus
        icono.className = 'fas fa-minus icono-alternar';
        boton.classList.add('expandido');
        empresasExpandidas.add(empresaKey);
    }
}

/**
 * Expandir todas las empresas
 */
function expandirTodas() {
    document.querySelectorAll('.boton-expandir-empresa').forEach(boton => {
        const empresaKey = boton.getAttribute('data-empresa');
        document.querySelectorAll(`.fila-mes-detalle[data-empresa="${empresaKey}"]`).forEach(f => f.style.display = 'table-row');
        const icono = boton.querySelector('.icono-alternar');
        if (icono) icono.className = 'fas fa-minus icono-alternar';
        boton.classList.add('expandido');
        empresasExpandidas.add(empresaKey);
    });
}

/**
 * Contraer todas las empresas
 */
function contraerTodas() {
    document.querySelectorAll('.boton-expandir-empresa').forEach(boton => {
        const empresaKey = boton.getAttribute('data-empresa');
        document.querySelectorAll(`.fila-mes-detalle[data-empresa="${empresaKey}"]`).forEach(f => f.style.display = 'none');
        const icono = boton.querySelector('.icono-alternar');
        if (icono) icono.className = 'fas fa-plus icono-alternar';
        boton.classList.remove('expandido');
        empresasExpandidas.delete(empresaKey);
    });
}

// ==================== FUNCIONES DE FILTRADO ====================

/**
 * Filtrar empresas F29 - Filtrado específico para consulta integral
 */
function filtrarEmpresasF29() {
    console.log(' Iniciando filtrado específico para Consulta Integral F29...');

    // Guard: Si la tabla no existe (estamos en dashboard), no hacer nada
    const rows = document.querySelectorAll('.modern-table tbody tr.empresa-row');
    if (rows.length === 0) {
        console.log(' Tabla de Consulta F29 no encontrada. Saltando filtrado.');
        return;
    }

    // PASO 1: Colapsar todas las empresas expandidas antes de filtrar
    // Esto evita que filas de detalle de otras empresas queden visibles
    empresasExpandidas.forEach(rut => {
        // Ocultar todas las filas de detalle de esta empresa
        const filasDetalle = document.querySelectorAll(`.fila-mes-detalle[data-empresa="${rut}"]`);
        filasDetalle.forEach(fila => {
            fila.style.display = 'none';
        });

        // Resetear el icono del botón a "collapsed"
        const botonExpandir = document.querySelector(`button.btn-expand[data-empresa="${rut}"]`);
        if (botonExpandir) {
            const icono = botonExpandir.querySelector('i');
            if (icono) {
                icono.className = 'fas fa-plus icono-alternar';
            }
        }
    });

    // Limpiar el Set de empresas expandidas
    empresasExpandidas.clear();
    console.log(' Todas las empresas expandidas colapsadas antes de filtrar');

    // PASO 2: Filtrado local optimizado
    const empresaInput = document.getElementById('empresaInput');
    const usuarioSelect = document.getElementById('usuarioSelect');
    const grupoSelect = document.getElementById('grupoSelect');
    const observacionesSelect = document.getElementById('observacionesSelect');

    const empresaTerm = empresaInput ? empresaInput.value.toLowerCase().trim() : '';
    const usuarioTerm = usuarioSelect ? usuarioSelect.value.toLowerCase().trim() : '';
    const grupoTerm = grupoSelect ? grupoSelect.value.toLowerCase().trim() : '';
    const observacionesFiltro = observacionesSelect ? observacionesSelect.value : '';

    // Debug: verificar valores de selectores
    console.log(' Valores actuales:');
    console.log('   usuario:', usuarioSelect?.value || 'vacío');
    console.log('   grupo:', grupoSelect?.value || 'vacío');
    console.log('   observaciones:', observacionesFiltro || 'todos');

    console.log('Términos de filtrado:', {
        empresa: empresaTerm,
        usuario: usuarioTerm,
        grupo: grupoTerm,
        observaciones: observacionesFiltro
    });
    let visibleCount = 0;

    console.log(` Encontradas ${rows.length} filas para filtrar`);

    // Debug: Mostrar datos de las primeras 3 filas
    if (usuarioTerm || grupoTerm) {
        console.log('Debug - Datos de las primeras 3 filas:');
        for (let i = 0; i < Math.min(3, rows.length); i++) {
            const row = rows[i];
            const empresaName = row.querySelector('.empresa-name')?.textContent || 'N/A';
            const usuarioData = row.getAttribute('data-usuario') || '';
            const grupoData = row.getAttribute('data-grupo') || '';
            const debugInfo = row.querySelector('.debug-info')?.textContent || 'N/A';
            console.log(`   Fila ${i + 1}: "${empresaName}" - Usuario: "${usuarioData}" - Grupo: "${grupoData}" - Debug: "${debugInfo}"`);
        }
    }

    rows.forEach(row => {
        let showRow = true;

        // Filtrar por empresa
        if (empresaTerm) {
            const empresaCell = row.querySelector('.empresa-name');
            if (empresaCell) {
                const empresaText = empresaCell.textContent.toLowerCase().trim();
                showRow = showRow && empresaText.includes(empresaTerm);
            } else {
                showRow = false;
            }
        }

        // Filtrar por usuario
        if (usuarioTerm && showRow) {
            const usuarioData = (row.getAttribute('data-usuario') || '').toLowerCase();
            const empresaName = row.querySelector('.empresa-name')?.textContent || 'N/A';

            const matchUsuario = usuarioData.includes(usuarioTerm);

            showRow = showRow && matchUsuario;
        }

        // Filtrar por grupo
        if (grupoTerm && showRow) {
            const grupoData = (row.getAttribute('data-grupo') || '').toLowerCase();
            showRow = showRow && grupoData.includes(grupoTerm);
        }

        // Filtrar por observaciones
        if (observacionesFiltro && showRow) {
            // Verificar si es un código específico
            if (observacionesFiltro.startsWith('codigo_')) {
                // Extraer el código específico (ej: "codigo_102" -> "102")
                const codigoBuscado = observacionesFiltro.replace('codigo_', '');

                // Obtener los códigos de observaciones de la empresa desde data-codigos-obs
                const codigosEmpresa = (row.getAttribute('data-codigos-obs') || '').split(',').filter(c => c);

                // Mostrar solo si la empresa tiene ese código específico
                showRow = showRow && codigosEmpresa.includes(codigoBuscado);

            } else if (observacionesFiltro === 'con_observaciones') {
                // Obtener los códigos de observaciones de la empresa
                const codigosObsStr = row.getAttribute('data-codigos-obs') || '';
                const tieneObservaciones = codigosObsStr.trim().length > 0;

                // Debug para las primeras 3 filas
                const rowIndex = Array.from(rows).indexOf(row);
                if (rowIndex < 3) {
                    const empresaName = row.querySelector('.empresa-name')?.textContent.trim() || 'N/A';
                    console.log(`   DEBUG Fila ${rowIndex + 1} (${empresaName}):`);
                    console.log(`     - data-codigos-obs: "${codigosObsStr}"`);
                    console.log(`     - tieneObservaciones: ${tieneObservaciones}`);
                }

                // Mostrar solo empresas con observaciones
                showRow = showRow && tieneObservaciones;

            } else if (observacionesFiltro === 'sin_observaciones') {
                // Obtener los códigos de observaciones de la empresa
                const codigosObsStr = row.getAttribute('data-codigos-obs') || '';
                const tieneObservaciones = codigosObsStr.trim().length > 0;

                // Mostrar solo empresas SIN observaciones
                showRow = showRow && !tieneObservaciones;
            }
        }

        // Mostrar/ocultar fila
        if (showRow) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    // Actualizar contador
    const resultsCount = document.querySelector('.results-count');
    if (resultsCount) {
        resultsCount.textContent = `${visibleCount} empresas encontradas`;
    }

    console.log(` Filtrado completado: ${visibleCount} empresas visibles de ${rows.length} totales`);

    return visibleCount;
}

/**
 * Alternar panel de filtros
 */
function alternarFiltros() {
    const contenidoFiltros = document.querySelector('.contenido-filtros');
    const iconoFiltro = document.querySelector('.icono-filtro');
    if (!contenidoFiltros) return;

    if (contenidoFiltros.style.display === 'none') {
        contenidoFiltros.style.display = 'block';
        iconoFiltro.textContent = '▼';
    } else {
        contenidoFiltros.style.display = 'none';
        iconoFiltro.textContent = '▶';
    }
}

/**
 * Limpiar todos los filtros
 */
function limpiarFiltros() {
    const form = document.getElementById('formularioFiltros');
    if (form) form.reset();
    filtrarEmpresasF29();
}

/**
 * Limpiar todos los filtros (función específica para el botón)
 */
function clearAllFilters() {
    // Limpiar todos los filtros disponibles
    const empresaInput = document.getElementById('empresaInput');
    const usuarioSelect = document.getElementById('usuarioSelect');
    const grupoSelect = document.getElementById('grupoSelect');
    const observacionesSelect = document.getElementById('observacionesSelect');

    if (empresaInput) empresaInput.value = '';
    if (usuarioSelect) usuarioSelect.value = '';
    if (grupoSelect) grupoSelect.value = '';
    if (observacionesSelect) observacionesSelect.value = '';

    // Aplicar filtros
    filtrarEmpresasF29();
}

/**
 * Exportar observaciones del usuario a Excel
 */
function exportarObservacionesExcel() {
    console.log(' Iniciando exportación de observaciones a Excel...');

    // Mostrar indicador de carga (opcional)
    const boton = event.target.closest('button');
    const textoOriginal = boton.innerHTML;
    boton.disabled = true;
    boton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Exportando...';

    // Obtener la base de datos actual desde la URL
    // Formato: /<base_datos>/consulta-integral-f29
    const pathParts = window.location.pathname.split('/');
    const baseDatos = pathParts[1]; // Primera parte después del /

    // Realizar petición al backend con la ruta correcta
    const url = `/${baseDatos}/api/exportar-observaciones-excel`;
    console.log('🔗 URL de exportación:', url);

    fetch(url)
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Error al exportar');
                });
            }
            return response.blob();
        })
        .then(blob => {
            // Crear link de descarga
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;

            // Generar nombre de archivo con fecha
            const fecha = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '_');
            a.download = `Observaciones_${fecha}.xlsx`;

            document.body.appendChild(a);
            a.click();

            // Limpiar
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            console.log('Excel descargado exitosamente');

            // Mostrar mensaje de éxito
            alert('Excel exportado exitosamente');
        })
        .catch(error => {
            console.error('Error exportando Excel:', error);
            alert('Error al exportar: ' + error.message);
        })
        .finally(() => {
            // Restaurar botón
            boton.disabled = false;
            boton.innerHTML = textoOriginal;
        });
}

// ==================== FUNCIONES DE EXPORTACIÓN ====================

/**
 * Exportar tabla a Excel
 */
function exportarTabla() {
    fetch('/consulta-integral-f29/api/exportar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            empresa_filtro: getVal('empresaInput'),
            rut_filtro: getVal('rut_filtro'),
            estado_filtro: getVal('estado_filtro')
        })
    })
        .then(r => r.json())
        .then(data => {
            if (data.exito) {
                alert('Datos exportados exitosamente (' + (data.bytes || 0) + ' bytes)');
            } else {
                alert('Error al exportar: ' + (data.error || 'desconocido'));
            }
        })
        .catch(err => {
            console.error('Error:', err);
            alert('Error al exportar datos');
        });
}

// ==================== FUNCIONES DEL MODAL DE OBSERVACIONES ====================


// ==================== FUNCIONES GLOBALES PARA EL TEMPLATE ====================

// Hacer funciones disponibles globalmente INMEDIATAMENTE para onclick en el template
window.alternarEmpresa = alternarEmpresa;
window.expandirTodas = expandirTodas;
window.contraerTodas = contraerTodas;
window.filtrarEmpresasF29 = filtrarEmpresasF29;
window.alternarFiltros = alternarFiltros;
window.limpiarFiltros = limpiarFiltros;
window.clearAllFilters = clearAllFilters;
window.exportarTabla = exportarTabla;
window.exportarObservacionesExcel = exportarObservacionesExcel;
window.mostrarObservaciones = mostrarObservaciones;
window.cerrarModalObservaciones = cerrarModalObservaciones;
window.setupModalClickOutside = setupModalClickOutside;
window.buscarProveedores = buscarProveedores;
window.cerrarModalProveedores = cerrarModalProveedores;

console.log(' Funciones globales asignadas:', {
    alternarEmpresa: typeof window.alternarEmpresa,
    expandirTodas: typeof window.expandirTodas,
    contraerTodas: typeof window.contraerTodas,
    exportarObservacionesExcel: typeof window.exportarObservacionesExcel,
    mostrarObservaciones: typeof window.mostrarObservaciones
});

// ==================== INICIALIZACIÓN Y EVENTOS ====================

/**
 * Inicialización cuando el DOM está listo
 */
document.addEventListener('DOMContentLoaded', function () {
    console.log(' Inicializando Consulta Integral F29...');
    console.log('Verificando elementos del DOM...');

    // Obtener elementos del DOM
    const empresaInput = document.getElementById('empresaInput');
    const filtroRut = document.getElementById('rut_filtro');
    const filtroEstado = document.getElementById('estado_filtro');
    const usuarioSelect = document.getElementById('usuarioSelect');
    const grupoSelect = document.getElementById('grupoSelect');
    const observacionesSelect = document.getElementById('observacionesSelect');
    const tablaResultados = document.getElementById('tablaResultados');

    console.log(' Elementos encontrados:');
    console.log('   empresaInput:', !!empresaInput);
    console.log('   usuarioSelect:', !!usuarioSelect);
    console.log('   grupoSelect:', !!grupoSelect);
    console.log('   observacionesSelect:', !!observacionesSelect);
    console.log('   tablaResultados:', !!tablaResultados);

    // Guard: Si no hay elementos de la página principal de Consulta Integral F29, solo inicializar modal
    const esConsuItaCompletaF29 = !!empresaInput && !!tablaResultados;
    const esModalEnDashboard = !esConsuItaCompletaF29 && document.getElementById('modalObservaciones');

    if (esModalEnDashboard) {
        console.log(' Modo Dashboard: Solo funcionalidades del modal disponibles');
        // El modal ya está disponible vía funciones globales
        setupModalClickOutside();
        console.log(' Modal configurado para cerrar al hacer click fuera');
        return; // No continuar con inicialización de filtros
    }

    console.log(' Modo Página Completa: Inicializando todos los filtros');

    // Crear versión "debounced" de la función de filtrado
    const debouncedFilter = debounce(filtrarEmpresasF29, 200);

    // Agregar event listeners para filtros dinámicos
    if (empresaInput) {
        empresaInput.addEventListener('input', debouncedFilter);
        console.log('Event listener agregado para filtro de empresa');
    }

    if (filtroRut) {
        filtroRut.addEventListener('input', debouncedFilter);
        console.log('Event listener agregado para filtro de RUT');
    }

    if (filtroEstado) {
        filtroEstado.addEventListener('change', debouncedFilter);
        console.log('Event listener agregado para filtro de estado');
    }

    if (usuarioSelect) {
        // Test manual del elemento
        console.log('Test del elemento usuarioSelect:');
        console.log('   ID:', usuarioSelect.id);
        console.log('   Opciones:', usuarioSelect.options.length);
        console.log('   Valor actual:', usuarioSelect.value);

        usuarioSelect.addEventListener('change', function () {
            console.log(' Event listener de usuario disparado!');
            console.log('   Nuevo valor:', usuarioSelect.value);
            filtrarEmpresasF29();
        });

        // Test adicional: agregar también event listener para 'input'
        usuarioSelect.addEventListener('input', function () {
            console.log(' Event listener INPUT de usuario disparado!');
            filtrarEmpresasF29();
        });

        console.log(' Event listener agregado para filtro de usuario');
    } else {
        console.log('Element usuarioSelect no encontrado!');
    }

    if (grupoSelect) {
        grupoSelect.addEventListener('change', function () {
            console.log(' Event listener de grupo disparado!');
            filtrarEmpresasF29();
        });
        console.log(' Event listener agregado para filtro de grupo');
    }

    if (observacionesSelect) {
        observacionesSelect.addEventListener('change', function () {
            console.log(' Event listener de observaciones disparado!');
            console.log('   Valor seleccionado:', observacionesSelect.value);
            filtrarEmpresasF29();
        });
        console.log(' Event listener agregado para filtro de observaciones');
    }

    // Ejecutar filtros una vez al cargar
    setTimeout(() => {
        try {
            filtrarEmpresasF29();
            console.log(' Filtros iniciales aplicados');
        } catch (e) {
            console.warn(' Error aplicando filtros iniciales:', e);
        }
    }, 150);

    // Configurar cierre de modal al hacer click fuera
    setupModalClickOutside();
    console.log(' Modal configurado para cerrar al hacer click fuera');

    // Test manual después de 3 segundos
    setTimeout(() => {
        console.log(' Test manual de selectores...');
        const usuarioTest = document.getElementById('usuarioSelect');
        const grupoTest = document.getElementById('grupoSelect');

        // Debug de prueba removido tras validación
    }, 3000);

    // ==================== INICIALIZAR TOOLTIPS DE BOOTSTRAP ====================

    /**
     * Inicializar todos los tooltips de Bootstrap
     * Usar delegación de eventos para tooltips dinámicos
     */
    console.log('🔧 Inicializando tooltips de Bootstrap...');

    // Inicializar tooltips estáticos
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover',
            delay: { show: 100, hide: 100 }
        });
    });

    // Observer para detectar nuevos elementos con tooltips (cuando se expanden filas)
    const observador = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            mutation.addedNodes.forEach(function (node) {
                if (node.nodeType === 1 && node.matches('[data-bs-toggle="tooltip"]')) {
                    new bootstrap.Tooltip(node, {
                        trigger: 'hover',
                        delay: { show: 100, hide: 100 }
                    });
                }
                // Buscar en descendientes también
                if (node.querySelectorAll) {
                    const tooltips = node.querySelectorAll('[data-bs-toggle="tooltip"]');
                    tooltips.forEach(function (el) {
                        new bootstrap.Tooltip(el, {
                            trigger: 'hover',
                            delay: { show: 100, hide: 100 }
                        });
                    });
                }
            });
        });
    });

    // Observar cambios en la tabla
    const tablaBody = document.querySelector('#tablaResultados tbody');
    if (tablaBody) {
        observador.observe(tablaBody, { childList: true, subtree: true });
        console.log('Observer de tooltips configurado');
    }

    console.log('Tooltips de Bootstrap inicializados');
});

// ==================== EVENT LISTENERS GLOBALES ====================

// Cerrar modales al hacer click fuera
document.addEventListener('click', function (e) {
    const modalObservaciones = document.getElementById('modalObservaciones');
    const modalProveedores = document.getElementById('modalProveedores');

    if (e.target === modalObservaciones) {
        cerrarModalObservaciones();
    }

    if (e.target === modalProveedores) {
        cerrarModalProveedores();
    }
});

// Cerrar modales con tecla Escape
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        const modalProveedores = document.getElementById('modalProveedores');
        const modalObservaciones = document.getElementById('modalObservaciones');

        // Si el modal de proveedores está visible, cerrarlo primero
        if (modalProveedores && modalProveedores.style.display === 'flex') {
            cerrarModalProveedores();
        } else if (modalObservaciones && modalObservaciones.style.display === 'flex') {
            cerrarModalObservaciones();
        }
    }
});

