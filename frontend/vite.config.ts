import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  // 根据构建模式确定配置
  const isEnglish = mode === 'english'

  return {
    plugins: [react()],
    server: {
      port: 3006,
      proxy: {
        '/api': {
          target: 'http://localhost:8006',
          changeOrigin: true
        }
      }
    },
    build: {
      outDir: isEnglish ? 'dist-en' : 'dist-zh',
      emptyOutDir: true,
      rollupOptions: {
        input: {
          main: resolve(__dirname, 'index.html')
        },
        output: {
          entryFileNames: 'assets/[name].[hash].js',
          chunkFileNames: 'assets/[name].[hash].js',
          assetFileNames: 'assets/[name].[hash].[ext]'
        }
      }
    },
    define: {
      // 根据构建模式定义全局变量
      __BUILD_VERSION__: JSON.stringify(isEnglish ? 'english' : 'chinese')
    }
  }
})
