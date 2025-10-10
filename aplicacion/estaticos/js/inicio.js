/**
 * Inicio - JavaScript
 * Funcionalidades para la página de inicio de Evolve Soluciones
 */

console.log('Cargando inicio.js...');

// ============================================
// CALENDARIO DINÁMICO
// ============================================
let mesActual = new Date().getMonth();
let añoActual = new Date().getFullYear();
const diaHoy = new Date().getDate();
const mesHoy = new Date().getMonth();
const añoHoy = new Date().getFullYear();

const mesesNombres = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

/**
 * Genera el calendario para el mes y año especificados
 * @param {number} mes - Mes (0-11)
 * @param {number} año - Año (ej: 2025)
 */
function generarCalendario(mes, año) {
  const calendarioGrid = document.getElementById('calendario-grid');
  const calendarioTitulo = document.getElementById('calendario-titulo');

  if (!calendarioGrid || !calendarioTitulo) {
    console.error('Elementos del calendario no encontrados');
    return;
  }

  // Limpiar grid
  calendarioGrid.innerHTML = '';

  // Actualizar título
  calendarioTitulo.textContent = `${mesesNombres[mes]} ${año}`;

  // Primer día del mes y último día del mes
  const primerDia = new Date(año, mes, 1).getDay();
  const ultimoDia = new Date(año, mes + 1, 0).getDate();
  const ultimoDiaMesAnterior = new Date(año, mes, 0).getDate();

  // Días del mes anterior
  for (let i = primerDia - 1; i >= 0; i--) {
    const dia = ultimoDiaMesAnterior - i;
    const divDia = document.createElement('div');
    divDia.className = 'calendario-dia otro-mes';
    divDia.textContent = dia;
    calendarioGrid.appendChild(divDia);
  }

  // Días del mes actual
  for (let dia = 1; dia <= ultimoDia; dia++) {
    const divDia = document.createElement('div');
    divDia.className = 'calendario-dia';
    divDia.textContent = dia;

    // Marcar el día actual
    if (dia === diaHoy && mes === mesHoy && año === añoHoy) {
      divDia.classList.add('hoy');
      divDia.title = 'Hoy';
    }

    calendarioGrid.appendChild(divDia);
  }

  // Días del mes siguiente para completar la cuadrícula
  const diasMostrados = primerDia + ultimoDia;
  const diasFaltantes = 42 - diasMostrados; // 6 semanas * 7 días

  for (let dia = 1; dia <= diasFaltantes; dia++) {
    const divDia = document.createElement('div');
    divDia.className = 'calendario-dia otro-mes';
    divDia.textContent = dia;
    calendarioGrid.appendChild(divDia);
  }

  console.log(`Calendario generado: ${mesesNombres[mes]} ${año}`);
}

/**
 * Navega al mes anterior
 */
function mesAnterior() {
  mesActual--;
  if (mesActual < 0) {
    mesActual = 11;
    añoActual--;
  }
  generarCalendario(mesActual, añoActual);
}

/**
 * Navega al mes siguiente
 */
function mesSiguiente() {
  mesActual++;
  if (mesActual > 11) {
    mesActual = 0;
    añoActual++;
  }
  generarCalendario(mesActual, añoActual);
}

// ============================================
// INICIALIZACIÓN
// ============================================

/**
 * Inicializa el dashboard al cargar la página
 */
document.addEventListener('DOMContentLoaded', function () {
  console.log('Inicializando Dashboard...');

  // Inicializar calendario
  generarCalendario(mesActual, añoActual);

  // Event listeners para botones de navegación del calendario
  const btnMesAnterior = document.getElementById('btn-mes-anterior');
  const btnMesSiguiente = document.getElementById('btn-mes-siguiente');

  if (btnMesAnterior) {
    btnMesAnterior.addEventListener('click', mesAnterior);
    console.log('Event listener agregado: btn-mes-anterior');
  }

  if (btnMesSiguiente) {
    btnMesSiguiente.addEventListener('click', mesSiguiente);
    console.log('Event listener agregado: btn-mes-siguiente');
  }

  console.log('Dashboard inicializado correctamente');
});

// ============================================
// AUTO-REFRESH
// ============================================

/**
 * Auto-refresh cada 5 minutos para mantener datos actualizados
 */
setTimeout(function () {
  console.log('Recargando dashboard para actualizar datos...');
  location.reload();
}, 300000); // 5 minutos

// ============================================
// FUNCIONES GLOBALES
// ============================================

// Hacer funciones disponibles globalmente
window.generarCalendario = generarCalendario;
window.mesAnterior = mesAnterior;
window.mesSiguiente = mesSiguiente;

console.log('inicio.js cargado correctamente');
