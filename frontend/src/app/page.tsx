"use client";

import { useEffect, useState } from "react";

interface HealthStatus {
  status: string;
  database: string;
  version: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((res) => res.json())
      .then((data) => setHealth(data))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold text-gray-900">EntreLíneas</h1>
      <p className="mt-4 text-lg text-gray-600">
        Las historias unen a las personas.
      </p>
      <p className="mt-2 text-sm text-gray-400">
        Platform under construction — Sprint 0 complete.
      </p>

      <div className="mt-8 rounded-lg border border-gray-200 p-4 text-sm">
        <h2 className="font-semibold text-gray-700">Backend Status</h2>
        {error && (
          <p className="mt-2 text-red-500">Connection failed: {error}</p>
        )}
        {health && (
          <ul className="mt-2 space-y-1 text-gray-600">
            <li>API: <span className="font-mono text-green-600">{health.status}</span></li>
            <li>Database: <span className="font-mono text-green-600">{health.database}</span></li>
            <li>Version: <span className="font-mono">{health.version}</span></li>
          </ul>
        )}
        {!health && !error && (
          <p className="mt-2 text-gray-400">Connecting...</p>
        )}
      </div>
    </main>
  );
}
