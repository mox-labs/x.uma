import type { Preset } from "../types.js";

export const predicates: Preset = {
  id: "predicates",
  name: "AND Predicate",
  mode: "config",
  description: "Compound AND: both role=admin AND org prefix acme must match",
  config: JSON.stringify(
    {
      matchers: [
        {
          predicate: {
            type: "and",
            predicates: [
              {
                type: "single",
                input: {
                  type_url: "xuma.test.v1.StringInput",
                  config: { key: "role" },
                },
                value_match: { Exact: "admin" },
              },
              {
                type: "single",
                input: {
                  type_url: "xuma.test.v1.StringInput",
                  config: { key: "org" },
                },
                value_match: { Prefix: "acme" },
              },
            ],
          },
          on_match: { type: "action", action: "admin_acme" },
        },
      ],
    },
    null,
    2,
  ),
  context: { role: "admin", org: "acme-corp" },
};
