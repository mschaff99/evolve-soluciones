/**
 * IA Dashboard - JavaScript
 * Módulo de Inteligencia Artificial para análisis contable
 * Evolve Soluciones
 */

// Variables globales
const csrfMetaTag = document.querySelector('meta[name=csrf-token]');
const csrfToken = csrfMetaTag ? csrfMetaTag.getAttribute('content') : '';

console.log('CSRF Token:', csrfToken ? 'Disponible' : 'No encontrado');

// Función para obtener CSRF Token
function getCSRFToken() {
  const metaTag = document.querySelector('meta[name=csrf-token]');
  return metaTag ? metaTag.getAttribute('content') : '';
}

// Función para cargar la lista de empresas
async function cargarListaEmpresas() {
  try {
    console.log('Cargando lista de empresas...');

    const anio = document.getElementById('filtro-anio').value;
    const mes = document.getElementById('filtro-periodo').value;

    const response = await fetch(`/ia/api/empresas-lista?anio=${anio}&mes=${mes}`);
    const data = await response.json();

    if (data.success) {
      console.log(`${data.total} empresas cargadas`);
      mostrarListaEmpresas(data.empresas);
    } else {
      console.error('Error cargando empresas:', data.error);
      mostrarErrorEmpresas('Error al cargar las empresas: ' + (data.error || 'Error desconocido'));
    }

  } catch (error) {
    console.error('Error en solicitud:', error);
    mostrarErrorEmpresas('Error de conexión al cargar empresas');
  }
}

// Función para mostrar la lista de empresas
function mostrarListaEmpresas(empresas) {
  const container = document.getElementById('empresas-container');

  if (!empresas || empresas.length === 0) {
    container.innerHTML = `
            <div class="ia-empty-state">
                <i class="fas fa-info-circle"></i>
                <h5>No hay empresas disponibles</h5>
                <p>No se encontraron empresas para el período seleccionado</p>
            </div>
        `;
    return;
  }

  const tableHtml = `
        <div class="table-responsive">
            <table class="table table-ia-empresas">
                <thead>
                    <tr>
                        <th>RUT</th>
                        <th>Empresa</th>
                        <th>Usuario</th>
                        <th>Grupo</th>
                        <th class="text-center">Acciones IA</th>
                    </tr>
                </thead>
                <tbody>
                    ${empresas.map(empresa => `
                        <tr>
                            <td>
                                <span class="badge-rut">${empresa.rut || 'N/A'}</span>
                            </td>
                            <td>
                                <strong class="text-empresa">${empresa.empresa || 'Sin nombre'}</strong>
                            </td>
                            <td>
                                <span class="badge-usuario">${empresa.usuario || 'Sin asignar'}</span>
                            </td>
                            <td>
                                <span class="badge-grupo">${empresa.grupo || 'Sin grupo'}</span>
                            </td>
                            <td class="text-center">
                                <div class="ia-action-buttons">
                                    <button class="btn btn-ia-action btn-ia-balance"
                                            onclick="generarBalanceCompleto('${empresa.rut}', '${empresa.empresa}')"
                                            title="Generar Balance de 8 Columnas">
                                        <i class="fas fa-calculator"></i>
                                        Balance
                                    </button>
                                    <button class="btn btn-ia-action btn-ia-analizar"
                                            onclick="analizarBalanceConIA('${empresa.rut}', '${empresa.empresa}')"
                                            title="Analizar Balance con IA">
                                        <i class="fas fa-brain"></i>
                                        Analizar IA
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;

  container.innerHTML = tableHtml;
}

