import { Navigate, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { useAuth } from '../auth/AuthContext'

export function ProtectedRoute() {
  const { user, loading } = useAuth()
  const { t } = useTranslation()

  if (loading) {
    return <div className="p-8 text-center text-slate-500">{t('common.loading')}</div>
  }
  return user ? <Outlet /> : <Navigate to="/login" replace />
}
