export default function LoadingSpinner({ text = 'Cargando...' }: { text?: string }) {
  return (
    <div className="loading-container">
      <div className="spinner" />
      <p>{text}</p>
    </div>
  );
}
