export type UtilityType = 'water' | 'electricity'
export type PropertyType = 'apartment' | 'villa' | 'office' | 'shop' | 'other'

export interface User {
  id: number
  email: string
  name: string
  created_at: string
}

export interface Property {
  id: number
  user_id: number
  name: string
  type: PropertyType
  size_sqm: number | null
  occupants: number | null
  region: string | null
  created_at: string
}

export interface PropertyCreate {
  name: string
  type: PropertyType
  size_sqm?: number | null
  occupants?: number | null
  region?: string | null
}

export interface Bill {
  id: number
  property_id: number
  utility_type: UtilityType
  period_start: string
  period_end: string
  consumption: number
  unit: string
  cost: number
  currency: string
  created_at: string
}

export interface BillCreate {
  utility_type: UtilityType
  period_start: string
  period_end: string
  consumption: number
  cost: number
  currency?: string
  unit?: string | null
}

export type ConsumptionStatus =
  | 'insufficient_data'
  | 'normal'
  | 'warning'
  | 'anomaly'

export type RecommendationCategory =
  | 'behavioral'
  | 'maintenance'
  | 'upgrade'
  | 'tariff'

export type Effort = 'low' | 'medium' | 'high'

export interface AnalysisResult {
  property_id: number
  utility_type: UtilityType
  baseline: { sample_size: number; mean: number; stdev: number }
  latest: {
    consumption: number
    unit: string
    status: ConsumptionStatus
    z_score: number | null
    ratio_to_baseline: number | null
    message: string
  }
  leak: { suspected: boolean; reason: string; verification_step: string | null }
  forecast: {
    predicted_consumption: number
    predicted_cost: number
    currency: string
    unit: string
    method: string
    low: number
    high: number
  }
  recommendations: {
    title: string
    category: RecommendationCategory
    reason: string
    estimated_savings: number
    currency: string
    effort: Effort
  }[]
}

export interface Explanation {
  enabled: boolean
  text: string | null
}

export interface Recommendation {
  title: string
  category: RecommendationCategory
  reason: string
  estimated_savings: number
  currency: string
  effort: Effort
}

export interface ExtractedBill {
  utility_type: UtilityType | null
  period_start: string | null
  period_end: string | null
  consumption: number | null
  unit: string | null
  cost: number | null
  currency: string
  confidence: 'high' | 'medium' | 'low'
  warnings: string[]
}

export interface ExtractionResult {
  enabled: boolean
  bill: ExtractedBill | null
  raw_text: string
}

export interface HealthReport {
  property_id: number
  utility_type: UtilityType
  periods_analyzed: number
  unit: string
  currency: string
  headline_annual_waste: number
  base_load: {
    monthly_consumption: number
    monthly_cost: number
    share_of_total: number
  } | null
  floor_rise: {
    suspected: boolean
    recent_floor: number
    prior_floor: number
    ratio: number | null
    reason: string
  }
  slab: {
    marginal_rate: number
    gap_to_next_slab: number | null
  } | null
  timeline: {
    period_start: string
    period_end: string
    consumption: number
    status: ConsumptionStatus
    excess_cost: number
  }[]
  recommendations: Recommendation[]
}
