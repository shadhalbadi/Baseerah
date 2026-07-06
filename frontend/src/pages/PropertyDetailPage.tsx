import { useCallback, useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { api, ApiError } from '../api/client'
import type { AnalysisResult, Bill, HealthReport, Property, UtilityType } from '../types'
import { AnalysisView } from '../components/AnalysisView'
import { ConsumptionChart } from '../components/ConsumptionChart'
import { HealthReportView } from '../components/HealthReportView'
import { Button, Card, ErrorText, Field, Input, Select } from '../components/ui'

export function PropertyDetailPage() {
  const { t } = useTranslation()
  const { id } = useParams()
  const propertyId = Number(id)

  const [property, setProperty] = useState<Property | null>(null)
  const [bills, setBills] = useState<Bill[]>([])
  const [error, setError] = useState('')

  // add-bill form
  const [utility, setUtility] = useState<UtilityType>('water')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [consumption, setConsumption] = useState('')
  const [cost, setCost] = useState('')
  const [busy, setBusy] = useState(false)

  // OCR scan
  const fileInput = useRef<HTMLInputElement>(null)
  const [scanning, setScanning] = useState(false)
  const [scanWarnings, setScanWarnings] = useState<string[]>([])
  const [scanNote, setScanNote] = useState('')

  // analysis
  const [analysisUtility, setAnalysisUtility] = useState<UtilityType>('water')
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [analysisError, setAnalysisError] = useState('')
  const [analyzing, setAnalyzing] = useState(false)

  // health report
  const [report, setReport] = useState<HealthReport | null>(null)
  const [reportLoading, setReportLoading] = useState(false)

  const loadBills = useCallback(() => {
    api.listBills(propertyId).then(setBills).catch((e: Error) => setError(e.message))
  }, [propertyId])

  useEffect(() => {
    api.getProperty(propertyId).then(setProperty).catch((e: Error) => setError(e.message))
    loadBills()
  }, [propertyId, loadBills])

  const scanBill = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = '' // allow re-selecting the same file
    if (!file) return
    setScanning(true)
    setScanWarnings([])
    setScanNote('')
    setError('')
    try {
      const result = await api.extractBill(propertyId, file)
      if (!result.enabled) {
        setScanNote(t('scan.disabled'))
        return
      }
      const bill = result.bill
      if (!bill) return
      if (bill.utility_type) setUtility(bill.utility_type)
      if (bill.period_start) setStart(bill.period_start)
      if (bill.period_end) setEnd(bill.period_end)
      if (bill.consumption !== null) setConsumption(String(bill.consumption))
      if (bill.cost !== null) setCost(String(bill.cost))
      setScanWarnings(bill.warnings)
      setScanNote(t(`scan.confidence.${bill.confidence}`))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setScanning(false)
    }
  }

  const addBill = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await api.createBill(propertyId, {
        utility_type: utility,
        period_start: start,
        period_end: end,
        consumption: Number(consumption),
        cost: Number(cost),
      })
      setStart('')
      setEnd('')
      setConsumption('')
      setCost('')
      loadBills()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const runAnalysis = async () => {
    setAnalyzing(true)
    setAnalysisError('')
    setAnalysis(null)
    setReport(null)
    try {
      setAnalysis(await api.getAnalysis(propertyId, analysisUtility))
    } catch (e) {
      setAnalysisError(
        e instanceof ApiError && e.status === 404 ? t('analysis.noBills') : (e as Error).message,
      )
    } finally {
      setAnalyzing(false)
    }
  }

  const runReport = async () => {
    setReportLoading(true)
    setAnalysisError('')
    setAnalysis(null)
    setReport(null)
    try {
      setReport(await api.getReport(propertyId, analysisUtility))
    } catch (e) {
      setAnalysisError(
        e instanceof ApiError && e.status === 422 ? t('report.needMoreBills') : (e as Error).message,
      )
    } finally {
      setReportLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/" className="text-sm text-brand-700 hover:underline">
          ← {t('common.back')}
        </Link>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">{property?.name ?? '…'}</h1>
        {property && (
          <p className="text-sm text-slate-500">
            {t(`properties.types.${property.type}`)}
            {property.region ? ` · ${property.region}` : ''}
          </p>
        )}
      </div>

      <ErrorText>{error}</ErrorText>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Bills */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">{t('bills.title')}</h2>
          <Card>
            <div className="mb-3 flex items-center justify-between gap-3 border-b border-slate-100 pb-3">
              <span className="text-sm text-slate-500">{t('scan.hint')}</span>
              <input
                ref={fileInput}
                type="file"
                accept="image/jpeg,image/png,image/webp,application/pdf"
                className="hidden"
                onChange={scanBill}
              />
              <Button variant="ghost" onClick={() => fileInput.current?.click()} disabled={scanning}>
                {scanning ? t('common.loading') : `📷 ${t('scan.button')}`}
              </Button>
            </div>
            {scanNote && <p className="mb-2 text-sm text-slate-600">{scanNote}</p>}
            {scanWarnings.length > 0 && (
              <ul className="mb-3 space-y-1 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                {scanWarnings.map((w, i) => (
                  <li key={i}>⚠ {w}</li>
                ))}
              </ul>
            )}
            <form onSubmit={addBill} className="grid gap-3 sm:grid-cols-2">
              <Field label={t('bills.utility')}>
                <Select value={utility} onChange={(e) => setUtility(e.target.value as UtilityType)}>
                  <option value="water">{t('bills.water')}</option>
                  <option value="electricity">{t('bills.electricity')}</option>
                </Select>
              </Field>
              <div />
              <Field label={t('bills.periodStart')}>
                <Input type="date" value={start} onChange={(e) => setStart(e.target.value)} required />
              </Field>
              <Field label={t('bills.periodEnd')}>
                <Input type="date" value={end} onChange={(e) => setEnd(e.target.value)} required />
              </Field>
              <Field label={t('bills.consumption')}>
                <Input
                  type="number"
                  step="any"
                  min={0}
                  value={consumption}
                  onChange={(e) => setConsumption(e.target.value)}
                  required
                />
              </Field>
              <Field label={t('bills.cost')}>
                <Input
                  type="number"
                  step="any"
                  min={0}
                  value={cost}
                  onChange={(e) => setCost(e.target.value)}
                  required
                />
              </Field>
              <div className="sm:col-span-2">
                <Button type="submit" disabled={busy}>
                  {busy ? t('common.loading') : t('bills.add')}
                </Button>
              </div>
            </form>
          </Card>

          {bills.length === 0 ? (
            <p className="text-sm text-slate-500">{t('bills.empty')}</p>
          ) : (
            <Card>
              <table className="w-full text-sm">
                <tbody>
                  {bills.map((b) => (
                    <tr key={b.id} className="border-b border-slate-100 last:border-0">
                      <td className="py-2">{t(`bills.${b.utility_type}`)}</td>
                      <td className="py-2 text-slate-500">{b.period_end}</td>
                      <td className="py-2 text-end">
                        {b.consumption} {b.unit}
                      </td>
                      <td className="py-2 text-end font-medium">
                        {b.cost} {b.currency}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}
        </div>

        {/* Analysis */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">{t('analysis.title')}</h2>
          <Card>
            <div className="flex items-end gap-3">
              <div className="flex-1">
                <Field label={t('analysis.utilityToAnalyze')}>
                  <Select
                    value={analysisUtility}
                    onChange={(e) => setAnalysisUtility(e.target.value as UtilityType)}
                  >
                    <option value="water">{t('bills.water')}</option>
                    <option value="electricity">{t('bills.electricity')}</option>
                  </Select>
                </Field>
              </div>
              <Button onClick={runAnalysis} disabled={analyzing || reportLoading}>
                {analyzing ? t('common.loading') : t('analysis.run')}
              </Button>
              <Button variant="ghost" onClick={runReport} disabled={analyzing || reportLoading}>
                {reportLoading ? t('common.loading') : t('report.run')}
              </Button>
            </div>
          </Card>
          <ErrorText>{analysisError}</ErrorText>
          {report && <HealthReportView report={report} />}
          {analysis && (
            <>
              <Card>
                <h3 className="mb-2 font-semibold text-slate-900">{t('analysis.chartTitle')}</h3>
                <ConsumptionChart
                  points={bills
                    .filter((b) => b.utility_type === analysis.utility_type)
                    .map((b) => ({ label: b.period_end, value: b.consumption }))}
                  forecast={analysis.forecast.predicted_consumption}
                  unit={analysis.latest.unit}
                />
              </Card>
              <AnalysisView result={analysis} propertyId={propertyId} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
