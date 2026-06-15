# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F029** — HD búsqueda real (profileName + marketId/stLocId)
**Spec:** `specs/F029-hd-busqueda-params.md`

## Descubierto en la corrida real (el líder SÍ tiene red desde el sandbox)
`scrape --dry-run` corrió en vivo sin bloqueo pero trajo **0 productos**: la búsqueda de HD
necesita `profileName=HCL_V2_findProductsBySearchTermWithPrice` + `marketId=10` + `stLocId=18503`
(id interno ≠ external_id 1333). Confirmado vía WebFetch: con esos params → 13 varillas; sin ellos → total:0.
El endpoint por `partNumber` ya funcionaba ($20,068).

## Plan F029 (capa backend → implementer-backend)
1. geo: `RetailerLocation.extra` JSONField (+ migración).
2. seed: HD Monterrey `extra={"market_id":"10","st_loc_id":"18503"}`.
3. adapter: `_build_search_url` añade profileName + limit/offset + marketId/stLocId desde `extra`.
4. test unit de la URL; offline tests siguen verdes.

Tras review, el líder **re-corre el `--dry-run` en vivo** para confirmar ~13 varillas.

**Estado:** F029 `in_progress`.
