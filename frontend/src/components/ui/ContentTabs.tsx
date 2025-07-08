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
  className?: string
}

export function ContentTabs({
  chatContent,
  practiceContent,
  simulationContent,
  className
}: ContentTabsProps) {
  return (
    <Tabs defaultValue="chat" className={className}>
      <TabsList className="grid w-full grid-cols-3 bg-transparent p-0">
        <TabsTrigger value="chat">Chat</TabsTrigger>
        <TabsTrigger value="practice">Practice</TabsTrigger>
        <TabsTrigger value="simulation">Simulation</TabsTrigger>
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
    </Tabs>
  )
} 