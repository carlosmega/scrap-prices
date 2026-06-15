# Sesión activa

> El líder mantiene este archivo. Se limpia al cerrar cada feature.

**Feature en curso:** **F030** — Fix hydration mismatch (hooks localStorage SSR-safe)
**Spec:** `specs/F030-fix-hydration.md`

## Bug reportado por el humano (navegador)
"Hydration failed... server rendered text didn't match the client" en SearchPanel/CardDescription.
Causa: `useSelectedZone` (y cotización/sesión) leen localStorage en el render inicial → SSR (sin zona)
≠ cliente (con zona guardada). Build/tests offline no lo detectaron (es runtime SSR/cliente).

## Plan F030 (frontend + e2e → implementer-frontend)
- Hooks SSR-safe: valor inicial = default sin localStorage; leer localStorage en useEffect/useSyncExternalStore
  tras montar. Conservar persistencia + sync. Aplicar a useSelectedZone (F019) y useQuote/getSessionKey (F022).
- Guardia E2E: fallar si hay error de hidratación al cargar `/` con zona pre-seteada en localStorage.

Tras review, el líder reinicia el dev server y confirma 200 sin mismatch.

**Estado:** F030 `in_progress`. (Datos reales de HD ya visibles en la app; este fix es de calidad de UI.)
