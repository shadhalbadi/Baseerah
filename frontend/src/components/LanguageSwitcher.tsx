import { useTranslation } from 'react-i18next'

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation()
  const toggle = () => void i18n.changeLanguage(i18n.language === 'ar' ? 'en' : 'ar')
  return (
    <button
      onClick={toggle}
      className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100"
    >
      {t('common.language')}
    </button>
  )
}
