// Shared "signal from noise / research terminal" visual layer.
// Renders a subtle scanline overlay + injects the shared interaction classes
// (press compression, hairline sweep, gold/emerald glow, signal pulse,
// crystallize entrance). Used by the research-terminal pages so the styling
// and micro-interactions stay consistent without duplicating CSS per page.
//
// Class hooks (apply alongside existing inline styles):
//   .tfx          → page root: scopes vars, sharper feel
//   .tfx-enter    → crystallize entrance (blur→crisp, respects reduced-motion)
//   .tfx-kicker   → mono uppercase letterspaced section/kicker text
//   .tfx-press    → terminal control button (gold glow + press compression + sweep)
//   .tfx-press.is-emerald → emerald-glow variant
//   .tfx-card     → hover-lift result/company card with emerald edge + sweep
//   .tfx-tab      → tab/segment control with active underline
//   .tfx-chip     → prompt chip / filter pill
//   .tfx-pulse    → signal-pulse dot

export default function TerminalFx() {
  return (
    <>
      <span className="tfx-scan" aria-hidden="true" />
      <style>{CSS}</style>
    </>
  )
}

const CSS = `
.tfx-scan {
  position: fixed; inset: 0; pointer-events: none; z-index: 6;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.012) 0 1px, transparent 1px 4px);
}

.tfx-enter { animation: tfxCrystal 0.7s ease both; }

.tfx-kicker {
  font-family: var(--font-mono) !important;
  text-transform: uppercase;
  letter-spacing: 0.3em !important;
  font-weight: 600 !important;
}

/* terminal control button */
.tfx-press {
  position: relative; overflow: hidden;
  transition: transform 0.12s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
  -webkit-tap-highlight-color: transparent;
}
.tfx-press::after {
  content: ''; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(120deg, transparent 20%, rgba(232,236,230,0.14) 50%, transparent 80%);
  transform: translateX(-130%);
  transition: transform 0.55s ease;
}
.tfx-press:hover { box-shadow: 0 0 18px rgba(200,163,90,0.28); }
.tfx-press:hover::after { transform: translateX(130%); }
.tfx-press:active { transform: translateY(1px) scale(0.985); }
.tfx-press:focus-visible { outline: 1px solid var(--primary); outline-offset: 2px; }
.tfx-press.is-emerald:hover { box-shadow: 0 0 18px rgba(77,165,131,0.28); }
.tfx-press.is-emerald:focus-visible { outline-color: var(--secondary); }

/* hover-lift card */
.tfx-card {
  position: relative; overflow: hidden;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}
.tfx-card::after {
  content: ''; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(120deg, transparent 30%, rgba(77,165,131,0.08) 50%, transparent 70%);
  transform: translateX(-130%); transition: transform 0.6s ease;
}
.tfx-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-bright) !important;
  box-shadow: 0 10px 34px rgba(0,0,0,0.4), 0 0 22px rgba(77,165,131,0.12);
}
.tfx-card:hover::after { transform: translateX(130%); }
.tfx-card:focus-visible { outline: 1px solid var(--secondary); outline-offset: 2px; }

/* tab / segment */
.tfx-tab {
  position: relative;
  transition: color 0.18s ease, background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}
.tfx-tab:hover { box-shadow: 0 0 14px rgba(200,163,90,0.18); }
.tfx-tab:active { transform: translateY(0.5px); }
.tfx-tab:focus-visible { outline: 1px solid var(--primary); outline-offset: 2px; }

/* prompt chip / filter pill */
.tfx-chip {
  position: relative;
  transition: transform 0.12s ease, color 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}
.tfx-chip:hover {
  border-color: var(--border-bright) !important;
  box-shadow: 0 0 14px rgba(200,163,90,0.16);
}
.tfx-chip:active { transform: translateY(1px) scale(0.98); }
.tfx-chip:focus-visible { outline: 1px solid var(--primary); outline-offset: 2px; }

/* signal-pulse dot */
.tfx-pulse { animation: tfxPulse 2.2s ease-in-out infinite; }

/* bottom disclaimer strip — same grammar as the instrument pages */
.tfx-caveat {
  position: sticky; bottom: 14px; z-index: 4; margin-top: 28px;
  display: flex; align-items: center; gap: 10px; width: fit-content; max-width: 100%; flex-wrap: wrap;
  font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.08em;
  color: var(--text-1); background: rgba(10,14,13,0.92);
  border: 1px solid rgba(200,163,90,0.5); border-radius: 2px; padding: 9px 16px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.5);
}
.tfx-caveat .tfx-pulse {
  width: 7px; height: 7px; border-radius: 50%; background: var(--primary); flex-shrink: 0;
}

/* inputs/selects/textareas inside a terminal page: emerald focus signal */
.tfx input:focus, .tfx textarea:focus, .tfx select:focus {
  border-color: var(--secondary) !important;
  box-shadow: 0 0 0 1px rgba(77,165,131,0.3);
  outline: none;
}

@keyframes tfxCrystal {
  from { opacity: 0; filter: blur(6px); }
  to { opacity: 1; filter: blur(0); }
}
@keyframes tfxPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

@media (prefers-reduced-motion: reduce) {
  .tfx-enter { animation: none; }
  .tfx-pulse { animation: none; }
  .tfx-press, .tfx-card, .tfx-tab, .tfx-chip { transition: none; }
  .tfx-press::after, .tfx-card::after { display: none; }
  .tfx-press:active, .tfx-card:hover, .tfx-chip:active, .tfx-tab:active { transform: none; }
}
`
