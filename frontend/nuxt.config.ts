// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxt/ui', '@nuxt/test-utils/module'],
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      apiMode: 'mock',
      apiBase: 'http://127.0.0.1:8000',
    },
  },
  typescript: {
    tsConfig: {
      include: ['../test/nuxt/**/*.ts'],
    },
  },
})
