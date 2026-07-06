import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { api } from '../api/client'
import type { AnalysisResult, ConsumptionStatus } from '../types'
import { Button, Card, ErrorText } from './ui'

const STATUS_STYLES: Record<ConsumptionStatus, string> = {
  normal: 'bg-emerald-100 text-emerald-800',
  warning: 'bg-amber-100 text-amber-800',
  anomaly: 'bg-red-100 text-red-800',
  insufficient_data: 'bg-slate-100 text-slate-600',
}

export function AnalysisView({
  result,
  propertyId,
}: {
  result: AnalysisResult
  propertyId: number
}) {
  const { t, i18n } = useTranslation()
  const { baseline, latest, leak, forecast, recommendations } = result
  const cur = forecast.currency

  const [explaining, setExplaining] = useState(false)
  const [explanation, setExplanation] = useState<string | null>(null)
  const [explainDisabled, setExplainDisabled] = useState(false)
  const [explainError, setExplainError] = useState('')

  const runExplain = async () => {
    setExplaining(true)
    setExplainError('')
    setExplanation(null)
    setExplainDisabled(false)
    try {
      const res = await api.getExplanation(propertyId, result.utility_type, i18n.language)
      if (!res.enabled) setExplainDisabled(true)
      else setExplanation(res.text)
    } catch (e) {
      setExplainError((e as Error).message)
    } finally {
      setExplaining(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Latest status */}
      <Card>
        <div className="flex items-center justify-between gap-3">
          <h3 className="font-semibold text-slate-900">{t('analysis.latest')}</h3>
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${STATUS_STYLES[latest.status]}`}
          >
            {t(`analysis.status.${latest.status}`)}
          </span>
        </div>
        <p className="mt-2 text-sm text-slate-600">{latest.message}</p>
        <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-500">
          <span>
            {latest.consumption} {latest.unit}
          </span>
          <span>
            {t('analysis.baseline')}: {baseline.mean} {latest.unit}{' '}
            {baseline.sample_size > 0 && `· ${t('analysis.samples', { count: baseline.sample_size })}`}
          </span>
        </div>
      </Card>

      {/* Leak */}
      <Card className={leak.suspected ? 'border-amber-300 bg-amber-50' : ''}>
        <h3 className="font-semibold text-slate-900">
          {leak.suspected ? `⚠️ ${t('analysis.leak.suspectedTitle')}` : `✅ ${t('analysis.leak.clearTitle')}`}
        </h3>
        <p className="mt-1 text-sm text-slate-600">{leak.reason}</p>
        {leak.verification_step && (
          <p className="mt-2 text-sm text-slate-700">
            <span className="font-medium">{t('analysis.leak.verify')}: </span>
            {leak.verification_step}
          </p>
        )}
      </Card>

      {/* Forecast */}
      <Card>
        <h3 className="font-semibold text-slate-900">{t('analysis.forecast.title')}</h3>
        <div className="mt-3 grid gap-4 sm:grid-cols-2">
          <div>
            <div className="text-xs text-slate-500">{t('analysis.forecast.predictedUsage')}</div>
            <div className="text-xl font-bold text-slate-900">
              {forecast.predicted_consumption} {forecast.unit}
            </div>
            <div className="text-xs text-slate-400">
              {t('analysis.forecast.range')}: {forecast.low}–{forecast.high} {forecast.unit}
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-500">{t('analysis.forecast.predictedCost')}</div>
            <div className="text-xl font-bold text-slate-900">
              {forecast.predicted_cost} {cur}
            </div>
            <div className="text-xs text-slate-400">
              {t('analysis.forecast.method')}: {forecast.method}
            </div>
          </div>
        </div>
      </Card>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card>
          <h3 className="mb-3 font-semibold text-slate-900">{t('analysis.recommendations.title')}</h3>
          <ul className="space-y-3">
            {recommendations.map((r, i) => (
              <li key={i} className="rounded-lg border border-slate-100 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="font-medium text-slate-900">{r.title}</div>
                  {r.estimated_savings > 0 && (
                    <div className="whitespace-nowrap text-sm font-semibold text-brand-700">
                      {t('analysis.recommendations.estSavings')}: {r.estimated_savings} {r.currency}
                      <span className="text-slate-400">{t('analysis.recommendations.perPeriod')}</span>
                    </div>
                  )}
                </div>
                <p className="mt-1 text-sm text-slate-600">{r.reason}</p>
                <div className="mt-2 flex gap-2">
                  <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                    {t(`analysis.recommendations.category.${r.category}`)}
                  </span>
                  <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                    {t(`analysis.recommendations.effort.${r.effort}`)}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* AI explanation */}
      <div>
        <Button variant="ghost" onClick={runExplain} disabled={explaining}>
          {explaining ? t('common.loading') : `✨ ${t('analysis.explain')}`}
        </Button>
        {explainDisabled && (
          <p className="mt-2 text-sm text-slate-500">{t('analysis.explainDisabled')}</p>
        )}
        <ErrorText>{explainError}</ErrorText>
        {explanation && (
          <Card className="mt-2 border-brand-200 bg-brand-50">
            <div className="mb-1 text-xs font-semibold text-brand-700">
              {t('analysis.explanationTitle')}
            </div>
            <p className="text-sm leading-relaxed text-slate-700">{explanation}</p>
          </Card>
        )}
      </div>
    </div>
  )
}
