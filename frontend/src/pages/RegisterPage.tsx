import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { useAuth } from '../auth/AuthContext'
import { ApiError } from '../api/client'
import { Button, Card, ErrorText, Field, Input } from '../components/ui'

export function RegisterPage() {
  const { t } = useTranslation()
  const { register } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await register(email, name, password)
      navigate('/')
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 409
          ? t('auth.emailTaken')
          : String((err as Error).message),
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <Card>
        <h1 className="mb-5 text-xl font-bold text-slate-900">{t('auth.registerTitle')}</h1>
        <form onSubmit={submit} className="space-y-4">
          <Field label={t('auth.name')}>
            <Input value={name} onChange={(e) => setName(e.target.value)} required autoComplete="name" />
          </Field>
          <Field label={t('auth.email')}>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </Field>
          <Field label={t('auth.password')}>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
            />
            <span className="mt-1 block text-xs text-slate-400">{t('auth.passwordHint')}</span>
          </Field>
          <ErrorText>{error}</ErrorText>
          <Button type="submit" disabled={busy} className="w-full">
            {busy ? t('common.loading') : t('auth.registerButton')}
          </Button>
        </form>
        <Link to="/login" className="mt-4 block text-center text-sm text-brand-700 hover:underline">
          {t('auth.toLogin')}
        </Link>
      </Card>
    </div>
  )
}
