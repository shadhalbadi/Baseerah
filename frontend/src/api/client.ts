import { API_URL, TOKEN_KEY } from '../config'
import type {
  AnalysisResult,
  Bill,
  BillCreate,
  Explanation,
  ExtractionResult,
  HealthReport,
  Property,
  PropertyCreate,
  User,
  UtilityType,
} from '../types'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem(TOKEN_KEY)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      // FormData must set its own multipart boundary — don't force JSON on it
      ...(options.body && !(options.body instanceof FormData)
        ? { 'Content-Type': 'application/json' }
        : {}),
      ...authHeaders(),
      ...(options.headers ?? {}),
    },
  })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = (await res.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export const api = {
  async login(email: string, password: string): Promise<string> {
    const body = new URLSearchParams({ username: email, password })
    const res = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    })
    if (!res.ok) {
      const msg = res.status === 401 ? 'invalid_credentials' : res.statusText
      throw new ApiError(res.status, msg)
    }
    const data = (await res.json()) as { access_token: string }
    return data.access_token
  },

  register(email: string, name: string, password: string): Promise<User> {
    return request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, name, password }),
    })
  },

  me(): Promise<User> {
    return request<User>('/auth/me')
  },

  listProperties(): Promise<Property[]> {
    return request<Property[]>('/properties')
  },

  createProperty(payload: PropertyCreate): Promise<Property> {
    return request<Property>('/properties', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  getProperty(id: number): Promise<Property> {
    return request<Property>(`/properties/${id}`)
  },

  listBills(propertyId: number): Promise<Bill[]> {
    return request<Bill[]>(`/properties/${propertyId}/bills`)
  },

  createBill(propertyId: number, payload: BillCreate): Promise<Bill> {
    return request<Bill>(`/properties/${propertyId}/bills`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  getAnalysis(propertyId: number, utility: UtilityType): Promise<AnalysisResult> {
    return request<AnalysisResult>(
      `/properties/${propertyId}/analysis?utility_type=${utility}`,
    )
  },

  getExplanation(propertyId: number, utility: UtilityType, lang: string): Promise<Explanation> {
    return request<Explanation>(
      `/properties/${propertyId}/analysis/explanation?utility_type=${utility}&lang=${lang}`,
    )
  },

  getReport(propertyId: number, utility: UtilityType): Promise<HealthReport> {
    return request<HealthReport>(
      `/properties/${propertyId}/report?utility_type=${utility}`,
    )
  },

  extractBill(propertyId: number, file: File): Promise<ExtractionResult> {
    const body = new FormData()
    body.append('file', file)
    // no Content-Type header — the browser sets the multipart boundary
    return request<ExtractionResult>(`/properties/${propertyId}/bills/extract`, {
      method: 'POST',
      body,
    })
  },
}
