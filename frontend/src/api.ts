/**
 * Authenticated API client for CloudSense
 */

const API_BASE_URL = 'http://localhost:8000'

/**
 * Make authenticated API request
 */
export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  // Get Clerk session token
  const token = await (window as any).__clerk?.session?.getToken()
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }
  
  // Add auth header if token exists
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  return fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })
}
