'use client'

import * as React from 'react'
import { useGlassTheme } from '@/hooks/useGlassTheme'

export function ThemeApplier() {
  const { theme } = useGlassTheme()

  React.useEffect(() => {
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(theme)
  }, [theme])

  return null
}


