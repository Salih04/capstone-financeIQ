import { useNavigate } from 'react-router-dom'
import { BrainCircuit, ArrowRight } from 'lucide-react'

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'var(--bg-deep)', padding: '2rem' }}>
      <div style={{ maxWidth: 760, width: '100%', background: 'var(--surface-1)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-xl)', padding: '2rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--primary)', fontWeight: 700, marginBottom: 10 }}>
          <BrainCircuit size={16} />
          Success DNA Forecasting
        </div>
        <h1 style={{ margin: 0, fontSize: '2rem', color: 'var(--text-1)', letterSpacing: '-0.6px' }}>Find future opportunities from proven winners</h1>
        <p style={{ fontSize: 14, color: 'var(--text-3)', marginTop: 10, lineHeight: 1.6 }}>
          The system learns only from successful stocks by sector and year, extracts robust parameters, and produces ranked opportunities with clear explanations.
        </p>
        <div style={{ display: 'flex', gap: 10, marginTop: 18 }}>
          <button
            onClick={() => navigate('/onboarding')}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              border: 'none', borderRadius: 'var(--radius-md)', background: 'var(--primary)', color: '#fff',
              padding: '10px 16px', fontWeight: 700, cursor: 'pointer',
            }}
          >
            Start Analysis <ArrowRight size={14} />
          </button>
          <button
            onClick={() => navigate('/login')}
            style={{ border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)', background: 'var(--surface-2)', color: 'var(--text-1)', padding: '10px 16px', cursor: 'pointer' }}
          >
            Login
          </button>
        </div>
      </div>
    </div>
  )
}
