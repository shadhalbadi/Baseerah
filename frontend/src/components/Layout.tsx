import { Link, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { useAuth } from '../auth/AuthContext'
import { LanguageSwitcher } from './LanguageSwitcher'

export function Layout() {
  const { t } = useTranslation()
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">💧</span>
            <div className="leading-tight">
              <div className="text-lg font-bold text-brand-700">{t('app.name')}</div>
              <div className="text-xs text-slate-500">{t('app.tagline')}</div>
            </div>
          </Link>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            {user && (
              <button
                onClick={logout}
                className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100"
              >
                {t('common.logout')}
              </button>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
