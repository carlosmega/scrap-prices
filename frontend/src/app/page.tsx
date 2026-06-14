import { HealthIndicator } from "@/features/health/components/health-indicator";
import { ZoneSelector } from "@/features/zones/components/zone-selector";

/**
 * Home de ConstruScan (shell de la app, F019).
 *
 * Server Component: compone el encabezado y el selector de zona. La
 * interactividad y el consumo de API viven en Client Components hijos
 * (`<ZoneSelector />`, `<HealthIndicator />`), por lo que el fetch ocurre en el
 * navegador y `pnpm build` no depende de que el backend esté arriba.
 */
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 bg-background p-8">
      <header className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">
          ConstruScan
        </h1>
        <p className="max-w-md text-sm text-muted-foreground">
          Comparador de precios de materiales de construcción. Empieza eligiendo
          tu zona.
        </p>
      </header>

      <ZoneSelector />

      <footer className="flex flex-col items-center gap-1">
        <HealthIndicator />
      </footer>
    </main>
  );
}
