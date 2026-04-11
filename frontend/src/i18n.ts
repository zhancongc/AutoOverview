import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import HttpApi from 'i18next-http-backend'
import enTranslation from '../locales/en/translation.json'
import zhTranslation from '../locales/zh/translation.json'

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
  .use(HttpApi)
  .use(LanguageDetector)
  .use(initReactI18next, {
    resources,
    fallbackLng: 'en', // 默认语言为英文
    lng: 'en', // 初始语言为英文
    supportedLngs: SUPPORTED_LANGUAGES,

    interpolation: {
      escapeValue: false
    },

    react: {
      useSuspense: false
    },

    detection: {
      // 语言检测顺序
      order: ['localStorage', 'navigator'],

      // localStorage 中存储语言设置的 key
      caches: ['localStorage'],

      // 默认语言
      fallbackLng: 'en',

      // 只检查白名单中的语言
      checkWhitelist: true
    }
  })

export default i18n
