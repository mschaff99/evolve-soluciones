interface StatCardProps {
  value: number | string;
  label: string;
  icon: string;
  gradient?: string;
}

export default function StatCard({ value, label, icon, gradient = 'var(--gradient-primary)' }: StatCardProps) {
  return (
    <div className="stat-card card-hover">
      <div className="stat-card-body">
        <div>
          <div className="stat-value">{value}</div>
          <div className="stat-label">{label}</div>
        </div>
        <div className="stat-icon" style={{ background: gradient }}>
          <i className={icon} />
        </div>
      </div>
    </div>
  );
}
