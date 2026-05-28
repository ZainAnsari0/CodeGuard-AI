// CodeGuard AI — Auth Endpoint Load Test
// Run with: k6 run k6_auth.js
// Requires: k6 (https://k6.io/)

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 20 },    // Stay at 20 users
    { duration: '30s', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests < 500ms
    http_req_failed: ['rate<0.05'],     // Less than 5% failure rate
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

export default function () {
  // Test health endpoint
  const healthRes = http.get(`${BASE_URL}/api/v1/health`);
  check(healthRes, {
    'health endpoint is 200': (r) => r.status === 200,
  });

  // Test login endpoint with invalid credentials (stress test)
  const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, {
    username: `loadtest_${__VU}@test.com`,
    password: 'LoadTest!Pass1',
  });
  check(loginRes, {
    'login returns 401 or 400': (r) => r.status === 401 || r.status === 400,
  });

  sleep(1);
}