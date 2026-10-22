type SwagRatingProps = {
  score: number
  label?: string
}

export function loyaltyScore(pieces: number): number {
  return Math.max(0, Math.min(5, Math.floor(pieces)))
}

function Flute({ filled }: { filled: boolean }) {
  return (
    <svg className={filled ? 'flute on' : 'flute'} viewBox="0 0 32 56" aria-hidden="true">
      <path className="flute-bowl" d="M9.5 3.5h13c.5 8 1.4 15.5-2 22.2-2.4 4.6-5.2 4.6-7.6 0C8 19 9 11.5 9.5 3.5z" />
      <path className="flute-stem" d="M15 27.5h2V44h-2z" />
      <path className="flute-foot" d="M8 45.5h16" />
      {filled && (
        <>
          <circle className="bubble" cx="14" cy="18" r="1.15" />
          <circle className="bubble b2" cx="18.2" cy="13" r="0.85" />
          <circle className="bubble b3" cx="15.4" cy="22" r="0.7" />
        </>
      )}
    </svg>
  )
}

export function SwagRating({ score, label = 'Swag' }: SwagRatingProps) {
  const flutes = Math.max(0, Math.min(5, Math.round(score)))
  return (
    <p className="swag" aria-label={`${label} ${flutes} out of 5`}>
      <span className="swag-label">{label}</span>
      <span className="flutes" aria-hidden="true">
        {Array.from({ length: 5 }, (_, index) => (
          <Flute key={index} filled={index < flutes} />
        ))}
      </span>
      <span className="swag-num">{flutes}/5</span>
    </p>
  )
}