// Función para mostrar errores
function mostrarErrorEmpresas(mensaje) {
  const container = document.getElementById('empresas-container');
  container.innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle"></i>
            ${mensaje}
        </div>
    `;
}

// Inicializar al cargar la página
document.addEventListener('DOMContentLoaded', function () {
  console.log('Dashboard IA cargado, iniciando carga de empresas...');
  cargarListaEmpresas();

  // Configurar eventos del modal
  const modalElement = document.getElementById('modalBalance');
  if (modalElement) {
    modalElement.addEventListener('hidden.bs.modal', function () {
      console.log('Modal cerrado - limpiando recursos...');

      // Limpiar contenido
      const tableBody = document.getElementById('balanceTableBody');
      if (tableBody) {
        tableBody.innerHTML = '';
      }

      // Resetear análisis IA
      cerrarAnalisisIA();

      // Limpiar backdrops colgados
      setTimeout(() => {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
      }, 100);
    });

    console.log('Eventos del modal configurados');
  }
});

// Exportar funciones globales para uso desde HTML inline events
window.cargarListaEmpresas = cargarListaEmpresas;
window.getCSRFToken = getCSRFToken;

// ============================================================================
// FUNCIONES DE GENERACIÓN Y ANÁLISIS DE BALANCE
// ============================================================================

/**
 * Función principal para generar balance completo
 */
async function generarBalanceCompleto(rut, nombreEmpresa) {
  console.log(`Iniciando generación de balance para ${nombreEmpresa} (${rut})`);
  mostrarConfiguracionBalance(rut, nombreEmpresa, 'balance');
}

/**
 * Función principal para análisis con IA
 */
async function analizarBalanceConIA(rut, nombreEmpresa) {
  console.log(`Iniciando análisis IA para ${nombreEmpresa} (${rut})`);
  mostrarConfiguracionBalance(rut, nombreEmpresa, 'analisis');
}

/**
 * Modal de configuración de período
 */
function mostrarConfiguracionBalance(empresaRut, empresaNombre, tipoOperacion = 'balance') {
  const tituloOperacion = tipoOperacion === 'analisis' ? 'Análisis con IA' : 'Generar Balance';
  const iconoOperacion = tipoOperacion === 'analisis' ? 'fas fa-brain' : 'fas fa-calculator';

  Swal.fire({
    title: `Configurar Período - ${tituloOperacion}`,
    html: `
            <div class="text-start">
                <p><strong>Empresa:</strong> ${empresaNombre}</p>
                <p><strong>RUT:</strong> ${empresaRut}</p>
                <hr>
                <div class="row mb-3">
                    <div class="col-6">
                        <label class="form-label">Año Inicio</label>
                        <select id="anioInicio" class="form-select">
                            <option value="2024">2024</option>
                            <option value="2025" selected>2025</option>
                            <option value="2026">2026</option>
                        </select>
                    </div>
                    <div class="col-6">
                        <label class="form-label">Mes Inicio</label>
                        <select id="mesInicio" class="form-select">
                            <option value="1" selected>Enero</option>
                            <option value="2">Febrero</option>
                            <option value="3">Marzo</option>
                            <option value="4">Abril</option>
                            <option value="5">Mayo</option>
                            <option value="6">Junio</option>
                            <option value="7">Julio</option>
                            <option value="8">Agosto</option>
                            <option value="9">Septiembre</option>
                            <option value="10">Octubre</option>
                            <option value="11">Noviembre</option>
                            <option value="12">Diciembre</option>
                        </select>
                    </div>
                </div>
                <div class="row">
                    <div class="col-6">
                        <label class="form-label">Año Fin</label>
                        <select id="anioFin" class="form-select">
                            <option value="2024">2024</option>
                            <option value="2025" selected>2025</option>
                            <option value="2026">2026</option>
                        </select>
                    </div>
                    <div class="col-6">
                        <label class="form-label">Mes Fin</label>
                        <select id="mesFin" class="form-select">
                            <option value="1">Enero</option>
                            <option value="2">Febrero</option>
                            <option value="3">Marzo</option>
                            <option value="4">Abril</option>
                            <option value="5">Mayo</option>
                            <option value="6">Junio</option>
                            <option value="7">Julio</option>
                            <option value="8">Agosto</option>
                            <option value="9">Septiembre</option>
                            <option value="10">Octubre</option>
                            <option value="11">Noviembre</option>
                            <option value="12">Diciembre</option>
                        </select>
                    </div>
                </div>
            </div>
        `,
    showCancelButton: true,
    confirmButtonText: `<i class="${iconoOperacion}"></i> ${tituloOperacion}`,
    cancelButtonText: 'Cancelar',
    didOpen: () => {
      const mesActual = new Date().getMonth() + 1;
      document.getElementById('mesFin').value = mesActual;
    },
    preConfirm: () => {
      const anioInicio = parseInt(document.getElementById('anioInicio').value);
      const mesInicio = parseInt(document.getElementById('mesInicio').value);
      const anioFin = parseInt(document.getElementById('anioFin').value);
      const mesFin = parseInt(document.getElementById('mesFin').value);

      if (anioInicio > anioFin || (anioInicio === anioFin && mesInicio > mesFin)) {
        Swal.showValidationMessage('El período de inicio debe ser anterior al período de fin');
        return false;
      }

      return { anioInicio, mesInicio, anioFin, mesFin };
    }
  }).then((result) => {
    if (result.isConfirmed) {
      const { anioInicio, mesInicio, anioFin, mesFin } = result.value;

      if (tipoOperacion === 'analisis') {
        ejecutarAnalisisIA(empresaRut, empresaNombre, anioInicio, mesInicio, anioFin, mesFin);
      } else {
        ejecutarGeneracionBalance(empresaRut, empresaNombre, anioInicio, mesInicio, anioFin, mesFin);
      }
    }
  });
}

/**
 * Función para ejecutar generación de balance
 */
async function ejecutarGeneracionBalance(empresaRut, empresaNombre, anioInicio, mesInicio, anioFin, mesFin) {
  try {
    console.log('Generando balance:', { empresaRut, empresaNombre, anioInicio, mesInicio, anioFin, mesFin });

    Swal.fire({
      title: 'Generando Balance...',
      html: `
                <div class="text-center">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <p><strong>${empresaNombre}</strong></p>
                    <p>Período: ${mesInicio}/${anioInicio} - ${mesFin}/${anioFin}</p>
                    <small class="text-muted">Este proceso puede tomar unos segundos...</small>
                </div>
            `,
      allowOutsideClick: false,
      showConfirmButton: false
    });

    const response = await fetch('/ia/generar-balance', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.csrfToken || getCSRFToken()
      },
      body: JSON.stringify({
        empresa_rut: empresaRut,
        anio_inicio: anioInicio,
        mes_inicio: mesInicio,
        anio_fin: anioFin,
        mes_fin: mesFin
      })
    });

    const data = await response.json();

    if (data.estado === 'exitoso') {
      console.log('Balance generado:', data);
      Swal.close();

      setTimeout(() => {
        try {
          const swalElements = document.querySelectorAll('.swal2-container, .swal2-backdrop, [aria-labelledby^="swal2"]');
          swalElements.forEach(el => {
            if (el && el.remove && !el.querySelector('#modalBalance') && el.id !== 'modalBalance') {
              console.log('Eliminando elemento SweetAlert:', el.className || el.tagName);
              el.remove();
            }
          });

          const elementosConAriaHidden = document.querySelectorAll('[aria-hidden="true"]');
          elementosConAriaHidden.forEach(el => {
            if (!el.classList.contains('modal') && el.id !== 'modalBalance') {
              console.log('Removiendo aria-hidden de:', el.className || el.tagName);
              el.removeAttribute('aria-hidden');
            }
          });

          if (document.body) {
            document.body.classList.remove('swal2-shown', 'swal2-height-auto', 'swal2-overflow-hidden');
            document.body.removeAttribute('aria-hidden');
          }

          console.log('SweetAlert completamente limpiado');
        } catch (e) {
          console.error('Error en limpieza de SweetAlert:', e);
        }
      }, 50);

      setTimeout(() => {
        const backdropsPrevios = document.querySelectorAll('.modal-backdrop, .swal2-backdrop');
        console.log(`Backdrops antes de abrir modal: ${backdropsPrevios.length}`);

        backdropsPrevios.forEach(b => {
          console.log('Eliminando backdrop previo:', b.className);
          b.remove();
        });

        const modalElement = document.getElementById('modalBalance');
        if (!modalElement) {
          console.error('CRÍTICO: El modal #modalBalance no existe en el DOM');
          Swal.fire({
            icon: 'error',
            title: 'Error Técnico',
            text: 'El modal de balance no está disponible. Por favor, recarga la página.',
            confirmButtonText: 'Recargar',
            allowOutsideClick: false
          }).then(() => {
            location.reload();
          });
          return;
        }

        console.log('Modal verificado, existe en DOM');

        mostrarBalanceEnModal(empresaRut, empresaNombre, data.balance, {
          periodo_inicio: `${mesInicio}/${anioInicio}`,
          periodo_fin: `${mesFin}/${anioFin}`,
          fecha_generacion: new Date().toLocaleString('es-CL'),
          anio_inicio: anioInicio,
          mes_inicio: mesInicio,
          anio_fin: anioFin,
          mes_fin: mesFin
        });
      }, 400);
    } else {
      Swal.fire({
        icon: 'error',
        title: 'Error al generar balance',
        html: `<p>${data.mensaje || 'Error desconocido'}</p>`,
        confirmButtonText: 'Entendido'
      });
    }

  } catch (error) {
    console.error('Error generando balance:', error);
    Swal.fire({
      icon: 'error',
      title: 'Error de conexión',
      html: `
                <strong>Error:</strong> ${error.message}<br>
                <small class="text-muted">Verifique su conexión a internet y la base de datos</small>
            `,
      confirmButtonText: 'Entendido'
    });
  }
}

/**
 * Función para ejecutar análisis con IA
 */
async function ejecutarAnalisisIA(empresaRut, empresaNombre, anioInicio, mesInicio, anioFin, mesFin) {
  try {
    console.log(`Iniciando análisis IA:`, { empresaRut, empresaNombre, anioInicio, mesInicio, anioFin, mesFin });
    console.log(`FRONTEND ENVIANDO - anio_inicio: ${anioInicio}, mes_inicio: ${mesInicio}, anio_fin: ${anioFin}, mes_fin: ${mesFin}`);

    Swal.fire({
      title: 'Analizando con IA...',
      html: `
                <div class="text-center">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <p><strong>Generando balance y enviando a Gemini AI para análisis...</strong></p>
                    <div class="progress mb-3">
                        <div class="progress-bar progress-bar-striped progress-bar-animated"
                             role="progressbar" style="width: 100%"></div>
                    </div>
                    <small class="text-muted">
                        Este proceso puede tomar unos minutos<br>
                        Analizando con IA<br>
                    </small>
                </div>
            `,
      allowOutsideClick: false,
      showConfirmButton: false
    });

    const response = await fetch('/ia/analizar-balance-completo', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.csrfToken || getCSRFToken()
      },
      body: JSON.stringify({
        empresa_rut: empresaRut,
        anio_inicio: anioInicio,
        mes_inicio: mesInicio,
        anio_fin: anioFin,
        mes_fin: mesFin
      }),
      signal: AbortSignal.timeout(180000)
    });

    const data = await response.json();

    if (data.success) {
      console.log('Análisis IA completado:', data);
      mostrarResultadoAnalisisIA(data);
    } else {
      mostrarErrorAnalisisIA(`Error: ${data.error || 'Error desconocido'}`, data);
    }

  } catch (error) {
    console.error('Error en análisis IA:', error);

    let errorMessage = 'Error de conexión';
    let errorDetails = error.message;

    if (error.name === 'AbortError' || error.message.includes('timeout')) {
      errorMessage = 'Timeout en análisis IA';
      errorDetails = 'El análisis tomó más tiempo del esperado. Esto puede ocurrir con empresas que tienen muchas cuentas. Intente nuevamente o contacte al administrador.';
    }

    mostrarErrorAnalisisIA(`${errorMessage}: ${errorDetails}`, {
      error: error.message,
      tipo: 'timeout_frontend'
    });
  }
}

/**
 * Función para mostrar resultado de análisis IA
 */
function mostrarResultadoAnalisisIA(data) {
  Swal.fire({
    title: 'Análisis Contable Profesional',
    html: `
            <div class="text-start">
                <div class="alert alert-info mb-3">
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Empresa:</strong> ${data.empresa_info.nombre}<br>
                            <strong>RUT:</strong> ${data.empresa_info.rut}<br>
                        </div>
                        <div class="col-md-6">
                            <strong>Período:</strong> ${data.empresa_info.periodo}<br>
                            <strong>Cuentas Analizadas:</strong> ${data.estadisticas.total_cuentas_analizadas}
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h6 class="mb-0"><i class="fas fa-brain"></i> Análisis Detallado por Inteligencia Artificial</h6>
                    </div>
                    <div class="card-body ap-typography" style="max-height: 500px; overflow-y: auto; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                        <div id="analisisTextSwal"></div>
                    </div>
                </div>

                <div class="mt-3 text-center">
                    <small class="text-muted">
                        <i class="fas fa-clock"></i> Análisis generado el ${new Date(data.estadisticas.fecha_analisis).toLocaleString('es-ES')}
                    </small>
                </div>
            </div>
        `,
    width: '90%',
    showCancelButton: true,
    confirmButtonText: '<i class="fas fa-download"></i> Descargar Análisis Completo',
    cancelButtonText: '<i class="fas fa-times"></i> Cerrar',
    customClass: {
      popup: 'swal-wide',
      confirmButton: 'btn btn-success',
      cancelButton: 'btn btn-secondary'
    },
    buttonsStyling: false,
    didOpen: () => {
      const analisisTextSwal = document.getElementById('analisisTextSwal');
      if (analisisTextSwal && data.analisis) {
        if (typeof window.renderAnalysisMarkdown === 'function') {
          let rendered = window.renderAnalysisMarkdown(data.analisis);
          rendered = rendered
            .replace(/\*\*([^*]+?:)\*\*/g, '<span class="ap-label">$1</span> ')
            .replace(/\*\*/g, '');
          analisisTextSwal.innerHTML = rendered;
        } else {
          analisisTextSwal.textContent = (data.analisis || '').replace(/\*\*/g, '');
        }
      }
    }
  }).then((result) => {
    if (result.isConfirmed) {
      descargarAnalisisIA(data);
    }
  });
}

/**
 * Función para mostrar error en análisis IA
 */
function mostrarErrorAnalisisIA(mensaje, detalles = {}) {
  Swal.fire({
    icon: 'error',
    title: 'Error en Análisis IA',
    html: `
            <div class="text-start">
                <p><strong>Error:</strong> ${mensaje}</p>
                ${detalles.fase ? `<p><strong>Fase:</strong> ${detalles.fase}</p>` : ''}
                ${detalles.detalles ? `<p><strong>Detalles:</strong> ${detalles.detalles}</p>` : ''}
            </div>
        `,
    confirmButtonText: 'Entendido'
  });
}

/**
 * Función para descargar análisis IA
 */
function descargarAnalisisIA(data) {
  const contenido = `
═══════════════════════════════════════════════════════════════
                    ANÁLISIS CONTABLE PROFESIONAL
                        Sistema JT-Asesores IA
═══════════════════════════════════════════════════════════════

INFORMACIÓN DEL ANÁLISIS

Empresa: ${data.empresa_info.nombre}
RUT: ${data.empresa_info.rut}
Período Analizado: ${data.empresa_info.periodo}
Cuentas Analizadas: ${data.estadisticas.total_cuentas_analizadas}
Fecha de Análisis: ${new Date(data.estadisticas.fecha_analisis).toLocaleString('es-ES')}
Analista: Sistema de Inteligencia Artificial Gemini

═══════════════════════════════════════════════════════════════
                    ANÁLISIS DETALLADO
═══════════════════════════════════════════════════════════════

${data.analisis}

═══════════════════════════════════════════════════════════════
                    INFORMACIÓN TÉCNICA
═══════════════════════════════════════════════════════════════

• Análisis basado en normativa contable chilena (PCGA y NIIF para PYMEs)
• Revisión automatizada mediante Inteligencia Artificial
• Evaluación cuenta por cuenta con criterios profesionales
• Identificación de riesgos y recomendaciones específicas

═══════════════════════════════════════════════════════════════

Documento generado automáticamente por:
Sistema JT-Asesores - Módulo de Inteligencia Artificial
${new Date().toLocaleString('es-ES')}

NOTA: Este análisis es una herramienta de apoyo. Se recomienda
revisión adicional por parte de un contador profesional.

═══════════════════════════════════════════════════════════════
    `;

  const blob = new Blob([contenido], { type: 'text/plain;charset=utf-8' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = `analisis-contable-ia-${data.empresa_info.rut.replace(/\./g, '').replace('-', '')}-${new Date().toISOString().split('T')[0]}.txt`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);

  Swal.fire({
    icon: 'success',
    title: 'Descarga Completada',
    html: `
            <div class="text-center">
                <p>El análisis contable profesional se ha descargado correctamente</p>
                <small class="text-muted">Archivo: analisis-contable-ia-${data.empresa_info.rut.replace(/\./g, '').replace('-', '')}-${new Date().toISOString().split('T')[0]}.txt</small>
            </div>
        `,
    timer: 3000,
    showConfirmButton: false
  });
}

// ============================================================================
// FUNCIONES DEL MODAL DE BALANCE
// ============================================================================

/**
 * Muestra el balance en el modal profesional
 */
function mostrarBalanceEnModal(empresaRut, empresaNombre, balanceData, metadata) {
  try {
    const selectores = [
      '.modal-backdrop',
      '.swal2-container',
      '.swal2-backdrop'
    ];

    selectores.forEach(selector => {
      try {
        const elementos = document.querySelectorAll(selector);
        elementos.forEach(el => {
          if (el && el.remove && el.id !== 'modalBalance') {
            console.log(`Eliminando elemento: ${selector}`, el.className);
            el.remove();
          }
        });
      } catch (e) {
        console.warn(`Error eliminando ${selector}:`, e);
      }
    });

    try {
      if (document.body) {
        document.body.classList.remove('swal2-shown', 'swal2-height-auto');
        document.body.removeAttribute('aria-hidden');

        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
          mainContent.removeAttribute('aria-hidden');
          console.log('aria-hidden removido de main-content');
        }

        if (document.body.style) {
          document.body.style.removeProperty('overflow');
          document.body.style.removeProperty('padding-right');
        }

        console.log('Estado del body limpiado');
      }
    } catch (e) {
      console.warn('Error reseteando body:', e);
    }

    if (!balanceData || !balanceData.cuentas_detalle) {
      throw new Error('Datos de balance inválidos');
    }

    const modalElement = document.getElementById('modalBalance');
    if (!modalElement) {
      throw new Error('Modal element not found');
    }

    if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
      throw new Error('Bootstrap Modal no está disponible');
    }

    let modal;
    try {
      modal = bootstrap.Modal.getInstance(modalElement);
      if (!modal) {
        modal = new bootstrap.Modal(modalElement, {
          backdrop: true,
          keyboard: true,
          focus: true
        });
      }
    } catch (modalError) {
      console.error('Error creando instancia del modal:', modalError);
      throw new Error('No se pudo inicializar el modal');
    }

    const balanceLoading = document.getElementById('balanceLoading');
    const balanceError = document.getElementById('balanceError');
    const analisisColumn = document.getElementById('analisisColumn');
    const balanceContent = document.getElementById('balanceContent');

    if (balanceLoading) balanceLoading.style.display = 'none';
    if (balanceError) balanceError.style.display = 'none';
    if (analisisColumn) analisisColumn.style.display = 'none';
    if (balanceContent) balanceContent.style.display = 'block';

    const nombreElement = document.getElementById('balanceEmpresaNombre');
    const rutElement = document.getElementById('balanceEmpresaRut');
    const periodoInicioElement = document.getElementById('balancePeriodoInicio');
    const periodoFinElement = document.getElementById('balancePeriodoFin');
    const fechaElement = document.getElementById('balanceFechaGeneracion');

    if (nombreElement) nombreElement.textContent = empresaNombre;
    if (rutElement) rutElement.textContent = empresaRut;
    if (periodoInicioElement) periodoInicioElement.textContent = metadata.periodo_inicio || 'N/A';
    if (periodoFinElement) periodoFinElement.textContent = metadata.periodo_fin || 'N/A';

    const fechaGeneracion = new Date().toLocaleDateString('es-CL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });

    if (fechaElement) fechaElement.textContent = fechaGeneracion;

    window.balanceActual = {
      empresaRut: empresaRut,
      empresaNombre: empresaNombre,
      balanceData: balanceData,
      metadata: metadata
    };

    const tbody = document.getElementById('balanceTableBody');
    if (!tbody) {
      throw new Error('Elemento balanceTableBody no encontrado');
    }

    tbody.innerHTML = '';

    balanceData.cuentas_detalle.forEach((cuenta) => {
      const tr = document.createElement('tr');

      if (cuenta.nombre && cuenta.nombre.includes('SUMAS')) {
        tr.classList.add('balance-sumas');
      } else if (cuenta.nombre && (cuenta.nombre.includes('RESULTADO') || cuenta.nombre.includes('UTILIDAD') || cuenta.nombre.includes('PÉRDIDA'))) {
        tr.classList.add('balance-resultado');
      } else if (cuenta.nombre && cuenta.nombre.includes('SUMAS IGUALES')) {
        tr.classList.add('balance-sumas-iguales');
      }

      const formatNum = (val) => {
        if (!val || val === 0 || val === '0') return '-';
        const num = typeof val === 'string' ? parseFloat(val) : val;
        return num.toLocaleString('es-CL', {
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        });
      };

      tr.innerHTML = `
                <td>${cuenta.cuenta || ''}</td>
                <td class="text-start">${cuenta.nombre || ''}</td>
                <td>${cuenta.tipo_cuenta || ''}</td>
                <td class="text-end">${formatNum(cuenta.saldos_iniciales_deudor)}</td>
                <td class="text-end">${formatNum(cuenta.saldos_iniciales_acreedor)}</td>
                <td class="text-end">${formatNum(cuenta.debitos)}</td>
                <td class="text-end">${formatNum(cuenta.creditos)}</td>
                <td class="text-end">${formatNum(cuenta.activos)}</td>
                <td class="text-end">${formatNum(cuenta.pasivos)}</td>
                <td class="text-end">${formatNum(cuenta.perdida)}</td>
                <td class="text-end">${formatNum(cuenta.ganancia)}</td>
            `;

      tbody.appendChild(tr);
    });

    document.querySelectorAll('.modal-backdrop, .swal2-backdrop').forEach(el => {
      console.log('PRE-LIMPIEZA: Eliminando backdrop:', el.className);
      el.remove();
    });

    if (modal && typeof modal.show === 'function') {
      console.log('Mostrando modal...');
      modal.show();

      modalElement.style.position = 'fixed';
      modalElement.style.zIndex = '9999';
      modalElement.style.display = 'block';
      modalElement.style.top = '0';
      modalElement.style.left = '0';
      modalElement.style.width = '100%';
      modalElement.style.height = '100%';

      setTimeout(() => {
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
          backdrop.style.position = 'fixed';
          backdrop.style.zIndex = '9998';
          backdrop.style.opacity = '0.5';
          console.log('Backdrop configurado: z-index=9998');
        }

        modalElement.style.zIndex = '9999';
        console.log('Modal configurado: z-index=9999, position=fixed');
      }, 50);
    } else {
      throw new Error('Modal no tiene método show()');
    }

    setTimeout(() => {
      try {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        console.log(`Estado final - Backdrops: ${backdrops.length}`);

        backdrops.forEach((backdrop, index) => {
          if (index === backdrops.length - 1) {
            backdrop.style.zIndex = '9998';
            console.log(`Backdrop activo configurado: z-index=9998`);
          } else {
            console.warn(`Backdrop extra detectado #${index}, eliminando...`);
            backdrop.remove();
          }
        });

        const modalZIndex = window.getComputedStyle(modalElement).zIndex;
        console.log(`Z-index computado del modal: ${modalZIndex}`);

        if (modalZIndex !== '9999') {
          console.warn(`Z-index del modal incorrecto (${modalZIndex}), forzando...`);
          modalElement.style.zIndex = '9999';
        }

        if (document.body && !document.body.classList.contains('modal-open')) {
          document.body.classList.add('modal-open');
        }

        console.log('Verificación final completada');
      } catch (e) {
        console.error('Error en verificación final:', e);
      }
    }, 150);

  } catch (error) {
    console.error('Error al mostrar balance en modal:', error);

    try {
      if (typeof Swal !== 'undefined' && Swal.fire) {
        Swal.fire({
          icon: 'error',
          title: 'Error al Mostrar Balance',
          text: error.message || 'No se pudo cargar el balance en el modal',
          confirmButtonText: 'Entendido'
        });
      } else {
        alert('Error al mostrar balance: ' + (error.message || 'Error desconocido'));
      }
    } catch (swalError) {
      console.error('Error mostrando SweetAlert:', swalError);
      alert('Error al mostrar balance: ' + (error.message || 'Error desconocido'));
    }
  }
}

