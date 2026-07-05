/**
 * Compare Page
 * Skeleton - no business implementation
 * @TODO: Implement full page in TP-2
 */

export default function ComparePage(): JSX.Element {
  return (
    <main className="min-h-screen bg-bg p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-text mb-2">
            Compare Teams
          </h1>
          <p className="text-muted">
            Side-by-side Team Analysis
          </p>
        </header>

        {/* TODO: Full implementation in TP-2 */}
        <div className="bg-surface border-border rounded-lg p-8 text-center">
          <p className="text-muted">Compare Page - Skeleton</p>
          <p className="text-sm text-muted mt-2">
            Full implementation coming in TP-2
          </p>
        </div>

        {/* Navigation placeholder */}
        <nav className="mt-8 flex justify-center gap-4">
          <a
            href="/"
            className="px-4 py-2 text-accent hover:underline"
          >
            Back to Home
          </a>
        </nav>
      </div>
    </main>
  );
}
