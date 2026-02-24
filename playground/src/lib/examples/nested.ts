import type { Preset } from "../types.js";

export const nested: Preset = {
  id: "nested",
  name: "Nested Matcher",
  mode: "config",
  description: "Outer matches tier, inner dispatches on region",
  config: JSON.stringify(
    {
      matchers: [
        {
          predicate: {
            type: "single",
            input: {
              type_url: "xuma.test.v1.StringInput",
              config: { key: "tier" },
            },
            value_match: { Exact: "premium" },
          },
          on_match: {
            type: "matcher",
            matcher: {
              matchers: [
                {
                  predicate: {
                    type: "single",
                    input: {
                      type_url: "xuma.test.v1.StringInput",
                      config: { key: "region" },
                    },
                    value_match: { Exact: "us-east" },
                  },
                  on_match: { type: "action", action: "premium_us_east" },
                },
                {
                  predicate: {
                    type: "single",
                    input: {
                      type_url: "xuma.test.v1.StringInput",
                      config: { key: "region" },
                    },
                    value_match: { Exact: "eu-west" },
                  },
                  on_match: { type: "action", action: "premium_eu_west" },
                },
              ],
              on_no_match: { type: "action", action: "premium_default" },
            },
          },
        },
      ],
      on_no_match: { type: "action", action: "free_tier" },
    },
    null,
    2,
  ),
  context: { tier: "premium", region: "us-east" },
};
