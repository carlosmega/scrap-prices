import { QuoteList } from "@/features/lists/components/quote-list";

/**
 * Ruta de la cotización (`/cotizacion`, F022).
 *
 * Server Component delgado: solo compone el organismo `<QuoteList />`, que es
 * Client Component (lee la sesión de `getSessionKey` y consume `/api/lists*`).
 * Así el fetch ocurre en el navegador y `pnpm build` no depende del backend.
 */
export default function QuotePage() {
  return (
    <main className="flex min-h-screen flex-col items-center gap-8 bg-background p-8">
      <QuoteList />
    </main>
  );
}
