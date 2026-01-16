export function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className="flex items-center justify-center p-8">
      <div
        className={`animate-spin rounded-full border-4 border-gray-200 border-t-primary ${sizeClasses[size]}`}
      />
    </div>
  );
}
