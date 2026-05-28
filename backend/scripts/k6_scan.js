// CodeGuard AI — Scan Upload + Polling Load Test
// Run with: k6 run k6_scan.js
// Requires: k6 (https://k6.io/) and a running backend with test user

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 2 },   // Ramp up to 2 concurrent scans
    { duration: '2m', target: 5 },    // Stay at 5 concurrent scans
    { duration: '30s', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],  // 95% of requests < 2s
    http_req_failed: ['rate<0.1'],      // Less than 10% failure rate
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';

export default function () {
  if (!AUTH_TOKEN) {
    console.error('AUTH_TOKEN environment variable is required');
    return;
  }

  const headers = {
    'Authorization': `Bearer ${AUTH_TOKEN}`,
  };

  // Upload a test file
  const uploadRes = http.post(`${BASE_URL}/api/v1/scanner/upload`, {
    files: http.file(b'print("hello world")', 'load_test.py', 'text/x-python'),
    language: 'python',
  }, { headers });

  check(uploadRes, {
    'upload status is 200/201/202': (r) => [200, 201, 202].includes(r.status),
  });

  sleep(2);
}