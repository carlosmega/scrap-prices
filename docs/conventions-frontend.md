# Convenciones de frontend (Next.js 15 + Tailwind + shadcn/ui)

## Stack
- Next.js 15, App Router, TypeScript estricto (`strict: true`, cero `any`).
- Tailwind v4 para estilos; shadcn/ui como sistema de componentes.
- pnpm como gestor. Prettier lo aplica el hook PostToolUse.

## Estructura (Atomic Design + Screaming Architecture)
```
frontend/src/
├── app/                      # rutas App Router (thin: componen features)
├── features/<dominio>/       # la arquitectura "grita" el dominio
│   ├── components/           # organismos del dominio
│   ├── hooks/
│   └── api.ts                # llamadas del dominio usando el client tipado
├── components/
│   └── ui/                   # shadcn — instalado por CLI/MCP, no se edita
│                             #   a mano salvo extensión consciente y comentada
└── lib/
    └── api/
        ├── schema.d.ts       # GENERADO por pnpm gen:api — nunca a mano
        └── client.ts         # único punto de fetch al backend
```

## Reglas duras
1. **El contrato manda.** Todo dato de API se tipa desde `schema.d.ts`.
   Declarar a mano el tipo de una respuesta es causa de rechazo en review.
2. **Un solo punto de salida HTTP:** `lib/api/client.ts` (maneja base URL,
   errores y tipos). Los componentes jamás hacen `fetch` directo.
3. Server Components por defecto; `"use client"` solo cuando hay
   interactividad o estado, y lo más abajo posible del árbol.
4. Componentes shadcn se añaden con `pnpm dlx shadcn@latest add <comp>` o
   con el MCP de shadcn. Nunca copy-paste manual del sitio.
5. Todo fetch renderiza sus tres estados: cargando, error, datos.
6. Tailwind: tokens del theme, no valores mágicos (`text-primary`, no
   `text-[#3b82f6]`).

## Arquitectura limpia (reglas mecánicas)
Las reglas 1 y 2 no se sostienen por disciplina: se hacen cumplir con ESLint
(`pnpm lint` falla si se rompen) y la Fase 4 de `init.sh` añade un grep heurístico.

- **`fetch(` solo en `src/lib/api/client.ts`.** Ningún componente, hook o
  `features/<dominio>/api.ts` llama a `fetch` directo: todos pasan por el
  cliente tipado. Regla ESLint: `no-restricted-syntax` / `import/no-restricted-paths`.
- **Cero `any`** (`@typescript-eslint/no-explicit-any: error`). Los tipos de la
  API salen de `schema.d.ts`; declarar a mano el tipo de una respuesta = rechazo.
- **El dominio grita.** Una feature vive completa en `features/<dominio>/`
  (componentes + hooks + `api.ts`); `app/` solo compone. No metas lógica de
  dominio en `app/`.

Flujo de datos (una dirección):
```
features/<dominio>/api.ts  →  lib/api/client.ts  →  backend
   (tipos de schema.d.ts)      (base URL, errores)
```

> **CORS:** como `client.ts` corre en el navegador (Client Components) contra
> `NEXT_PUBLIC_API_URL` (`:8000`), el backend DEBE tener `corsheaders`
> configurado (ver `specs/F001`). Sin eso el fetch client-side se bloquea.
