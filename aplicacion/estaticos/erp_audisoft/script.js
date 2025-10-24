class ReporteImpuestosApp {
  constructor() {
    this.initializeElements();
    this.bindEvents();
    this.lastReportData = null;
  }

  initializeElements() {
    this.elements = {
      periodoInput: document.getElementById('periodo'),
      generateButton: document.getElementById('generateReport'),
      assignDataButton: document.getElementById('assignData'),
      assignPaymentsButton: document.getElementById('assignPayments'),
      loading: document.getElementById('loading'),
      errorMessage: document.getElementById('errorMessage'),
      errorText: document.getElementById('errorText'),
      resultsSection: document.getElementById('resultsSection'),
      tableHead: document.getElementById('tableHead'),
      tableBody: document.getElementById('tableBody'),
      periodoInfo: document.getElementById('periodoInfo'),
      fechaGeneracion: document.getElementById('fechaGeneracion'),
      exportCSV: document.getElementById('exportCSV'),
      printReport: document.getElementById('printReport')
    };
  }

  bindEvents() {
    // Mostrar modal de mantenimiento en lugar de ejecutar generateReport
    this.elements.generateButton.addEventListener('click', () => this.showMaintenanceModal());
    this.elements.assignDataButton.addEventListener('click', () => this.assignData());
    this.elements.assignPaymentsButton.addEventListener('click', () => this.assignPayments());
    this.elements.periodoInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        this.showMaintenanceModal();
      }
    });
    this.elements.periodoInput.addEventListener('input', (e) => this.formatPeriodoInput(e));
    this.elements.exportCSV.addEventListener('click', () => this.exportToCSV());
    this.elements.printReport.addEventListener('click', () => this.printReport());
  }

  formatPeriodoInput(e) {
    // Solo permitir números
    e.target.value = e.target.value.replace(/[^0-9]/g, '');

    // Limitar a 6 caracteres
    if (e.target.value.length > 6) {
      e.target.value = e.target.value.substr(0, 6);
    }
  }

  validatePeriodo(periodo) {
    if (!periodo || periodo.length !== 6) {
      return 'El período debe tener exactamente 6 dígitos (YYYYMM)';
    }

    const year = parseInt(periodo.substr(0, 4));
    const month = parseInt(periodo.substr(4, 2));

    if (year < 2000 || year > 2030) {
      return 'El año debe estar entre 2000 y 2030';
    }

    if (month < 1 || month > 12) {
      return 'El mes debe estar entre 01 y 12';
    }

    return null;
  }

  async generateReport() {
    const periodo = this.elements.periodoInput.value.trim();

    // Validar período
    const validationError = this.validatePeriodo(periodo);
    if (validationError) {
      this.showError(validationError);
      return;
    }

    this.showLoading();
    this.hideError();
    this.hideResults();

    try {
      const response = await fetch('/api/reporte-impuestos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ periodo })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Error en la respuesta del servidor');
      }

      if (result.success) {
        this.lastReportData = result;
        this.displayResults(result);
      } else {
        throw new Error(result.error || 'Error desconocido');
      }

    } catch (error) {
      console.error('Error al generar reporte:', error);
      this.showError(`Error al generar el reporte: ${error.message}`);
    } finally {
      this.hideLoading();
    }
  }

  async assignData() {
    const confirmed = confirm('¿Confirma ejecutar la Asignación de Datos en la base de datos? Esto modificará registros.');
    if (!confirmed) return;

    this.showLoading();
    this.hideError();

    try {
      const response = await fetch('/api/asignacion-datos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Error al ejecutar la asignación');

      if (result.success) {
        alert('Asignación completada: ' + (result.message || 'OK'));
      } else {
        throw new Error(result.error || 'Fallo en la asignación');
      }

    } catch (err) {
      console.error('Error en asignación de datos:', err);
      this.showError('Error en Asignación de Datos: ' + err.message);
    } finally {
      this.hideLoading();
    }
  }

  async assignPayments() {
    const confirmed = confirm('\u00bfConfirma ejecutar la asignaci\u00f3n de datos de pagos? Esto modific\u00e1 registros.');
    if (!confirmed) return;

    this.showLoading();
    this.hideError();

    try {
      const response = await fetch('/api/asignacion-pagos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Error al ejecutar la asignaci\u00f3n de pagos');

      if (result.success) {
        alert('Asignaci\u00f3n de pagos completada: ' + (result.message || 'OK'));
      } else {
        throw new Error(result.error || 'Fallo en la asignaci\u00f3n de pagos');
      }

    } catch (err) {
      console.error('Error en asignaci\u00f3n de pagos:', err);
      this.showError('Error en Asignaci\u00f3n de Pagos: ' + err.message);
    } finally {
      this.hideLoading();
    }
  }

  displayResults(data) {
    if (!data.data || data.data.length === 0) {
      this.showError('No se encontraron datos para el período especificado');
      return;
    }

    // Actualizar información del reporte
    this.elements.periodoInfo.textContent = `Período: ${this.formatPeriodo(data.periodo)}`;
    this.elements.fechaGeneracion.textContent = `Generado: ${this.formatDate(data.fecha_generacion)}`;

    // Generar tabla
    this.generateTable(data.data);

    // Mostrar resultados con animación
    this.showResults();
  }

  generateTable(data) {
    // Limpiar tabla
    this.elements.tableHead.innerHTML = '';
    this.elements.tableBody.innerHTML = '';

    if (data.length === 0) return;

    // Obtener columnas (claves del primer objeto)
    const originalColumns = Object.keys(data[0]);

    // Reorganizar columnas: primera columna (nombre_impuesto_tipo) se mantiene, el resto se invierte
    const typeColumn = 'nombre_impuesto_tipo';
    const otherColumns = originalColumns.filter(col => col !== typeColumn).reverse(); // Filtrar y luego invertir
    const columns = [typeColumn, ...otherColumns];

    // Generar encabezados
    const headerRow = document.createElement('tr');
    columns.forEach(column => {
      const th = document.createElement('th');
      th.textContent = this.formatColumnName(column);
      headerRow.appendChild(th);
    });
    this.elements.tableHead.appendChild(headerRow);

    // Generar filas de datos
    data.forEach(row => {
      const tr = document.createElement('tr');
      const rowType = row['nombre_impuesto_tipo']; // Usar directamente la clave específica

      columns.forEach((column, index) => {
        const td = document.createElement('td');
        const value = row[column];

        if (column === 'nombre_impuesto_tipo') {
          // Columna del tipo de impuesto
          td.textContent = value || '';
          td.style.fontWeight = '600';
        } else {
          // Columnas numéricas
          td.className = 'numeric';
          if (value !== null && value !== undefined) {
            const numValue = parseFloat(value);
            if (!isNaN(numValue)) {
              // Verificar si es una fila que debe mostrarse como número puro
              if (this.isCountField(rowType)) {
                td.textContent = this.formatCount(numValue);
                td.classList.add('count-field'); // Clase específica para campos de conteo
                td.classList.remove('positive', 'negative'); // Remover clases de color
              } else {
                td.textContent = this.formatNumber(numValue);
                if (numValue < 0) {
                  td.classList.add('negative');
                } else if (numValue > 0) {
                  td.classList.add('positive');
                }
              }
            } else {
              td.textContent = value;
            }
          } else {
            td.textContent = '-';
          }
        }

        tr.appendChild(td);
      });
      this.elements.tableBody.appendChild(tr);
    });
  }

  isCountField(rowType) {
    // Verificar si es un tipo de fila que debe mostrarse como número puro
    if (!rowType) return false;

    const countFields = [
      'Q Doctos. Compras del Mes',
      'Compras sin detalle'
    ];

    // Comparación exacta y también por inclusión para mayor robustez
    return countFields.some(field =>
      rowType === field ||
      rowType.includes('Doctos') ||
      rowType.includes('sin detalle')
    );
  }

  formatCount(number) {
    // Formatear como número entero sin símbolo de moneda
    return new Intl.NumberFormat('es-CL', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(number);
  }

  formatColumnName(columnName) {
    if (columnName === 'nombre_impuesto_tipo') {
      return 'Tipo de Impuesto';
    }
    return columnName;
  }

  formatNumber(number) {
    return '$' + new Intl.NumberFormat('es-CL', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(Math.abs(number)) + (number < 0 ? ' (-)' : '');
  }

  formatPeriodo(periodo) {
    if (periodo && periodo.length === 6) {
      const year = periodo.substr(0, 4);
      const month = periodo.substr(4, 2);
      const monthNames = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
      ];
      return `${monthNames[parseInt(month) - 1]} ${year}`;
    }
    return periodo;
  }

  formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('es-CL', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  exportToCSV() {
    if (!this.lastReportData || !this.lastReportData.data) {
      this.showError('No hay datos para exportar');
      return;
    }

    const data = this.lastReportData.data;
    if (data.length === 0) return;

    // Generar CSV
    const columns = Object.keys(data[0]);
    const csvHeader = columns.map(col => this.formatColumnName(col)).join(',');

    const csvRows = data.map(row => {
      return columns.map(column => {
        const value = row[column];
        if (value === null || value === undefined) return '';
        if (typeof value === 'string' && value.includes(',')) {
          return `"${value}"`;
        }
        return value;
      }).join(',');
    });

    const csvContent = [csvHeader, ...csvRows].join('\n');

    // Descargar archivo
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `reporte_impuestos_${this.lastReportData.periodo}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  printReport() {
    window.print();
  }

  showLoading() {
    this.elements.loading.style.display = 'block';
    this.elements.loading.classList.add('fade-in');
    this.elements.generateButton.disabled = true;
  }

  hideLoading() {
    this.elements.loading.style.display = 'none';
    this.elements.generateButton.disabled = false;
  }

  showError(message) {
    this.elements.errorText.textContent = message;
    this.elements.errorMessage.style.display = 'flex';
    this.elements.errorMessage.classList.add('fade-in');
  }

  hideError() {
    this.elements.errorMessage.style.display = 'none';
  }

  showResults() {
    this.elements.resultsSection.style.display = 'block';
    this.elements.resultsSection.classList.add('fade-in');
  }

  hideResults() {
    this.elements.resultsSection.style.display = 'none';
  }

  showMaintenanceModal() {
    const modal = document.getElementById('maintenanceModal');
    if (!modal) return;
    modal.style.display = 'flex';
    const closeBtn = document.getElementById('closeMaintenance');
    if (closeBtn) {
      closeBtn.onclick = () => { modal.style.display = 'none'; };
    }
  }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
  new ReporteImpuestosApp();
});

// Función auxiliar para manejar errores globales
window.addEventListener('error', (event) => {
  console.error('Error global:', event.error);
});

// Función auxiliar para manejar promesas rechazadas
window.addEventListener('unhandledrejection', (event) => {
  console.error('Promesa rechazada:', event.reason);
});
