declare const __BUILD_VERSION__: string | undefined

declare global {
  interface Window {
    Paddle?: any
  }

  const __BUILD_VERSION__: string | undefined
}

export {}