/**
 * Analiza el balance con IA desde el modal
 */
function analizarBalanceEnModal() {
  if (!window.balanceActual) {
    Swal.fire({
      icon: 'warning',
      title: 'Sin Datos',
      text: 'No hay balance cargado para analizar',
      confirmButtonText: 'Entendido'
    });
    return;
  }

  const { empresaRut, empresaNombre, balanceData, metadata } = window.balanceActual;

  const analisisColumn = document.getElementById('analisisColumn');
  const analisisLoading = document.getElementById('analisisLoading');
  const analisisError = document.getElementById('analisisError');
  const analisisContent = document.getElementById('analisisContent');

  if (!analisisColumn || !analisisLoading || !analisisError || !analisisContent) {
    console.error('Error: No se encontraron los elementos del análisis en el modal');
    Swal.fire({
      icon: 'error',
      title: 'Error de Interfaz',
      text: 'No se pudo inicializar el panel de análisis. Por favor, recarga la página.',
      confirmButtonText: 'Entendido'
    });
    return;
  }

  if (!metadata.anio_inicio || !metadata.mes_inicio || !metadata.anio_fin || !metadata.mes_fin) {
    console.error('Error: Faltan parámetros de período en metadata:', metadata);
    Swal.fire({
      icon: 'error',
      title: 'Datos Incompletos',
      text: 'No se encontró la información del período. Por favor, genera el balance nuevamente.',
      confirmButtonText: 'Entendido'
    });
    return;
  }

  const balanceColumn = document.getElementById('balanceColumn');
  if (balanceColumn) {
    balanceColumn.classList.remove('col-12');
    balanceColumn.classList.add('col-6');
  }

  analisisColumn.style.display = 'block';
  analisisLoading.style.display = 'block';
  analisisError.style.display = 'none';
  analisisContent.style.display = 'none';

  fetch('/ia/analizar-balance-completo', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': window.csrfToken || getCSRFToken()
    },
    body: JSON.stringify({
      empresa_rut: empresaRut,
      anio_inicio: metadata.anio_inicio,
      mes_inicio: metadata.mes_inicio,
      anio_fin: metadata.anio_fin,
      mes_fin: metadata.mes_fin
    })
  })
    .then(response => response.json())
    .then(data => {
      console.log('[DEBUG] Respuesta recibida:', data);

      analisisLoading.style.display = 'none';
      analisisLoading.classList.add('d-none');

      if (data.success && data.analisis) {
        console.log('[DEBUG] Análisis recibido, mostrando contenido...');

        const analisisHtml = marked.parse(data.analisis);
        document.getElementById('analisisTexto').innerHTML = analisisHtml;

        analisisContent.style.display = 'block';
        analisisContent.classList.remove('d-none');

        const analisisFooter = document.getElementById('analisisFooter');
        if (analisisFooter) {
          analisisFooter.style.display = 'block';
          analisisFooter.classList.remove('d-none');
        }

        window.analisisActual = {
          texto: data.analisis,
          empresaNombre: empresaNombre,
          fecha: new Date().toISOString().split('T')[0]
        };

        console.log('[DEBUG] Análisis mostrado correctamente');
      } else {
        throw new Error(data.error || 'Error desconocido en análisis');
      }
    })
    .catch(error => {
      console.error('Error al analizar:', error);

      analisisLoading.style.display = 'none';
      analisisLoading.classList.add('d-none');

      document.getElementById('analisisErrorTexto').textContent = error.message || 'Error al generar análisis';

      analisisError.style.display = 'block';
      analisisError.classList.remove('d-none');

      const errorAlert = analisisError.querySelector('.alert');
      if (errorAlert) {
        errorAlert.style.display = 'block';
      }
    });
}

