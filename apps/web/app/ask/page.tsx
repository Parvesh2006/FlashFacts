"use client";

import React, { useEffect, useState } from "react";
import { MessageSquareText, Send, Sparkles, AlertCircle, Bot, User } from "lucide-react";
import { askQuestion, AskResponse } from "@/services/ask";
import { BackButton } from "@/components/navigation/back-button";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  isStatusNote?: boolean;
}

const SUGGESTED_QUESTIONS = [
  "What happened today?",
  "Latest AI developments",
  "Important government current affairs",
  "Show this week's sports events",
  "Explain today's major events",
];

export default function AskPage() {
  const [questionInput, setQuestionInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "init",
      sender: "assistant",
      text: "Ask FlashFacts AI is being connected to the intelligence engine. Enter a question below to test prompt routing.",
      timestamp: "--:--",
      isStatusNote: true,
    },
  ]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMessages((prev) =>
      prev.map((message) =>
        message.id === "init"
          ? {
              ...message,
              timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            }
          : message,
      ),
    );
  }, []);

  const handleSend = async (qText: string) => {
    const cleanQ = qText.trim();
    if (!cleanQ || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: cleanQ,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setQuestionInput("");
    setLoading(true);

    try {
      const res: AskResponse = await askQuestion(cleanQ);
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: res.answer || "Ask FlashFacts AI is being connected to the intelligence engine.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isStatusNote: true,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: "Ask FlashFacts AI is being connected to the intelligence engine.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isStatusNote: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto flex flex-col min-h-[calc(100vh-220px)] lg:h-[calc(100vh-140px)]">
      <BackButton fallbackHref="/" />

      {/* Header */}
      <div className="border-b pb-3 flex-shrink-0">
        <div className="eyebrow flex items-center gap-2 mb-1">
          <Sparkles className="w-4 h-4" />
          <span>AI Intelligence Interface</span>
        </div>
        <h1 className="headline text-3xl md:text-4xl">
          Ask FlashFacts AI
        </h1>
        <p className="body-copy text-sm">
          RAG-powered conversational assistant for natural language current affairs query synthesis.
        </p>
      </div>

      <div className="p-3 bg-[var(--brand-primary-soft)] border border-[var(--brand-primary-border)] rounded-lg flex items-center gap-3 text-xs font-mono text-[var(--brand-primary)] flex-shrink-0">
        <AlertCircle className="w-4 h-4 flex-shrink-0" />
        <span>Ask FlashFacts AI is being connected to the intelligence engine (Phase 3 RAG integration).</span>
      </div>

      <div className="space-y-1.5 flex-shrink-0">
        <p className="meta-text uppercase">Suggested Prompts:</p>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((prompt, i) => (
            <button
              key={i}
              onClick={() => handleSend(prompt)}
              className="control text-xs font-mono px-3 py-1.5"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 editorial-card p-4 md:p-6 overflow-y-auto space-y-4" aria-live="polite" aria-label="Conversation">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 ${msg.sender === "user" ? "flex-row-reverse" : "flex-row"}`}
          >
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 font-mono text-xs ${
                msg.sender === "user"
                  ? "bg-[var(--brand-primary)] text-white"
                  : "brand-mark"
              }`}
            >
              {msg.sender === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div
              className={`max-w-[80%] rounded-2xl p-4 text-xs font-sans space-y-1 ${
                msg.sender === "user"
                  ? "bg-[var(--brand-primary-soft)] border border-[var(--brand-primary-border)] text-[var(--text-primary)]"
                  : msg.isStatusNote
                  ? "bg-[var(--surface-muted)] border text-[var(--text-secondary)] font-mono"
                  : "bg-[var(--surface-muted)] border text-[var(--text-primary)]"
              }`}
            >
              <div className="flex items-center justify-between gap-4 font-mono text-[10px] text-[var(--text-muted)] pb-1 border-b">
                <span>{msg.sender === "user" ? "You" : "FlashFacts AI Assistant"}</span>
                <span>{msg.timestamp}</span>
              </div>
              <p className="leading-relaxed pt-1">{msg.text}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-3 meta-text animate-pulse" role="status">
            <Bot className="w-4 h-4 accent-mark" />
            <span>Querying FlashFacts engine...</span>
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend(questionInput);
        }}
        className="flex gap-2 flex-shrink-0"
      >
        <input
          type="text"
          placeholder="Ask any question about today's current affairs..."
          value={questionInput}
          onChange={(e) => setQuestionInput(e.target.value)}
          className="control-input flex-1 px-4 py-3 text-xs font-mono focus:outline-none focus:border-[var(--brand-primary)]"
        />
        <button
          type="submit"
          disabled={!questionInput.trim() || loading}
          className="brand-button px-5 py-3 disabled:opacity-40 font-mono text-xs font-semibold flex items-center gap-2"
          aria-label="Ask FlashFacts AI"
        >
          <span>Ask</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}
