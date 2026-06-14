import { ProductDetail } from "@/features/products/components/product-detail";
import { QuoteBadge } from "@/features/lists/components/quote-badge";

/**
 * Ruta de detalle de producto (`/products/[id]`, F021).
 *
 * Server Component delgado: lee el `id` de la ruta (en Next 15 `params` es una
 * promesa) y compone el organismo `<ProductDetail />`, que es Client Component
 * (lee la zona de `useSelectedZone` y consume `GET /api/products/{id}`). Así el
 * fetch ocurre en el navegador y `pnpm build` no depende de que el backend esté
 * arriba.
 */
export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <main className="flex min-h-screen flex-col items-center gap-8 bg-background p-8">
      <div className="flex w-full max-w-2xl items-center justify-end">
        <QuoteBadge />
      </div>

      <ProductDetail id={id} />
    </main>
  );
}
