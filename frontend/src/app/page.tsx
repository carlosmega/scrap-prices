import { HealthIndicator } from "@/features/health/components/health-indicator";
import { SearchPanel } from "@/features/search/components/search-panel";
import { ZoneSelector } from "@/features/zones/components/zone-selector";

/**
 * Home de ConstruScan (shell de la app, F019 + F020).
 *
 * Server Component: compone el encabezado, el selector de zona y, debajo, el
 * panel de búsqueda. La interactividad y el consumo de API viven en Client
 * Components hijos (`<ZoneSelector />`, `<SearchPanel />`, `<HealthIndicator />`),
 * por lo que el fetch ocurre en el navegador y `pnpm build` no depende de que el
 * backend esté arriba.
 */
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center gap-8 bg-background p-8">
      <header className="flex flex-col items-center gap-2 pt-8 text-center">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">
          ConstruScan
        </h1>
        <p className="max-w-md text-sm text-muted-foreground">
          Comparador de precios de materiales de construcción. Empieza eligiendo
          tu zona.
        </p>
      </header>

      <ZoneSelector />

      <SearchPanel />

      <footer className="mt-auto flex flex-col items-center gap-1 pt-4">
        <HealthIndicator />
      </footer>
    </main>
  );
}
