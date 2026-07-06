import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { api } from '../api/client'
import type { Property, PropertyType } from '../types'
import { Button, Card, ErrorText, Field, Input, Select } from '../components/ui'

const TYPES: PropertyType[] = ['apartment', 'villa', 'office', 'shop', 'other']

export function PropertiesPage() {
  const { t } = useTranslation()
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)

  const [name, setName] = useState('')
  const [type, setType] = useState<PropertyType>('apartment')
  const [region, setRegion] = useState('')
  const [occupants, setOccupants] = useState('')
  const [busy, setBusy] = useState(false)

  const load = () => {
    setLoading(true)
    api
      .listProperties()
      .then(setProperties)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await api.createProperty({
        name,
        type,
        region: region || null,
        occupants: occupants ? Number(occupants) : null,
      })
      setName('')
      setRegion('')
      setOccupants('')
      setShowForm(false)
      load()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{t('properties.title')}</h1>
        <Button onClick={() => setShowForm((s) => !s)}>
          {showForm ? t('common.cancel') : t('properties.add')}
        </Button>
      </div>

      {showForm && (
        <Card>
          <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
            <Field label={t('properties.name')}>
              <Input value={name} onChange={(e) => setName(e.target.value)} required />
            </Field>
            <Field label={t('properties.type')}>
              <Select value={type} onChange={(e) => setType(e.target.value as PropertyType)}>
                {TYPES.map((ty) => (
                  <option key={ty} value={ty}>
                    {t(`properties.types.${ty}`)}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label={`${t('properties.region')} (${t('common.optional')})`}>
              <Input value={region} onChange={(e) => setRegion(e.target.value)} />
            </Field>
            <Field label={`${t('properties.occupants')} (${t('common.optional')})`}>
              <Input
                type="number"
                min={0}
                value={occupants}
                onChange={(e) => setOccupants(e.target.value)}
              />
            </Field>
            <div className="sm:col-span-2">
              <Button type="submit" disabled={busy}>
                {busy ? t('common.loading') : t('common.save')}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <ErrorText>{error}</ErrorText>

      {loading ? (
        <p className="text-slate-500">{t('common.loading')}</p>
      ) : properties.length === 0 ? (
        <Card>
          <p className="text-slate-500">{t('properties.empty')}</p>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {properties.map((p) => (
            <Link key={p.id} to={`/properties/${p.id}`}>
              <Card className="h-full transition hover:border-brand-400 hover:shadow-md">
                <div className="text-lg font-semibold text-slate-900">{p.name}</div>
                <div className="mt-1 text-sm text-slate-500">
                  {t(`properties.types.${p.type}`)}
                  {p.region ? ` · ${p.region}` : ''}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
