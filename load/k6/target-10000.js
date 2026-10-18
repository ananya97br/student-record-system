import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: { target_10000: { executor: "ramping-vus", startVUs: 100, stages: [{ duration: "1m", target: 2500 }, { duration: "2m", target: 10000 }, { duration: "1m", target: 10000 }, { duration: "30s", target: 0 }] } },
  thresholds: { http_req_duration: ["p(95)<3000"], http_req_failed: ["rate<0.02"] },
};

export default function () {
  const base = __ENV.BASE_URL || "http://localhost:8000";
  const response = http.get(`${base}/health/live`);
  check(response, { "health is 200": (r) => r.status === 200 });
}
