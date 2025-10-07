/**
 * Script para Limpiar Cookies Automáticamente después de Error CSRF
 * ===================================================================
 *
 * Este script se ejecuta en la página de login cuando hay un error CSRF.
 * Limpia automáticamente todas las cookies y storage del navegador
 * para resolver problemas de sesión corrupta.
 *
 * Se activa cuando la URL contiene el parámetro: ?limpiar_cookies=1
 *
 * @author Evolve Soluciones
 * @date 2025-10-07
 */

(function () {
  'use strict';

  /**
   * Limpia todas las cookies del dominio actual
   */
  function limpiarTodasLasCookies() {
    const cookies = document.cookie.split(";");
    let cookiesLimpiadas = 0;

    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i];
      const eqPos = cookie.indexOf("=");
      const name = eqPos > -1 ? cookie.substr(0, eqPos).trim() : cookie.trim();

      if (!name) continue;

      // Eliminar cookie para el dominio actual
      document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";

      // Eliminar para el dominio específico
      document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=" + window.location.hostname;

      // Eliminar para subdominios (ej: .evolveasesores.cl)
      const domainParts = window.location.hostname.split('.');
      if (domainParts.length >= 2) {
        const rootDomain = domainParts.slice(-2).join('.');
        document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=." + rootDomain;
      }

      cookiesLimpiadas++;
    }

    return cookiesLimpiadas;
  }

  /**
   * Limpia sessionStorage y localStorage
   */
  function limpiarStorage() {
    try {
      // Limpiar todo el sessionStorage
      sessionStorage.clear();

      // Limpiar items específicos del localStorage
      const itemsALimpiar = ['session_token', 'user_data', 'csrf_token'];
      itemsALimpiar.forEach(item => {
        localStorage.removeItem(item);
      });

      console.log('[CSRF Fix] Storage limpiado exitosamente');
      return true;
    } catch (e) {
      console.warn('[CSRF Fix] No se pudo limpiar storage:', e);
      return false;
    }
  }

  /**
   * Muestra un mensaje temporal al usuario
   */
  function mostrarMensajeTemporal(mensaje, tipo = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo} alert-dismissible fade show`;
    alertDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    alertDiv.innerHTML = `
            <i class="fas fa-${tipo === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
            ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

    document.body.appendChild(alertDiv);

    // Auto-cerrar después de 3 segundos
    setTimeout(() => {
      alertDiv.remove();
    }, 3000);
  }

  /**
   * Función principal que ejecuta la limpieza
   */
  function ejecutarLimpiezaCSRF() {
    // Verificar si se debe limpiar cookies
    const urlParams = new URLSearchParams(window.location.search);
    const limpiarCookies = urlParams.get('limpiar_cookies');

    if (limpiarCookies !== '1') {
      return; // No hacer nada si no hay parámetro
    }

    console.log('[CSRF Fix] Iniciando limpieza automática de sesión...');

    // Mostrar indicador visual
    mostrarMensajeTemporal('Limpiando sesión corrupta...', 'info');

    // Limpiar cookies
    const cookiesLimpiadas = limpiarTodasLasCookies();
    console.log(`[CSRF Fix] ${cookiesLimpiadas} cookies eliminadas`);

    // Limpiar storage
    limpiarStorage();

    // Esperar un momento para que se vean los cambios
    setTimeout(function () {
      console.log('[CSRF Fix] Limpieza completada. Recargando página...');

      // Redirigir a la URL limpia (sin parámetros)
      const urlLimpia = window.location.pathname;
      window.location.replace(urlLimpia);
    }, 800);
  }

  // Ejecutar cuando el DOM esté listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ejecutarLimpiezaCSRF);
  } else {
    // DOM ya está listo, ejecutar inmediatamente
    ejecutarLimpiezaCSRF();
  }

})();
