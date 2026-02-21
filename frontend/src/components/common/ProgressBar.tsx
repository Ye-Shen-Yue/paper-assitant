interface Props {
  progress: number;
  label?: string;
  className?: string;
}

export default function ProgressBar({ progress, label, className = '' }: Props) {
  const pct = Math.min(Math.max(progress * 100, 0), 100);

  return (
    <div className={className}>
      {label && (
        <div className="flex justify-between text-sm text-slate-600 mb-1">
          <span>{label}</span>
          <span>{pct.toFixed(0)}%</span>
        </div>
      )}
      <div className="w-full bg-slate-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
