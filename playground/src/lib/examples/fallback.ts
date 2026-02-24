import type { Preset } from "../types.js";

export const fallback: Preset = {
  id: "fallback",
  name: "Fallback",
  mode: "config",
  description: "on_no_match provides a default action when nothing matches",
  config: JSON.stringify(
    {
      matchers: [
        {
          predicate: {
            type: "single",
            input: {
              type_url: "xuma.test.v1.StringInput",
              config: { key: "status" },
            },
            value_match: { Exact: "active" },
          },
          on_match: { type: "action", action: "allow" },
        },
      ],
      on_no_match: { type: "action", action: "deny" },
    },
    null,
    2,
  ),
  context: { status: "suspended" },
};
