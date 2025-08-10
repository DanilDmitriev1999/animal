import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import * as React from "react"

export interface ContentTabsProps {
  chatContent: React.ReactNode
  practiceContent: React.ReactNode
  simulationContent: React.ReactNode
  // AICODE-NOTE: Optional synopsis content for mobile view; hidden on desktop where a side panel is used
  synopsisContent?: React.ReactNode
  // AICODE-NOTE: Allow parent to control active tab (e.g., to switch to synopsis on mobile by button)
  value?: string
  onValueChange?: (value: string) => void
  className?: string
}

export function ContentTabs({
  chatContent,
  practiceContent,
  simulationContent,
  synopsisContent,
  value,
  onValueChange,
  className
}: ContentTabsProps) {
  return (
    <Tabs defaultValue="chat" value={value} onValueChange={onValueChange} className={className}>
      {/* AICODE-NOTE: 4 columns on mobile to include optional Synopsis tab; on desktop it stays 3 */}
      <TabsList className="grid w-full grid-cols-4 lg:grid-cols-3 bg-transparent p-0">
        <TabsTrigger value="chat">Чат</TabsTrigger>
        <TabsTrigger value="practice">Практика</TabsTrigger>
        <TabsTrigger value="simulation">Симуляция</TabsTrigger>
        {synopsisContent ? (
          <TabsTrigger value="synopsis" className="lg:hidden">Конспект</TabsTrigger>
        ) : null}
      </TabsList>
      <TabsContent value="chat" className="mt-4">
        {chatContent}
      </TabsContent>
      <TabsContent value="practice" className="mt-4">
        {practiceContent}
      </TabsContent>
      <TabsContent value="simulation" className="mt-4">
        {simulationContent}
      </TabsContent>
      {synopsisContent ? (
        <TabsContent value="synopsis" className="mt-4 lg:hidden">
          {synopsisContent}
        </TabsContent>
      ) : null}
    </Tabs>
  )
} 