/**
 * Cierra el panel de análisis IA
 */
function cerrarAnalisisIA() {
  const analisisColumn = document.getElementById('analisisColumn');
  const balanceColumn = document.getElementById('balanceColumn');
  const analisisFooter = document.getElementById('analisisFooter');
  const analisisLoading = document.getElementById('analisisLoading');
  const analisisError = document.getElementById('analisisError');
  const analisisContent = document.getElementById('analisisContent');

  if (analisisColumn) analisisColumn.style.display = 'none';
  if (analisisFooter) analisisFooter.style.display = 'none';

  if (analisisLoading) {
    analisisLoading.style.display = 'none';
    analisisLoading.classList.add('d-none');
  }
  if (analisisError) {
    analisisError.style.display = 'none';
    analisisError.classList.add('d-none');
  }
  if (analisisContent) {
    analisisContent.style.display = 'none';
    analisisContent.classList.add('d-none');
  }

  if (balanceColumn) {
    balanceColumn.classList.remove('col-6');
    balanceColumn.classList.add('col-12');
  }

  window.analisisActual = null;
}

/**
 * Descarga el análisis IA desde el modal
 */
function descargarAnalisisDesdeModal() {
  if (!window.analisisActual) {
    Swal.fire({
      icon: 'warning',
      title: 'Sin Análisis',
      text: 'No hay análisis disponible para descargar',
      confirmButtonText: 'Entendido'
    });
    return;
  }

  const { texto, empresaNombre, fecha } = window.analisisActual;

  const contenido =
    `=========================================\n` +
    `ANÁLISIS FINANCIERO CON INTELIGENCIA ARTIFICIAL\n` +
    `=========================================\n\n` +
    `Empresa: ${empresaNombre}\n` +
    `Fecha de Análisis: ${fecha}\n` +
    `Generado por: Sistema IA Evolve Soluciones\n\n` +
    `${texto}`;

  const blob = new Blob([contenido], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Analisis_Balance_${empresaNombre.replace(/\s+/g, '_')}_${fecha}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  Swal.fire({
    title: 'Descarga Exitosa',
    text: 'El análisis se ha descargado correctamente',
    icon: 'success',
    timer: 2000,
    showConfirmButton: false
  });
}

/**
 * Cierra el modal de balance
 */
function cerrarModalBalance() {
  const modalElement = document.getElementById('modalBalance');
  const modal = bootstrap.Modal.getInstance(modalElement);
  if (modal) {
    modal.hide();
  }
  window.balanceActual = null;
}

/**
 * Imprime el balance
 */
function imprimirBalance() {
  window.print();
}

/**
 * Exporta el balance a Excel
 */
function exportarBalanceExcel() {
  if (!window.balanceActual) {
    Swal.fire({
      icon: 'warning',
      title: 'Sin Datos',
      text: 'No hay balance cargado para exportar',
      confirmButtonText: 'Entendido'
    });
    return;
  }

  const { empresaRut, metadata } = window.balanceActual;

  Swal.fire({
    title: 'Exportando a Excel...',
    text: 'Generando archivo, por favor espera',
    allowOutsideClick: false,
    didOpen: () => {
      Swal.showLoading();
    }
  });

  fetch('/ia/exportar-balance-excel', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': window.csrfToken || getCSRFToken()
    },
    body: JSON.stringify({
      empresa_rut: empresaRut,
      periodo_inicio: metadata.periodo_inicio,
      periodo_fin: metadata.periodo_fin,
      tipo_balance: metadata.tipo_balance || 'Mensual'
    })
  })
    .then(response => {
      if (!response.ok) throw new Error('Error al generar Excel');
      return response.blob();
    })
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Balance_${window.balanceActual.empresaNombre.replace(/\s+/g, '_')}_${metadata.periodo_inicio}_${metadata.periodo_fin}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      Swal.fire({
        icon: 'success',
        title: 'Exportación Exitosa',
        text: 'El archivo Excel se ha descargado correctamente',
        timer: 2000,
        showConfirmButton: false
      });
    })
    .catch(error => {
      console.error('Error al exportar:', error);
      Swal.fire({
        icon: 'error',
        title: 'Error al Exportar',
        text: 'No se pudo generar el archivo Excel',
        confirmButtonText: 'Entendido'
      });
    });
}

// Exportar funciones globales adicionales
window.generarBalanceCompleto = generarBalanceCompleto;
window.analizarBalanceConIA = analizarBalanceConIA;
window.mostrarBalanceEnModal = mostrarBalanceEnModal;
window.analizarBalanceEnModal = analizarBalanceEnModal;
window.cerrarAnalisisIA = cerrarAnalisisIA;
window.descargarAnalisisDesdeModal = descargarAnalisisDesdeModal;
window.cerrarModalBalance = cerrarModalBalance;
window.imprimirBalance = imprimirBalance;
window.exportarBalanceExcel = exportarBalanceExcel;
