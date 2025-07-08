'use client'

import * as React from "react"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Header } from "@/components/layout/Header"
import { LiveSynopsis } from "@/components/ui/LiveSynopsis"
import { ContentTabs } from "@/components/ui/ContentTabs"
import { ChatMessage } from "@/components/ui/ChatMessage"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Send } from "lucide-react"
import { GlassCard } from "@/components/ui/GlassCard"

// Mock data for a single track page
const trackData = {
    name: "Introduction to Neural Networks",
    slug: "intro-to-neural-networks",
    synopsisPoints: [
        "A neural network is a series of algorithms that endeavors to recognize underlying relationships in a set of data.",
        "Key components include neurons (nodes), layers (input, hidden, output), and weights.",
        "The activation function determines the output of a node given a set of inputs.",
    ],
    chatMessages: [
        { role: "assistant", message: "Hello! Let's start with the basics. A neural network is inspired by the human brain. What specific part of this concept would you like to explore first? We can discuss neurons, layers, or activation functions." },
        { role: "user", message: "Tell me more about activation functions. Why are they necessary?", avatarUrl: "https://github.com/shadcn.png" },
        { role: "assistant", message: "Activation functions are crucial because they introduce non-linearity into the network. Without them, a neural network, no matter how many layers it has, would behave just like a single-layer linear regression model. This non-linearity allows the network to learn complex patterns from the data. Common activation functions include Sigmoid, Tanh, and ReLU (Rectified Linear Unit)." },
        { role: "user", message: "What's the difference between them? Which one is most commonly used?", avatarUrl: "https://github.com/shadcn.png" },
        { role: "assistant", message: "Sigmoid and Tanh are 'saturating' non-linearities, which means they can slow down or even stop the learning process (the 'vanishing gradient' problem). ReLU, on the other hand, does not saturate for positive inputs and is computationally very efficient. For these reasons, ReLU has become the default activation function for many types of neural networks, especially in deep learning." },
        { role: "user", message: "That makes sense. Could you show a simple code example of a neuron with a ReLU activation function?", avatarUrl: "https://github.com/shadcn.png" },
        { role: "assistant", message: "Of course! Here is a simple Python example:\n\n```python\nimport numpy as np\n\ndef relu(x):\n    return np.maximum(0, x)\n\n# Example of a single neuron's output\ninputs = np.array([0.5, -1.2, 2.3])\nweights = np.array([0.8, -0.4, 1.1])\nbias = -0.5\n\nlinear_combination = np.dot(inputs, weights) + bias\noutput = relu(linear_combination)\n\nprint(f\"Linear Combination: {linear_combination:.2f}\")\nprint(f\"Output after ReLU: {output:.2f}\")\n```\n\nThis shows how the weighted sum of inputs plus a bias is passed through the ReLU function to produce the neuron's final output." },
        { role: "user", message: "Great, thanks! I understand the basics now.", avatarUrl: "https://github.com/shadcn.png" }
    ]
}

const TrackPage = ({ params }: { params: { slug: string } }) => {
  const chatContainerRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [trackData.chatMessages])

  const chatContent = (
    <div ref={chatContainerRef} className="space-y-6 pr-4 max-h-[400px] overflow-y-auto">
      {trackData.chatMessages.map((msg, index) => (
        <ChatMessage key={index} role={msg.role as "user" | "assistant"} message={msg.message} avatarUrl={msg.avatarUrl} />
      ))}
    </div>
  )

  return (
    <div className="flex flex-col h-screen bg-background">
      <Header isAuthenticated={true} />
      <div className="flex-1 overflow-y-auto pb-24"> {/* Padding bottom for the fixed chat bar */}
        <main className="container mx-auto px-4 py-8">
            <Breadcrumb className="mb-6">
                <BreadcrumbList>
                    <BreadcrumbItem>
                        <BreadcrumbLink href="/tracks">Tracks</BreadcrumbLink>
                    </BreadcrumbItem>
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                        <BreadcrumbPage>{trackData.name}</BreadcrumbPage>
                    </BreadcrumbItem>
                </BreadcrumbList>
            </Breadcrumb>
            
            <LiveSynopsis 
                points={trackData.synopsisPoints}
                lastUpdated="Updated 2m ago"
                className="mb-8"
            />

            <ContentTabs 
                chatContent={chatContent}
                practiceContent={<p className="text-center text-text-secondary p-8">Practice exercises will appear here.</p>}
                simulationContent={<p className="text-center text-text-secondary p-8">Simulations will run in this tab.</p>}
            />
        </main>
      </div>
      
      <div className="fixed bottom-0 left-0 right-0 bg-background/50 backdrop-blur-lg">
          <div className="container mx-auto p-4">
            <GlassCard className="p-2">
                <div className="flex gap-2">
                    <Input 
                        placeholder="Ask anything about your project or course..."
                        className="bg-transparent border-none focus-visible:ring-0 focus-visible:ring-offset-0 text-base"
                    />
                    <Button size="icon" aria-label="Send message">
                        <Send className="h-5 w-5" />
                    </Button>
                </div>
            </GlassCard>
          </div>
      </div>
    </div>
  )
}

export default TrackPage 