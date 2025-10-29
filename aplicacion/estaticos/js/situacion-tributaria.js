document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('formBusqueda');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    // Dejar que el GET haga el render lado servidor
    // Aquí podríamos hacer fetch a /api si se quiere SPA
  });
});


