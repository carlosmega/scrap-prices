import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

// Selectores de `no-restricted-syntax` que prohíben llamar a `fetch` directo.
// El único punto de salida HTTP es `src/lib/api/client.ts` (ver
// docs/conventions-frontend.md). Cubre `fetch(...)`, `window.fetch(...)` y
// `globalThis.fetch(...)`.
const NO_FETCH_RULES = [
  {
    selector: "CallExpression[callee.name='fetch']",
    message:
      "Prohibido `fetch` directo. Todo HTTP pasa por src/lib/api/client.ts (F003).",
  },
  {
    selector:
      "CallExpression[callee.object.name=/^(window|globalThis|self)$/][callee.property.name='fetch']",
    message:
      "Prohibido `fetch` directo. Todo HTTP pasa por src/lib/api/client.ts (F003).",
  },
];

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    ignores: [
      "node_modules/**",
      ".next/**",
      // F036: build output del distDir aislado de verificación (NEXT_DIST_DIR=.next-ci).
      // Es generado, igual que .next/; sin esto, lint del build de prod falla y rompe
      // el objetivo de F036 (init.sh verde repetible cuando .next-ci/ existe).
      ".next-ci/**",
      "out/**",
      "build/**",
      "next-env.d.ts",
      // schema.d.ts es GENERADO por `pnpm gen:api`; no se lintean sus tipos.
      "src/lib/api/schema.d.ts",
    ],
  },
  // Reglas de arquitectura limpia (mecánicas, no de prompt).
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: {
      // Cero `any`: los tipos de la API salen de schema.d.ts, nunca a mano.
      "@typescript-eslint/no-explicit-any": "error",
      // `fetch` directo prohibido fuera del cliente.
      "no-restricted-syntax": ["error", ...NO_FETCH_RULES],
      // El schema generado no se importa a mano fuera del flujo gen:api;
      // se consume vía el cliente tipado (F003).
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["**/lib/api/schema", "**/lib/api/schema.d"],
              message:
                "No importes schema.d.ts directamente: consúmelo vía src/lib/api/client.ts.",
            },
          ],
        },
      ],
    },
  },
  // El cliente HTTP es el ÚNICO lugar donde `fetch` está permitido.
  {
    files: ["src/lib/api/client.ts"],
    rules: {
      "no-restricted-syntax": "off",
    },
  },
];

export default eslintConfig;
