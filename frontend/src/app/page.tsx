import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { HealthIndicator } from "@/features/health/components/health-indicator";
import { env } from "@/lib/env";

/**
 * Home de ConstruScan.
 *
 * Server Component: compone estilos Tailwind y componentes shadcn. El consumo
 * de `GET /api/health` ocurre en `<HealthIndicator />` (Client Component), de
 * modo que el fetch sucede en el navegador y `pnpm build` no depende de que el
 * backend esté arriba.
 */
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 bg-background p-8">
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">
          ConstruScan
        </h1>
        <p className="max-w-md text-sm text-muted-foreground">
          Comparador de precios de materiales de construcción. Bootstrap del
          frontend (F002): aún sin consumo de API.
        </p>
      </div>

      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Buscar material</CardTitle>
          <CardDescription>
            Placeholder de UI. La búsqueda real se conecta al backend en F003.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Input
            type="search"
            placeholder='Ej. "varilla 3/8"'
            aria-label="Buscar material"
            disabled
          />
          <Button disabled>Buscar</Button>
        </CardContent>
        <CardFooter className="flex-col items-start gap-2">
          <HealthIndicator />
          <p className="text-xs text-muted-foreground">
            Backend configurado en{" "}
            <code className="rounded bg-muted px-1 py-0.5 font-mono">
              {env.apiUrl}
            </code>
          </p>
        </CardFooter>
      </Card>
    </main>
  );
}
