import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import enTranslation from './locales/en/translation.json'
import zhTranslation from './locales/zh/translation.json'

// 根据构建版本确定默认语言
const isEnglishVersion = typeof __BUILD_VERSION__ !== 'undefined' && __BUILD_VERSION__ === 'english'
const defaultLanguage = isEnglishVersion ? 'en' : 'zh'

// 支持的语言列表
const SUPPORTED_LANGUAGES = ['en', 'zh']

const resources = {
  en: {
    translation: enTranslation
  },
  zh: {
    translation: zhTranslation
  }
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: defaultLanguage,
    lng: defaultLanguage,
    supportedLngs: SUPPORTED_LANGUAGES,

    interpolation: {
      escapeValue: false
    },

    react: {
      useSuspense: false
    },

    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage']
    }
  })

export default i18n
