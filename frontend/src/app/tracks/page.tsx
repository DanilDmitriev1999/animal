'use client';

import { Header } from "@/components/layout/Header";
import { TrackCard } from "@/components/ui/TrackCard";
import * as React from "react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Plus } from "lucide-react";
import { api, type Track } from "@/lib/api";

// AICODE-NOTE: Мок-данные удалены. Список будет подгружаться через API.
type TrackListItem = { title: string; description?: string; slug: string };
const TracksPage = () => {
  const [tracks, setTracks] = React.useState<TrackListItem[]>([]);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let mounted = true
    api
      .getTracks()
      .then((list: Track[]) => {
        if (!mounted) return
        setTracks(list.map((t) => ({ title: t.title, description: t.description, slug: t.slug })))
      })
      .catch((e) => mounted && setError(String(e)))
      .finally(() => mounted && setLoading(false))
    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="flex flex-col min-h-screen">
      <Header isAuthenticated={true} />
      <main className="container mx-auto px-4 py-6 flex-1">
        <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-text-primary">Ваши треки</h1>
            <div className="flex items-center gap-3">
              <span className="text-text-secondary hidden sm:inline">{tracks.length} треков</span>
              <Link href="/tracks/create">
                <Button type="button" className="gap-2">
                  <Plus className="h-4 w-4" />
                  Создать трек
                </Button>
              </Link>
            </div>
        </div>
        {loading ? (
          <div className="text-text-secondary">Загрузка…</div>
        ) : error ? (
          <div className="text-red-500">Ошибка загрузки: {error}</div>
        ) : tracks.length === 0 ? (
          <div className="text-text-secondary">У вас пока нет треков. Создайте первый.</div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {tracks.map((track) => (
              <Link key={track.slug} href={`/tracks/${track.slug}`} className="block">
                <TrackCard
                  title={track.title}
                  description={track.description ?? ''}
                  className="h-full"
                  size="lg"
                />
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default TracksPage; 