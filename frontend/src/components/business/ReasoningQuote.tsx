/**
 * ReasoningQuote Component (Business Layer)
 * Displays reasoning text with source
 * @TODO: Implement full UI in TP-2
 */

export interface ReasoningQuoteProps {
  text: string;
  source?: string;
}

export function ReasoningQuote({ text, source }: ReasoningQuoteProps): JSX.Element {
  // TODO: Implement full UI in TP-2
  return (
    <div data-component="ReasoningQuote">
      <div className="bg-surface2 border-l-4 border-accent pl-4 py-2">
        <p className="text-sm italic">&ldquo;{text}&rdquo;</p>
        {source && (
          <p className="text-xs text-muted mt-2">— {source}</p>
        )}
      </div>
    </div>
  );
}
