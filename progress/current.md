# Sesión activa — F026 ConstruramaAdapter

> El líder mantiene este archivo. Punto de retomada de la sesión.

**Feature en curso:** `F026` (in_progress) — ConstruramaAdapter (Algolia, respetuoso):
parser + ingestión + Celery + seed, segundo retailer (habilita comparación
cross-retailer real).

**ToS: APROBADO por el humano el 2026-07-07** → levanta el `paused` del recon §0.
Guardrails vigentes: UA honesto, rate-limit, sin evasión, raw_payload, stop-if-blocked.

## Bloqueo actual (esperando insumo humano)
El parser necesita la **forma real de `hits[]`** de la respuesta Algolia, que NO
estaba en el 1er HAR (F011 §2.1/§6). El humano va a capturar un **2º HAR "Save with
content"** y dejarlo en `docs/recon/har/` (gitignored). Ruta elegida: "tú capturas
HAR" (no hago requests yo; parser con golden fixtures, patrón F025).

### Qué debe traer la 2ª captura (en orden de importancia)
1. **Body de la respuesta de Algolia** — `POST njvy3eu5dw-dsn.algolia.net/1/indexes/*/queries`
   (índice `construrama_mx`) tras buscar "varilla" en Monterrey/Nuevo León.
   → de aquí salen los nombres de campos de `hits[]` (objectID/productCode, nombre,
   precio `OSS7_priceValue_mxn_double`, url, unidad, marca, facets de diámetro/grado/largo).
2. `GET .../store-finder/setStoresByCity?...` — store-id/external_id del distribuidor de Monterrey.
3. `GET .../get/algolia` — App ID + search key pública + prefijo `OSS7` por zona.

## Plan (una vez llegue el HAR)
1. [hecho] `specs/F026-adapter-construrama.md` (contrato; campos de hits[] a cerrar con el HAR).
2. [hecho] F026 `in_progress`.
3. [pendiente] Recibir HAR en `docs/recon/har/` → extraer/sanitizar golden fixtures.
4. [pendiente] Lanzar `implementer-backend` con la spec: adapter + parser + ingestión +
   tarea Celery + wiring en `manage.py scrape` + seed Construrama Monterrey.
5. [pendiente] Validar dry-run offline (MockTransport) y, si procede, corrida real respetuosa.
6. [pendiente] `reviewer` → APROBADO → `done` → history.md.

## Arrastre de la sesión (todo en origin/main salvo lo indicado)
- Repo validado; 2 hotfixes de arnés (`d951a03` +x, `435d25c` docker) y **F032 CI
  entregada y verde en Actions** (workflow `.github/workflows/ci.yml`).
- **Permisos:** `git push` movido a `permissions.ask` (aprobación por-push). Commit
  local `chore(harness): git push pasa a 'ask'` **SIN pushear** (espera tu aprobación).
- Atribución git de la sesión con committer `M081899@…local` (no enlaza a `carlosmega`).

## Cómo levantar (local)
```bash
./dev-backend.sh    # :8800   ./dev-frontend.sh   # :3300
```
