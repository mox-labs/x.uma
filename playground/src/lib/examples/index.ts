import type { Preset } from "../types.js";
import { simpleExact } from "./simple-exact.js";
import { predicates } from "./predicates.js";
import { nested } from "./nested.js";
import { httpRouting } from "./http-routing.js";
import { fallback } from "./fallback.js";

export const presets: Preset[] = [
  simpleExact,
  predicates,
  nested,
  httpRouting,
  fallback,
];

export { simpleExact, predicates, nested, httpRouting, fallback };
