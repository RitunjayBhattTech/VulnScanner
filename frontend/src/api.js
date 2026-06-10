const API_BASE = '/api/v1';

async function request(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || `HTTP ${response.status}`);
  }
  return response.json();
}

export function getScans(skip = 0, limit = 50) {
  return request(`/scans/?skip=${skip}&limit=${limit}`);
}

export function getScan(scanId) {
  return request(`/scans/${scanId}`);
}

export function getScanFindings(scanId, skip = 0, limit = 100) {
  return request(`/scans/${scanId}/findings?skip=${skip}&limit=${limit}`);
}

export function getScanChains(scanId) {
  return request(`/scans/${scanId}/chains`);
}

export function createScan(target_scope, profile, authorized) {
  return request('/scans/', {
    method: 'POST',
    body: JSON.stringify({ target_scope, profile, authorized }),
  });
}

export async function checkBackendHealth() {
  try {
    await request('/scans/?limit=1');
    return true;
  } catch {
    return false;
  }
}