/**
 * Home Page
 * Skeleton - no business implementation
 * @TODO: Implement full page in TP-2
 */

export default function HomePage(): JSX.Element {
  return (
    <main className="min-h-screen bg-bg p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12 text-center">
          <h1 className="text-4xl font-bold text-text mb-4">
            World Cup 2026 AI Prediction
          </h1>
          <p className="text-muted text-lg">
            Explainable Tournament Analysis
          </p>
        </header>

        {/* TODO: Full implementation in TP-2 */}
        <div className="bg-surface border-border rounded-lg p-8 text-center">
          <p className="text-muted">Home Page - Skeleton</p>
          <p className="text-sm text-muted mt-2">
            Full implementation coming in TP-2
          </p>
        </div>

        {/* Navigation placeholder */}
        <nav className="mt-8 flex justify-center gap-4">
          <a
            href="/tournament"
            className="px-4 py-2 bg-accent text-bg rounded-lg font-medium hover:opacity-90 transition-opacity"
          >
            View Tournament
          </a>
        </nav>
      </div>
    </main>
  );
}
