import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import en from './locales/en.json'
import ar from './locales/ar.json'

const LANG_KEY = 'baseerah_lang'
const saved = localStorage.getItem(LANG_KEY) ?? 'en'

void i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    ar: { translation: ar },
  },
  lng: saved,
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})

function applyDir(lng: string) {
  const dir = lng === 'ar' ? 'rtl' : 'ltr'
  document.documentElement.setAttribute('dir', dir)
  document.documentElement.setAttribute('lang', lng)
}

applyDir(saved)

i18n.on('languageChanged', (lng) => {
  localStorage.setItem(LANG_KEY, lng)
  applyDir(lng)
})

export default i18n
