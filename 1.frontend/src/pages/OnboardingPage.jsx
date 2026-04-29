import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const inputS = {
  width: '100%',
  boxSizing: 'border-box',
  background: 'var(--surface-1)',
  border: '1px solid var(--border-strong)',
  borderRadius: 'var(--radius-md)',
  color: 'var(--text-1)',
  padding: '10px 12px',
  fontSize: 13,
  outline: 'none',
}

export default function OnboardingPage() {
  const { isAuth, updateProfile } = useAuth()
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [userType, setUserType] = useState('individual')
  const [riskLevel, setRiskLevel] = useState('medium')
  const [investmentScope, setInvestmentScope] = useState('')
  const [sectorFocus, setSectorFocus] = useState('')
  const [msg, setMsg] = useState('')

  const finish = async () => {
    if (!isAuth) {
      navigate('/login')
      return
    }
    try {
      await updateProfile({
        user_type: userType,
        risk_level: riskLevel,
        investment_scope: investmentScope ? parseFloat(investmentScope) : null,
        sector_focus: sectorFocus || null,
      })
      navigate('/forecasting')
    } catch (e) {
      setMsg(e.response?.data?.detail || 'Profile setup failed.')
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'var(--bg-deep)', padding: '2rem' }}>
      <div style={{ width: '100%', maxWidth: 640, background: 'var(--surface-1)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-xl)', padding: '1.5rem' }}>
        <div style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 8 }}>Step {step} / 3</div>
        <h1 style={{ margin: 0, color: 'var(--text-1)', fontSize: '1.45rem' }}>Start Analysis Setup</h1>

        {msg && <div style={{ marginTop: 12, fontSize: 13, color: '#fca5a5' }}>{msg}</div>}

        {step === 1 && (
          <div style={{ marginTop: 14 }}>
            <label style={{ fontSize: 12, color: 'var(--text-3)' }}>User Type</label>
            <select value={userType} onChange={(e) => setUserType(e.target.value)} style={{ ...inputS, marginTop: 6 }}>
              <option value="individual">Individual</option>
              <option value="advanced">Advanced</option>
              <option value="corporate">Corporate</option>
            </select>
          </div>
        )}

        {step === 2 && (
          <div style={{ marginTop: 14 }}>
            <label style={{ fontSize: 12, color: 'var(--text-3)' }}>Risk Level</label>
            <select value={riskLevel} onChange={(e) => setRiskLevel(e.target.value)} style={{ ...inputS, marginTop: 6 }}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
            <input
              value={investmentScope}
              onChange={(e) => setInvestmentScope(e.target.value)}
              placeholder="Investment size (optional)"
              style={{ ...inputS, marginTop: 10 }}
            />
          </div>
        )}

        {step === 3 && (
          <div style={{ marginTop: 14 }}>
            <label style={{ fontSize: 12, color: 'var(--text-3)' }}>Sector Focus</label>
            <input
              value={sectorFocus}
              onChange={(e) => setSectorFocus(e.target.value)}
              placeholder="Example: Enerji Üretim ve Dağıtım"
              style={{ ...inputS, marginTop: 6 }}
            />
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 16 }}>
          <button
            onClick={() => setStep((s) => Math.max(1, s - 1))}
            disabled={step === 1}
            style={{ border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)', background: 'var(--surface-2)', color: 'var(--text-1)', padding: '9px 12px', cursor: step === 1 ? 'not-allowed' : 'pointer' }}
          >
            Back
          </button>
          {step < 3 ? (
            <button
              onClick={() => setStep((s) => Math.min(3, s + 1))}
              style={{ border: 'none', borderRadius: 'var(--radius-md)', background: 'var(--primary)', color: '#fff', padding: '9px 14px', cursor: 'pointer' }}
            >
              Next
            </button>
          ) : (
            <button
              onClick={finish}
              style={{ border: 'none', borderRadius: 'var(--radius-md)', background: 'var(--primary)', color: '#fff', padding: '9px 14px', cursor: 'pointer' }}
            >
              Finish
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
