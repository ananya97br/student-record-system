import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: { target_2000: { executor: "constant-vus", vus: 2000, duration: "2m" } },
  thresholds: { http_req_duration: ["p(95)<3000"], http_req_failed: ["rate<0.02"] },
};

export default function () {
  const base = __ENV.BASE_URL || "http://localhost:8000";
  const response = http.get(`${base}/health/live`);
  check(response, { "health is 200": (r) => r.status === 200 });
}
