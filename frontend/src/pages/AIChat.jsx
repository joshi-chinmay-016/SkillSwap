import React, { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import Input from "../components/common/Input";
import { useToast } from "../components/common/Toast";
import { Send, Bot, User, Sparkles, MessageSquare } from "lucide-react";

export default function AIChat() {
  const { toast } = useToast();
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hello! I'm your AI learning assistant. Ask me anything about skills, learning paths, or mentorship recommendations!" },
    { role: "assistant", content: "I can help you with:\n- Finding the right skills to learn\n- Creating learning roadmaps\n- Connecting with mentors\n- Career advice" },
    { role: "assistant", content: "Try asking me something like:\n- What skills do I need for web development?\n- How can I become a data scientist?\n- Recommend a mentor for React" },
    { role: "assistant", content: "I'm here to guide your learning journey!" }
    
  ]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  const chatMutation = useMutation({
    mutationFn: async (message) => {
      const res = await api.post("/ai/chat", { message });
      return res.data;
    },
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { role: "assistant", content: data.response }]);
    },
    onError: (error) => {
      toast({ 
        title: "Error", 
        description: error.response?.data?.detail || "Failed to get AI response",
        variant: "destructive" 
      });
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I encountered an error. Please try again." }]);
    },
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    chatMutation.mutate(userMessage);
  };

  return (
    <div className="flex flex-col gap-6 h-[calc(100vh-8rem)]">
      {/* Page Header */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-accent/10 text-accent rounded-lg">
            <MessageSquare size={20} />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-text">AI Learning Assistant</h1>
            <p className="text-sm text-text-secondary mt-1">
              Ask questions about skills, learning paths, and mentorship
            </p>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <div className="flex-1 flex flex-col overflow-hidden bg-bg border border-border rounded-lg shadow-sm">
        {/* Messages Area */}
        <div 
          id="chat-messages"
          className="flex-1 overflow-y-auto p-4 space-y-4"
          style={{ 
            height: "500px",
            overflowY: "scroll"
          }}
        >
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {message.role === "assistant" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-accent/10 text-accent flex items-center justify-center">
                  <Bot size={16} />
                </div>
              )}
              <div
                className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                  message.role === "user"
                    ? "bg-accent text-white"
                    : "bg-bg border border-border"
                }`}
              >
                {message.role === "assistant" ? (
                  <div className="text-sm prose prose-sm max-w-none prose-headings:text-text prose-p:text-text prose-li:text-text prose-strong:text-text prose-ul:text-text prose-ol:text-text">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                )}
              </div>
              {message.role === "user" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-accent text-white flex items-center justify-center">
                  <User size={16} />
                </div>
              )}
            </div>
          ))}
          {chatMutation.isPending && (
            <div className="flex gap-3 justify-start">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-accent/10 text-accent flex items-center justify-center">
                <Bot size={16} />
              </div>
              <div className="bg-bg border border-border rounded-2xl px-4 py-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-text-secondary rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-text-secondary rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-text-secondary rounded-full animate-bounce delay-200" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-border p-4 shrink-0">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about skills, learning paths, or mentorship..."
              disabled={chatMutation.isPending}
              className="flex-1"
            />
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={!input.trim() || chatMutation.isPending}
            >
              <Send size={16} />
            </Button>
          </form>
          <div className="mt-3 flex flex-wrap gap-2">
            {[
              "How do I become a full-stack developer?",
              "What skills do I need for data science?",
              "Recommend a mentor for React",
            ].map((suggestion, index) => (
              <button
                key={index}
                type="button"
                onClick={() => setInput(suggestion)}
                className="text-xs px-3 py-1.5 bg-bg border border-border rounded-full text-text-secondary hover:border-accent/50 hover:text-accent transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
