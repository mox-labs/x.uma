import type { Preset } from "../types.js";

export const simpleExact: Preset = {
  id: "simple-exact",
  name: "Simple Exact",
  mode: "config",
  description: "Single field matcher with exact string match",
  config: JSON.stringify(
    {
      matchers: [
        {
          predicate: {
            type: "single",
            input: {
              type_url: "xuma.test.v1.StringInput",
              config: { key: "name" },
            },
            value_match: { Exact: "alice" },
          },
          on_match: { type: "action", action: "matched" },
        },
      ],
      on_no_match: { type: "action", action: "default" },
    },
    null,
    2,
  ),
  context: { name: "alice" },
};
