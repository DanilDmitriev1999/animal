'use client';

import { GlassCard } from "@/components/ui/GlassCard";
import { Header } from "@/components/layout/Header";
import { TrackCard } from "@/components/ui/TrackCard";
import { Send } from "lucide-react";
import * as React from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ChatMessage } from "@/components/ui/ChatMessage";

const tracks = [
    {
      title: "Введение в нейронные сети",
      description: "Изучите основы нейронных сетей, от отдельных нейронов до сложных архитектур.",
      progress: 25,
      slug: "intro-to-neural-networks",
    },
    {
      title: "Продвинутые SQL запросы",
      description: "Освойте сложные соединения, оконные функции и оптимизацию производительности для больших наборов данных.",
      progress: 75,
      slug: "advanced-sql-queries",
    },
    {
      title: "Визуализация данных с D3.js",
      description: "Создавайте интерактивные и красивые диаграммы и графики с нуля, используя библиотеку D3.js.",
      progress: 50,
      slug: "data-visualization-with-d3js",
    },
];

const mockMessages = [
    { role: "assistant", message: "Привет! Я твой AI-помощник. Чем могу помочь сегодня на твоем пути к знаниям?" },
    { role: "user", message: "Создай мне, пожалуйста, учебный трек по теме 'Продвинутый Go Concurrency'.", avatarUrl: "https://github.com/shadcn.png" },
    { role: "assistant", message: "Конечно! Трек 'Продвинутый Go Concurrency' создан. Он включает в себя темы о горутинах, каналах, select, и паттернах конкурентности. Хотите начать с основ или перейти к более сложным темам?" },
    { role: "user", message: "Давай начнем с основ. Что такое горутины?", avatarUrl: "https://github.com/shadcn.png" },
    { role: "assistant", message: "Горутины — это легковесные потоки, управляемые средой выполнения Go. Они позволяют выполнять функции конкурентно. В отличие от системных потоков, горутины имеют небольшой начальный размер стека, который может расти по мере необходимости. Это делает их очень эффективными для создания тысяч и даже миллионов конкурентных задач." },
    { role: "user", message: "Интересно. А как насчет каналов?", avatarUrl: "https://github.com/shadcn.png" },
    { role: "assistant", message: "Каналы — это типизированные конвейеры, через которые можно отправлять и получать значения с помощью оператора `<-`. Они являются основным способом коммуникации между горутинами, обеспечивая их синхронизацию без явного использования блокировок. Хотите пример кода?" },
    { role: "user", message: "Да, пожалуйста!", avatarUrl: "https://github.com/shadcn.png" },
    { role: "assistant", message: "```go\npackage main\n\nimport (\n\t\"fmt\"\n\t\"time\"\n)\n\nfunc worker(done chan bool) {\n\tfmt.Print(\"working...\")\n\ttime.Sleep(time.Second)\n\tfmt.Println(\"done\")\n\n\tdone <- true\n}\n\nfunc main() {\n\tdone := make(chan bool, 1)\n\tgo worker(done)\n\n\t<-done\n}\n```\nЭтот пример демонстрирует, как запустить фоновую задачу в горутине и дождаться ее завершения с помощью канала." },
    { role: "user", message: "Спасибо, это очень полезно. Я готов двигаться дальше.", avatarUrl: "https://github.com/shadcn.png" },
];

const TracksPage = () => {
  const chatContainerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [mockMessages]);

  return (
    <div className="flex flex-col h-screen">
      <Header isAuthenticated={true} />
      <main className="container mx-auto px-4 py-8 flex-1">
        <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold text-text-primary">Ваши треки</h1>
            <span className="text-text-secondary">{tracks.length} треков</span>
        </div>

        <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3 mb-8">
          {tracks.map((track) => (
            <Link key={track.slug} href={`/tracks/${track.slug}`}>
                <TrackCard {...track} />
            </Link>
          ))}
        </div>
      </main>

      <div className="sticky bottom-0 left-0 right-0 bg-background/50 backdrop-blur-lg">
          <div className="container mx-auto p-4">
            <div className="space-y-6 pr-4 max-h-[40vh] overflow-y-auto pb-4" ref={chatContainerRef}>
              {mockMessages.map((msg, index) => (
                <ChatMessage key={index} role={msg.role as "user" | "assistant"} message={msg.message} avatarUrl={msg.avatarUrl} />
              ))}
            </div>
            <GlassCard className="p-2">
                <div className="flex gap-2">
                    <Input 
                        placeholder="Спросите что-нибудь о вашем проекте или курсе..."
                        className="bg-transparent border-none focus-visible:ring-0 focus-visible:ring-offset-0 text-base"
                    />
                    <Button size="icon" aria-label="Отправить сообщение">
                        <Send className="h-5 w-5" />
                    </Button>
                </div>
            </GlassCard>
          </div>
      </div>
    </div>
  );
};

export default TracksPage; 