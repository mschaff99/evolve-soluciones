import { useState } from 'react';
import PageHeader from '../../components/ui/PageHeader';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import api from '../../api/client';

export default function IADashboard() {
  const [rut, setRut] = useState('');
  const [anioInicio, setAnioInicio] = useState(2024);
  const [mesInicio, setMesInicio] = useState(1);
  const [anioFin, setAnioFin] = useState(2024);
  const [mesFin, setMesFin] = useState(12);
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [step, setStep] = useState<'form' | 'balance' | 'analisis'>('form');
  const [balanceData, setBalanceData] = useState<Record<string, unknown> | null>(null);

  const generarBalance = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/ia/generar-balance', {
        empresa_rut: rut,
        anio_inicio: anioInicio,
        mes_inicio: mesInicio,
        anio_fin: anioFin,
        mes_fin: mesFin,
      });
      if (res.data.exito) {
        setBalanceData(res.data.datos);
        setStep('balance');
      } else {
        setError(res.data.mensaje);
      }
    } catch {
      setError('Error al generar balance');
    } finally {
      setLoading(false);
    }
  };

  const analizarBalance = async () => {
    if (!balanceData) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/ia/analizar-balance', {
        empresa_rut: rut,
        datos_balance: balanceData,
        tipo_analisis: 'general',
      });
      if (res.data.exito) {
        setResultado(res.data.analisis);
        setStep('analisis');
      } else {
        setError(res.data.mensaje);
      }
    } catch {
      setError('Error al analizar balance');
    } finally {
      setLoading(false);
    }
  };

  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ];

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Inteligencia Artificial"
        subtitle="Analisis de balances con IA (Gemini)"
        icon="fas fa-robot"
      />

      {error && (
        <div className="alert alert-danger mb-2">
          <i className="fas fa-exclamation-circle" style={{ marginRight: '8px' }} />
          {error}
        </div>
      )}

      {step === 'form' && (
        <div className="card">
          <div className="card-header">
            <h3 style={{ fontSize: '18px', fontWeight: 600, margin: 0 }}>
              <i className="fas fa-calculator" style={{ marginRight: '10px', color: 'var(--color-primary)' }} />
              Generar Balance de 8 Columnas
            </h3>
          </div>
          <div className="card-body">
            <div className="form-group">
              <label className="form-label">RUT Empresa</label>
              <div className="form-control-icon">
                <i className="fas fa-building icon" />
                <input className="form-control font-mono" value={rut} onChange={(e) => setRut(e.target.value)} placeholder="76.123.456-7" />
              </div>
            </div>

            <div className="grid grid-2">
              <div>
                <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '12px' }}>
                  Periodo Inicio
                </h4>
                <div className="grid grid-2">
                  <div className="form-group">
                    <label className="form-label">Ano</label>
                    <input className="form-control" type="number" value={anioInicio} onChange={(e) => setAnioInicio(+e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Mes</label>
                    <select className="form-control form-select" value={mesInicio} onChange={(e) => setMesInicio(+e.target.value)}>
                      {meses.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
                    </select>
                  </div>
                </div>
              </div>
              <div>
                <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '12px' }}>
                  Periodo Fin
                </h4>
                <div className="grid grid-2">
                  <div className="form-group">
                    <label className="form-label">Ano</label>
                    <input className="form-control" type="number" value={anioFin} onChange={(e) => setAnioFin(+e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Mes</label>
                    <select className="form-control form-select" value={mesFin} onChange={(e) => setMesFin(+e.target.value)}>
                      {meses.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <div style={{ marginTop: '24px' }}>
              <button className="btn btn-gradient btn-lg" onClick={generarBalance} disabled={loading || !rut}>
                {loading ? (
                  <><div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px' }} /> Generando...</>
                ) : (
                  <><i className="fas fa-cogs" /> Generar Balance</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {step === 'balance' && balanceData && (
        <div className="card">
          <div className="card-header flex-between">
            <h3 style={{ fontSize: '18px', fontWeight: 600, margin: 0 }}>
              <i className="fas fa-table" style={{ marginRight: '10px', color: 'var(--color-teal)' }} />
              Balance Generado
            </h3>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="btn btn-outline btn-sm" onClick={() => setStep('form')}>
                <i className="fas fa-arrow-left" /> Volver
              </button>
              <button className="btn btn-gradient btn-sm" onClick={analizarBalance} disabled={loading}>
                {loading ? 'Analizando...' : <><i className="fas fa-robot" /> Analizar con IA</>}
              </button>
            </div>
          </div>
          <div className="card-body" style={{ maxHeight: '500px', overflowY: 'auto' }}>
            <pre style={{
              background: 'var(--bg-tertiary)',
              padding: '20px',
              borderRadius: '12px',
              color: 'var(--text-primary)',
              fontSize: '13px',
              overflow: 'auto',
              fontFamily: 'var(--font-mono)',
            }}>
              {JSON.stringify(balanceData, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {step === 'analisis' && resultado && (
        <div className="card">
          <div className="card-header flex-between">
            <h3 style={{ fontSize: '18px', fontWeight: 600, margin: 0 }}>
              <i className="fas fa-brain" style={{ marginRight: '10px', color: 'var(--color-cyan)' }} />
              Analisis IA
            </h3>
            <button className="btn btn-outline btn-sm" onClick={() => { setStep('form'); setResultado(null); setBalanceData(null); }}>
              <i className="fas fa-redo" /> Nuevo Analisis
            </button>
          </div>
          <div className="card-body">
            <div style={{
              background: 'var(--bg-tertiary)',
              padding: '24px',
              borderRadius: '16px',
              lineHeight: 1.8,
              fontSize: '15px',
              whiteSpace: 'pre-wrap',
            }}>
              {resultado}
            </div>
          </div>
        </div>
      )}

      {loading && step !== 'form' && <LoadingSpinner text="Procesando con Inteligencia Artificial..." />}
    </div>
  );
}
