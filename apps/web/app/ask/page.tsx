"use client";

import React, { useEffect, useState, useRef } from "react";
import { MessageSquareText, Send, Sparkles, AlertCircle, Bot, User, ArrowUp } from "lucide-react";
import { askQuestion, AskResponse } from "@/services/ask";
import { BackButton } from "@/components/navigation/back-button";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  isStatusNote?: boolean;
}

const SUGGESTED_QUESTIONS = [
  "What happened today?",
  "Tamil Nadu current affairs",
  "Latest science & technology",
  "Give me 5 MCQs",
  "Important TNPSC current affairs",
];

export default function AskPage() {
  const [questionInput, setQuestionInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

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
        text: res.answer || "I couldn't find enough verified FlashFacts data for that query.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: "I encountered an error connecting to the intelligence engine.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isStatusNote: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(questionInput);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] overflow-hidden bg-[var(--background-primary)] text-[var(--text-primary)]">
      {/* Header */}
      <div className="border-b border-[var(--surface-border)] bg-[var(--background-primary)] z-10 flex-shrink-0">
        <div className="max-w-[1100px] mx-auto px-4 md:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <BackButton fallbackHref="/" />
              <div>
                <div className="eyebrow flex items-center gap-2 mb-0.5 text-xs font-semibold text-[var(--brand-primary)] tracking-widest uppercase">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>AI Intelligence</span>
                </div>
                <h1 className="text-xl md:text-2xl font-bold text-[var(--text-primary)]">
                  Ask FlashFacts AI
                </h1>
              </div>
            </div>
            
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--surface-muted)] border border-[var(--surface-border)] hidden sm:flex">
              <span className="w-2 h-2 rounded-full bg-[var(--brand-primary)] animate-pulse"></span>
              <span className="text-xs font-medium text-[var(--text-secondary)]">FlashFacts AI · Online</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Conversation Area */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-8" aria-live="polite">
        <div className="max-w-[1100px] mx-auto space-y-8 pb-12">
          
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center min-h-[40vh] text-center space-y-8 animate-in fade-in zoom-in duration-500">
              <div className="w-16 h-16 rounded-2xl bg-[var(--brand-primary-soft)] flex items-center justify-center mb-2">
                <Bot className="w-8 h-8 text-[var(--brand-primary)]" />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl md:text-3xl font-bold text-[var(--text-primary)]">Ask FlashFacts AI</h2>
                <p className="text-[var(--text-secondary)] max-w-md mx-auto text-sm md:text-base">
                  Your exam-focused current affairs assistant. Ask anything about recent events, policies, or exam topics.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 w-full max-w-3xl mt-8">
                {SUGGESTED_QUESTIONS.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(prompt)}
                    className="flex items-center text-left p-4 rounded-xl border border-[var(--surface-border)] bg-[var(--surface-muted)] hover:bg-[var(--surface-hover)] hover:border-[var(--brand-primary)] transition-all duration-200 text-sm font-medium text-[var(--text-primary)]"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-start gap-4 ${msg.sender === "user" ? "flex-row-reverse" : "flex-row"}`}
              >
                <div
                  className={`w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${msg.sender === "user" ? "bg-[var(--text-primary)] text-[var(--background-primary)]" : "bg-[var(--brand-primary)] text-white shadow-lg shadow-[var(--brand-primary)]/20"}`}
                >
                  {msg.sender === "user" ? <User className="w-4 h-4 md:w-5 md:h-5" /> : <Bot className="w-4 h-4 md:w-5 md:h-5" />}
                </div>

                <div
                  className={`max-w-[90%] md:max-w-[850px] ${msg.sender === "user" ? "bg-[var(--surface-muted)] border border-[var(--surface-border)] rounded-2xl rounded-tr-sm p-4 md:p-5" : "pt-1"}`}
                >
                  {msg.sender === "user" ? (
                    <p className="text-[15px] leading-relaxed text-[var(--text-primary)] whitespace-pre-wrap">{msg.text}</p>
                  ) : (
                    msg.isStatusNote ? (
                      <div className="p-4 rounded-xl bg-[var(--surface-muted)] border border-[var(--surface-border)] text-[var(--text-secondary)] text-sm font-mono">
                        {msg.text}
                      </div>
                    ) : (
                      <MarkdownRenderer content={msg.text} />
                    )
                  )}
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-[var(--brand-primary)] text-white shadow-lg shadow-[var(--brand-primary)]/20 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 md:w-5 md:h-5" />
              </div>
              <div className="pt-2 flex items-center gap-3">
                <span className="flex gap-1">
                  <span className="w-2 h-2 rounded-full bg-[var(--brand-primary)] animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-2 h-2 rounded-full bg-[var(--brand-primary)] animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-2 h-2 rounded-full bg-[var(--brand-primary)] animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </span>
                <span className="text-sm font-medium text-[var(--text-secondary)] animate-pulse">Thinking...</span>
              </div>
            </div>
          )}
          
          <div ref={bottomRef} className="h-4"></div>
        </div>
      </div>

      {/* Input Composer */}
      <div className="flex-shrink-0 bg-gradient-to-t from-[var(--background-primary)] via-[var(--background-primary)] to-transparent pt-6 pb-6 px-4 md:px-8 border-t border-[var(--surface-border)]/50">
        <div className="max-w-[900px] mx-auto">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend(questionInput);
            }}
            className="relative flex items-end gap-2 bg-[var(--surface-muted)] border border-[var(--surface-border)] rounded-2xl p-2 focus-within:border-[var(--brand-primary)] focus-within:ring-1 focus-within:ring-[var(--brand-primary)] transition-all shadow-sm"
          >
            <textarea
              rows={1}
              placeholder="Ask anything about current affairs..."
              value={questionInput}
              onChange={(e) => {
                setQuestionInput(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
              }}
              onKeyDown={handleKeyDown}
              className="flex-1 max-h-[120px] bg-transparent resize-none px-3 py-3 text-[15px] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none scrollbar-thin"
              style={{ minHeight: '44px' }}
            />
            <button
              type="submit"
              disabled={!questionInput.trim() || loading}
              className="mb-1 mr-1 w-10 h-10 rounded-xl bg-[var(--brand-primary)] text-white flex items-center justify-center disabled:opacity-40 disabled:bg-[var(--surface-border)] disabled:text-[var(--text-muted)] transition-colors flex-shrink-0"
              aria-label="Send message"
            >
              <ArrowUp className="w-5 h-5" />
            </button>
          </form>
          <div className="text-center mt-3">
            <span className="text-[11px] text-[var(--text-muted)]">FlashFacts AI can make mistakes. Verify important information.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
