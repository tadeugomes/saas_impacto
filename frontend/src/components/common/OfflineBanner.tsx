import { useEffect, useState } from 'react';

export function OfflineBanner() {
  const [online, setOnline] = useState<boolean>(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (online) {
    return null;
  }

  return (
    <div className="bg-amber-500 text-white px-4 py-2 text-sm font-medium">
      Modo offline — os dados podem estar desatualizados.
    </div>
  );
}
