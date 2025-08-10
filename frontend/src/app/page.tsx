'use client'

import { GlassCard } from "@/components/ui/GlassCard";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Zap, Sun, Moon } from "lucide-react";
import Link from "next/link";
import * as React from "react";
import { useGlassTheme } from "@/hooks/useGlassTheme";

// AICODE-NOTE: Smaller, less intrusive theme toggle
const ThemeToggle = () => {
  const { theme, toggleTheme } = useGlassTheme()

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      aria-label="Переключить тему"
      className="fixed top-4 right-4 z-50 h-8 w-8 rounded-full bg-white/10 dark:bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-white/20 dark:hover:bg-white/20 transition-all"
    >
      {theme === 'dark' ? (
        <Sun className="h-4 w-4 text-text-primary" />
      ) : (
        <Moon className="h-4 w-4 text-text-primary" />
      )}
    </Button>
  )
}

// AICODE-NOTE: Enhanced header for landing page
const LandingHeader = () => (
  <header className="relative container mx-auto flex items-center justify-between p-6 text-text-primary">
    <Link href="/" className="flex items-center gap-3 group">
      <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
        <Zap className="h-6 w-6 text-white" />
      </div>
      <span className="text-2xl font-bold text-text-primary">
        AI Learning
      </span>
    </Link>
    <nav className="flex items-center gap-4">
      <Button variant="ghost" className="hidden sm:flex text-text-primary hover:bg-white/10 dark:hover:bg-white/10">
        Войти
      </Button>
      <Button className="bg-primary hover:bg-primary/90 text-white shadow-lg">
        Регистрация
      </Button>
    </nav>
  </header>
)

const LandingFooter = () => (
  <footer className="container mx-auto py-12 text-center">
    <GlassCard variant="subtle" size="md" className="inline-block">
      <p className="text-text-secondary">
        © {new Date().getFullYear()} AI Learning. Все права защищены.
      </p>
    </GlassCard>
  </footer>
)

export default function Home() {
  return (
    <>
      <ThemeToggle />
      <LandingHeader />
      <main className="relative">
        {/* AICODE-NOTE: Hero section with enhanced typography and glass effects */}
        <section className="container mx-auto px-6 py-16 lg:py-24 text-center relative">
          <div className="relative z-10">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-bold leading-tight tracking-tight mb-8 text-text-primary">
              Будущее обучения,<br />
              <span className="bg-gradient-to-r from-primary via-primary to-primary/80 bg-clip-text text-transparent">
                персонализированное
              </span><br />
              с помощью ИИ
            </h1>
            
            <p className="mx-auto mt-8 max-w-3xl text-lg sm:text-xl lg:text-2xl text-text-secondary leading-relaxed font-medium">
              Создавайте динамические учебные планы, получайте мгновенные объяснения и осваивайте новые навыки быстрее, чем когда-либо.
            </p>
            
            <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-6">
              <Link href="/tracks">
                <Button size="lg" className="text-lg px-8 py-4 h-auto bg-primary hover:bg-primary/90 text-white shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105">
                  Начать бесплатно
                </Button>
              </Link>
              <Button 
                variant="outline" 
                size="lg" 
                className="text-lg px-8 py-4 h-auto glass-morphism hover:bg-white/10 dark:hover:bg-white/10 transition-all duration-300 text-text-primary border-white/20"
              >
                Узнать больше
              </Button>
            </div>
          </div>
        </section>
      </main>
      
      <LandingFooter />
    </>
  );
}
