import type { Preset } from "../types.js";

export const httpRouting: Preset = {
  id: "http-routing",
  name: "HTTP Routing",
  mode: "http",
  description: "Gateway API-style route matching with method + path + headers",
  config: JSON.stringify(
    [
      {
        match: {
          method: "GET",
          path: { type: "PathPrefix", value: "/api/" },
        },
        action: "api_get",
      },
      {
        match: {
          method: "POST",
          path: { type: "PathPrefix", value: "/api/" },
          headers: [
            {
              type: "Exact",
              name: "content-type",
              value: "application/json",
            },
          ],
        },
        action: "api_post_json",
      },
      {
        match: {
          path: { type: "Exact", value: "/health" },
        },
        action: "healthcheck",
      },
    ],
    null,
    2,
  ),
  context: {},
  http: {
    method: "GET",
    path: "/api/users",
    headers: {},
  },
};
