/**
 * Scripts Globales para Evolve Soluciones
 * =======================================
 *
 * Funcionalidades JavaScript comunes a toda la aplicación
 */

console.log(' Cargando scripts globales de Evolve Soluciones...');

// Configuración global
window.EvolveApp = {
    version: '1.0.0',
    debug: true,
    apiEndpoints: {
        base: '/api',
        auth: '/auth/api',
        consulta: '/consulta-integral-f29/api'
    }
};

/**
 * Utilidades generales
 */
const Utils = {
    /**
     * Formatea un número como moneda chilena
     */
    formatearMoneda: function (numero) {
        if (numero === null || numero === undefined) return '$0';
        return new Intl.NumberFormat('es-CL', {
            style: 'currency',
            currency: 'CLP',
            minimumFractionDigits: 0
        }).format(numero);
    },

    /**
     * Formatea una fecha
     */
    formatearFecha: function (fecha, formato = 'dd/mm/yyyy') {
        if (!fecha) return '-';

        const fechaObj = new Date(fecha);
        if (isNaN(fechaObj.getTime())) return '-';

        const opciones = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        };

        if (formato.includes('hh:mm')) {
            opciones.hour = '2-digit';
            opciones.minute = '2-digit';
        }

        return fechaObj.toLocaleDateString('es-CL', opciones);
    },

    /**
     * Debounce para optimizar eventos
     */
    debounce: function (func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Muestra notificación toast
     */
    mostrarToast: function (mensaje, tipo = 'info') {
        const toast = this.crearToast(mensaje, tipo);
        document.body.appendChild(toast);

        // Mostrar toast
        setTimeout(() => toast.classList.add('show'), 100);

        // Ocultar automáticamente
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    },

    /**
     * Crea elemento toast
     */
    crearToast: function (mensaje, tipo) {
        const iconos = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-triangle',
            warning: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle'
        };

        const colores = {
            success: 'success',
            error: 'danger',
            warning: 'warning',
            info: 'info'
        };

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${colores[tipo]} border-0 position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="${iconos[tipo]} me-2"></i>
                    ${mensaje}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.closest('.toast').remove()"></button>
            </div>
        `;

        return toast;
    },

    /**
     * Confirma acción con modal
     */
    confirmarAccion: function (titulo, mensaje, callback) {
        const modal = this.crearModalConfirmacion(titulo, mensaje, callback);
        document.body.appendChild(modal);

        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();

        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    },

    /**
     * Crea modal de confirmación
     */
    crearModalConfirmacion: function (titulo, mensaje, callback) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-question-circle text-warning me-2"></i>
                            ${titulo}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${mensaje}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-1"></i>
                            Cancelar
                        </button>
                        <button type="button" class="btn btn-primary" id="confirmarBtn">
                            <i class="fas fa-check me-1"></i>
                            Confirmar
                        </button>
                    </div>
                </div>
            </div>
        `;

        modal.querySelector('#confirmarBtn').addEventListener('click', () => {
            bootstrap.Modal.getInstance(modal).hide();
            if (callback) callback();
        });

        return modal;
    },

    /**
     * Muestra overlay de carga
     */
    mostrarCarga: function (mensaje = 'Cargando...') {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.querySelector('.loading-text').textContent = mensaje;
            overlay.style.display = 'flex';
        } else {
            this.crearOverlayCarga(mensaje);
        }
    },

    /**
     * Oculta overlay de carga
     */
    ocultarCarga: function () {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    },

    /**
     * Crea overlay de carga
     */
    crearOverlayCarga: function (mensaje) {
        const overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="spinner-custom mb-3"></div>
                <div class="loading-text">${mensaje}</div>
            </div>
        `;
        document.body.appendChild(overlay);
    }
};

/**
 * Manejo de errores AJAX
 */
const ErrorHandler = {
    /**
     * Maneja errores de peticiones AJAX
     */
    manejarErrorAjax: function (xhr, status, error) {
        console.error('Error AJAX:', { xhr, status, error });

        let mensaje = 'Ha ocurrido un error inesperado.';

        if (xhr.status === 401) {
            mensaje = 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.';
            setTimeout(() => {
                window.location.href = '/auth/iniciar-sesion';
            }, 2000);
        } else if (xhr.status === 403) {
            mensaje = 'No tienes permisos para realizar esta acción.';
        } else if (xhr.status === 404) {
            mensaje = 'El recurso solicitado no fue encontrado.';
        } else if (xhr.status === 500) {
            mensaje = 'Error interno del servidor. Intenta nuevamente.';
        } else if (xhr.responseJSON && xhr.responseJSON.error) {
            mensaje = xhr.responseJSON.error;
        }

        Utils.mostrarToast(mensaje, 'error');
    }
};

/**
 * Validaciones del lado cliente
 */
const Validaciones = {
    /**
     * Valida email
     */
    validarEmail: function (email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    },

    /**
     * Valida RUT chileno
     */
    validarRut: function (rut) {
        if (!rut) return false;

        // Limpiar RUT
        const rutLimpio = rut.replace(/[.\-]/g, '').toUpperCase();

        // Validar formato
        if (!/^\d{7,8}[0-9K]$/.test(rutLimpio)) return false;

        // Calcular dígito verificador
        const numero = rutLimpio.slice(0, -1);
        const dv = rutLimpio.slice(-1);

        let suma = 0;
        let multiplicador = 2;

        for (let i = numero.length - 1; i >= 0; i--) {
            suma += parseInt(numero[i]) * multiplicador;
            multiplicador = multiplicador === 7 ? 2 : multiplicador + 1;
        }

        const resto = suma % 11;
        const dvCalculado = resto === 1 ? 'K' : resto === 0 ? '0' : (11 - resto).toString();

        return dv === dvCalculado;
    },

    /**
     * Valida contraseña
     */
    validarContraseña: function (contraseña) {
        if (!contraseña || contraseña.length < 8) return false;

        const tieneMinuscula = /[a-z]/.test(contraseña);
        const tieneMayuscula = /[A-Z]/.test(contraseña);
        const tieneNumero = /\d/.test(contraseña);

        return tieneMinuscula && tieneMayuscula && tieneNumero;
    }
};

/**
 * Funciones de inicialización
 */
const App = {
    /**
     * Inicializa la aplicación
     */
    init: function () {
        console.log('🎯 Inicializando aplicación Evolve Soluciones...');

        this.configurarAjax();
        this.configurarEventosGlobales();
        this.verificarSesion();

        console.log(' Aplicación inicializada correctamente');
    },

    /**
     * Configura peticiones AJAX globales
     */
    configurarAjax: function () {
        // Configurar timeout por defecto
        $.ajaxSetup({
            timeout: 30000,
            error: ErrorHandler.manejarErrorAjax
        });

        // Mostrar/ocultar indicador de carga en peticiones AJAX
        $(document).ajaxStart(function () {
            Utils.mostrarCarga();
        });

        $(document).ajaxStop(function () {
            Utils.ocultarCarga();
        });
    },

    /**
     * Configura eventos globales
     */
    configurarEventosGlobales: function () {
        // Confirmar enlaces de eliminación
        $(document).on('click', '[data-confirm]', function (e) {
            e.preventDefault();
            const mensaje = $(this).data('confirm') || '¿Estás seguro?';
            const href = $(this).attr('href');

            Utils.confirmarAccion('Confirmar acción', mensaje, function () {
                window.location.href = href;
            });
        });

        // Auto-ocultar alertas
        $('.alert').each(function () {
            const alert = this;
            setTimeout(() => {
                $(alert).fadeOut();
            }, 5000);
        });

        // Tooltips de Bootstrap
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },

    /**
     * Verifica estado de la sesión
     */
    verificarSesion: function () {
        // Solo verificar si el usuario está autenticado
        if (!document.querySelector('.navbar')) return;

        setInterval(() => {
            fetch('/auth/api/verificar-sesion')
                .then(response => {
                    if (!response.ok && response.status === 401) {
                        Utils.mostrarToast('Tu sesión ha expirado. Redirigiendo...', 'warning');
                        setTimeout(() => {
                            window.location.href = '/auth/iniciar-sesion';
                        }, 2000);
                    }
                })
                .catch(error => {
                    console.warn('No se pudo verificar la sesión:', error);
                });
        }, 300000); // Verificar cada 5 minutos
    }
};

// Hacer utilidades disponibles globalmente
window.Utils = Utils;
window.ErrorHandler = ErrorHandler;
window.Validaciones = Validaciones;
window.EvolveApp.App = App;

// Inicializar cuando el DOM esté listo
$(document).ready(function () {
    App.init();
});

// Log de carga completada
console.log(' Scripts globales de Evolve Soluciones cargados correctamente');
