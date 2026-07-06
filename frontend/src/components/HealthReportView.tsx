import { useTranslation } from 'react-i18next'

import type { ConsumptionStatus, HealthReport } from '../types'
import { Card } from './ui'

const STATUS_STYLES: Record<ConsumptionStatus, string> = {
  normal: 'bg-emerald-100 text-emerald-800',
  warning: 'bg-amber-100 text-amber-800',
  anomaly: 'bg-red-100 text-red-800',
  insufficient_data: 'bg-slate-100 text-slate-600',
}

export function HealthReportView({ report }: { report: HealthReport }) {
  const { t } = useTranslation()
  const { floor_rise, base_load, slab, timeline, recommendations } = report
  const flagged = timeline.filter((e) => e.status === 'warning' || e.status === 'anomaly')

  return (
    <div className="space-y-4">
      {/* Headline */}
      <Card className="border-brand-200 bg-brand-50">
        <div className="text-xs font-semibold uppercase tracking-wide text-brand-700">
          {t('report.headlineLabel')}
        </div>
        <div className="mt-1 text-3xl font-bold text-slate-900">
          {report.headline_annual_waste} {report.currency}
        </div>
        <p className="mt-1 text-sm text-slate-600">
          {t('report.headlineCaption', { count: report.periods_analyzed })}
        </p>
      </Card>

      {/* Floor rise */}
      <Card className={floor_rise.suspected ? 'border-amber-300 bg-amber-50' : ''}>
        <h3 className="font-semibold text-slate-900">
          {floor_rise.suspected
            ? `⚠️ ${t('report.floor.suspectedTitle')}`
            : `✅ ${t('report.floor.clearTitle')}`}
        </h3>
        <p className="mt-1 text-sm text-slate-600">{floor_rise.reason}</p>
        {floor_rise.ratio !== null && (
          <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-500">
            <span>
              {t('report.floor.priorFloor')}: {floor_rise.prior_floor} {report.unit}
            </span>
            <span>
              {t('report.floor.recentFloor')}: {floor_rise.recent_floor} {report.unit}
            </span>
          </div>
        )}
      </Card>

      {/* Base load (electricity) */}
      {base_load && (
        <Card>
          <h3 className="font-semibold text-slate-900">{t('report.baseLoad.title')}</h3>
          <div className="mt-3 grid gap-4 sm:grid-cols-3">
            <div>
              <div className="text-xs text-slate-500">{t('report.baseLoad.monthly')}</div>
              <div className="text-xl font-bold text-slate-900">
                {base_load.monthly_consumption} {report.unit}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-500">{t('report.baseLoad.cost')}</div>
              <div className="text-xl font-bold text-slate-900">
                {base_load.monthly_cost} {report.currency}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-500">{t('report.baseLoad.share')}</div>
              <div className="text-xl font-bold text-slate-900">
                {Math.round(base_load.share_of_total * 100)}%
              </div>
            </div>
          </div>
          <p className="mt-2 text-xs text-slate-400">{t('report.baseLoad.hint')}</p>
        </Card>
      )}

      {/* Tariff slab position (electricity) */}
      {slab && (
        <Card>
          <h3 className="font-semibold text-slate-900">{t('report.slab.title')}</h3>
          <div className="mt-3 grid gap-4 sm:grid-cols-2">
            <div>
              <div className="text-xs text-slate-500">{t('report.slab.marginalRate')}</div>
              <div className="text-xl font-bold text-slate-900">
                {Math.round(slab.marginal_rate * 1000 * 10) / 10}{' '}
                <span className="text-sm font-normal">{t('report.slab.baisaPerKwh')}</span>
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-500">{t('report.slab.gap')}</div>
              <div className="text-xl font-bold text-slate-900">
                {slab.gap_to_next_slab === null
                  ? t('report.slab.topSlab')
                  : `${slab.gap_to_next_slab} kWh`}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Anomaly timeline */}
      <Card>
        <h3 className="mb-3 font-semibold text-slate-900">{t('report.timeline.title')}</h3>
        {flagged.length === 0 ? (
          <p className="text-sm text-slate-500">{t('report.timeline.empty')}</p>
        ) : (
          <ul className="space-y-2">
            {flagged.map((e) => (
              <li
                key={e.period_start}
                className="flex items-center justify-between gap-3 rounded-lg border border-slate-100 p-3 text-sm"
              >
                <div>
                  <span
                    className={`me-2 rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_STYLES[e.status]}`}
                  >
                    {t(`analysis.status.${e.status}`)}
                  </span>
                  <span className="text-slate-600">
                    {e.period_start} → {e.period_end}
                  </span>
                </div>
                <div className="text-end">
                  <div className="font-medium text-slate-900">
                    {e.consumption} {report.unit}
                  </div>
                  {e.excess_cost > 0 && (
                    <div className="text-xs text-red-600">
                      {t('report.timeline.excess')}: {e.excess_cost} {report.currency}
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
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
                      <span className="text-slate-400">{t('report.perYear')}</span>
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
    </div>
  )
}
