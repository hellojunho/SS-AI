type ProgressBarProps = {
  value: number
  label?: string
}

const ProgressBar = ({ value, label = '진행 상황' }: ProgressBarProps) => {
  const clamped = Math.max(0, Math.min(100, Math.round(value)))
  return (
    <div className="progress-bar-wrapper" role="status" aria-live="polite">
      <div className="progress-bar-header">
        <span>{label}</span>
        <span>{clamped}%</span>
      </div>
      <div className="progress-bar-track" role="progressbar" aria-valuenow={clamped} aria-valuemin={0} aria-valuemax={100}>
        <div className="progress-bar-fill" style={{ width: `${clamped}%` }} />
      </div>
    </div>
  )
}

export default ProgressBar
