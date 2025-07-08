'use client' // For theme toggle state

import { Button } from "@/components/ui/button"
import { Zap, Sun, Moon } from "lucide-react"
import Link from "next/link"
import Image from "next/image"
import * as React from "react"
import { useGlassTheme } from "@/hooks/useGlassTheme"

export interface HeaderProps {
  isAuthenticated?: boolean
}

export const Header = ({ isAuthenticated = false }: HeaderProps) => {
  const { theme, toggleTheme } = useGlassTheme()

  return (
    <header className="container mx-auto flex items-center justify-between p-6 text-text-primary">
      <Link href="/" className="flex items-center gap-3 group">
        <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
          <Zap className="h-6 w-6 text-white" />
        </div>
        <span className="text-2xl font-bold text-text-primary">AI Learning</span>
      </Link>
      <nav className="flex items-center gap-4">
        {isAuthenticated ? (
          <>
            <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme" className="hover:bg-white/10 dark:hover:bg-white/10">
                {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>
            <Link href="/profile">
                <Image
                src="https://github.com/shadcn.png" // Placeholder avatar
                alt="User avatar"
                width={32}
                height={32}
                className="rounded-full"
                />
            </Link>
          </>
        ) : (
          <>
            <Button variant="ghost" className="text-text-primary hover:bg-white/10 dark:hover:bg-white/10">Войти</Button>
            <Button className="bg-primary hover:bg-primary/90 text-white shadow-lg">Регистрация</Button>
          </>
        )}
      </nav>
    </header>
  )
} 