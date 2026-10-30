"use client";

import React, { useEffect, useState, useRef } from "react";
import { Sparkles, Bot, User, ArrowUp, Loader2, ExternalLink, BookOpen } from "lucide-react";
import { askQuestion, AskResponse, ChatHistoryItem, SourceItem } from "@/services/ask";
import { BackButton } from "@/components/navigation/back-button";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  isStatusNote?: boolean;
  sources?: (SourceItem | string)[];
  provider?: string;
}

const SUGGESTED_QUESTIONS = [
  "What happened today in national news?",
  "Key Tamil Nadu government welfare schemes",
  "Recent Science & Technology developments",
  "Explain the fundamental duties of the Indian Constitution",
  "Important Supreme Court judgments 2024-2025",
  "High priority updates for TNPSC Group 4",
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

    const previousMessages = messages;
    setMessages((prev) => [...prev, userMsg]);
    setQuestionInput("");
    setLoading(true);

    try {
      const history: ChatHistoryItem[] = previousMessages.slice(-6).map((m) => ({
        role: m.sender === "user" ? "user" : "assistant",
        content: m.text,
      }));

      const res: AskResponse = await askQuestion(cleanQ, history);
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: res.answer || "I couldn't locate enough verified FlashFacts records for that syllabus query.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        sources: res.sources,
        provider: res.provider,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: err?.message || "Could not establish a connection to the FlashFacts AI intelligence service. Please ensure the local Ollama and API server are running.",
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
    <div className="flex flex-col h-[calc(100vh-70px)] overflow-hidden bg-[var(--background)] text-[var(--text-primary)] page-enter">
      {/* Header */}
      <div className="border-b border-[var(--border)] bg-[var(--surface)] z-10 flex-shrink-0">
        <div className="max-w-5xl mx-auto px-4 md:px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BackButton fallbackHref="/" />
            <div>
              <div className="flex items-center gap-1.5 text-[11px] font-semibold text-[var(--accent)] uppercase tracking-wider">
                <Sparkles className="w-3.5 h-3.5" />
                <span>AI Intelligence Desk</span>
              </div>
              <h1 className="headline text-lg md:text-xl font-bold text-[var(--text-primary)]">
                Ask FlashFacts AI
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--surface-muted)] border border-[var(--border)] text-xs">
            <span className="w-2 h-2 rounded-full bg-[var(--success)] animate-pulse" />
            <span className="text-[11px] font-medium text-[var(--text-secondary)]">Verified Syllabus Engine</span>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 overflow-y-auto px-4 md:px-6 py-6" aria-live="polite">
        <div className="max-w-4xl mx-auto space-y-6 pb-8">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center min-h-[50vh] text-center space-y-6 py-8">
              <div className="w-16 h-16 rounded-2xl bg-[var(--accent-soft)] border border-[color-mix(in_srgb,var(--accent)_30%,var(--border))] flex items-center justify-center text-[var(--accent)] shadow-xs">
                <Bot className="w-8 h-8" />
              </div>
              <div className="space-y-2 max-w-lg">
                <h2 className="headline text-2xl md:text-3xl font-bold text-[var(--text-primary)] tracking-tight">
                  Curriculum Intelligence Assistant
                </h2>
                <p className="body-copy text-xs md:text-sm text-[var(--text-secondary)] leading-relaxed">
                  Ask targeted questions about government schemes, constitutional amendments, scientific breakthroughs, or general examination concepts.
                </p>
              </div>

              {/* Prompt Suggestions Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 w-full max-w-3xl pt-2">
                {SUGGESTED_QUESTIONS.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(prompt)}
                    className="flex items-center text-left p-3.5 rounded-xl border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-muted)] hover:border-[var(--accent)] transition-all text-xs font-medium text-[var(--text-primary)] shadow-xs"
                  >
                    <span className="text-[var(--accent)] mr-2 shrink-0">✦</span>
                    <span className="line-clamp-2">{prompt}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-start gap-3.5 ${msg.sender === "user" ? "flex-row-reverse" : "flex-row"}`}
              >
                <div
                  className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-xs ${
                    msg.sender === "user"
                      ? "bg-[var(--text-primary)] text-[var(--surface)]"
                      : "bg-[var(--accent)] text-white"
                  }`}
                >
                  {msg.sender === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div
                  className={`max-w-[88%] md:max-w-2xl ${
                    msg.sender === "user"
                      ? "bg-[var(--accent)] text-white rounded-2xl rounded-tr-xs p-4 shadow-xs"
                      : "bg-[var(--surface)] border border-[var(--border)] rounded-2xl rounded-tl-xs p-5 shadow-xs"
                  }`}
                >
                  {msg.sender === "user" ? (
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                  ) : msg.isStatusNote ? (
                    <div className="p-3 rounded-lg bg-[var(--danger-soft)] border border-[color-mix(in_srgb,var(--danger)_30%,var(--border))] text-[var(--danger)] text-xs">
                      {msg.text}
                    </div>
                  ) : (
                    <>
                      <MarkdownRenderer content={msg.text} />
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-3.5 pt-3 border-t border-[var(--border)] space-y-2">
                          <div className="text-[10px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider flex items-center gap-1.5">
                            <BookOpen className="w-3 h-3 text-[var(--accent)]" />
                            <span>Verified Sources</span>
                            {msg.provider && (
                              <span className="px-1.5 py-0.2 rounded text-[9px] bg-[var(--surface-muted)] text-[var(--accent)] font-mono">
                                {msg.provider}
                              </span>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.sources.map((src, idx) => {
                              const isObj = typeof src === "object" && src !== null;
                              const name = isObj ? src.name : src;
                              const url = isObj ? src.url : undefined;
                              const date = isObj ? src.date : undefined;

                              return url ? (
                                <a
                                  key={idx}
                                  href={url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] bg-[var(--surface-muted)] hover:bg-[var(--accent-soft)] hover:text-[var(--accent)] border border-[var(--border)] transition-colors text-[var(--text-primary)]"
                                >
                                  <span className="font-medium">{name}</span>
                                  {date && <span className="text-[10px] text-[var(--text-muted)]">({date})</span>}
                                  <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                                </a>
                              ) : (
                                <span
                                  key={idx}
                                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] bg-[var(--surface-muted)] border border-[var(--border)] text-[var(--text-secondary)]"
                                >
                                  <span className="font-medium">{name}</span>
                                  {date && <span className="text-[10px] text-[var(--text-muted)]">({date})</span>}
                                </span>
                              );
                            })}
                          </div>
                        </div>
                      )}
                      {msg.provider === "ai_syllabus" && (
                        <div className="mt-2.5 pt-2 border-t border-[var(--border)] flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded text-[10px] bg-[var(--surface-muted)] text-[var(--accent)] font-medium">
                            Exam Syllabus Knowledge • Direct LLM Explanation
                          </span>
                        </div>
                      )}
                      {msg.provider === "ai_unverified_limitation" && (
                        <div className="mt-2.5 pt-2 border-t border-[var(--border)] flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded text-[10px] bg-[var(--surface-muted)] text-[var(--text-secondary)] font-medium">
                            Archive Limitation • No Verified Contemporary Records Found
                          </span>
                        </div>
                      )}
                    </>
                  )}
                  <div
                    className={`text-[10px] mt-2 text-right ${
                      msg.sender === "user" ? "text-white/70" : "text-[var(--text-muted)]"
                    }`}
                  >
                    {msg.timestamp}
                  </div>
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-xl bg-[var(--accent)] text-white shadow-xs flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-4 rounded-2xl rounded-tl-xs bg-[var(--surface)] border border-[var(--border)] flex items-center gap-2.5 text-xs text-[var(--text-secondary)] shadow-xs">
                <Loader2 className="w-4 h-4 animate-spin text-[var(--accent)]" />
                <span>Querying FlashFacts verified intelligence...</span>
              </div>
            </div>
          )}

          <div ref={bottomRef} className="h-4" />
        </div>
      </div>

      {/* Input Composer */}
      <div className="flex-shrink-0 bg-[var(--surface)] border-t border-[var(--border)] p-4 md:px-6">
        <div className="max-w-3xl mx-auto">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend(questionInput);
            }}
            className="relative flex items-center gap-2 bg-[var(--surface-muted)] border border-[var(--border)] rounded-2xl p-2 focus-within:border-[var(--accent)] focus-within:bg-[var(--surface)] transition-all shadow-xs"
          >
            <textarea
              rows={1}
              placeholder="Ask anything about current affairs, schemes, policies, or syllabus topics..."
              value={questionInput}
              onChange={(e) => {
                setQuestionInput(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 100) + 'px';
              }}
              onKeyDown={handleKeyDown}
              className="flex-1 max-h-[100px] bg-transparent resize-none px-3 py-2 text-xs md:text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none"
              style={{ minHeight: '38px' }}
            />
            <button
              type="submit"
              disabled={!questionInput.trim() || loading}
              className="w-9 h-9 rounded-xl bg-[var(--accent)] text-white flex items-center justify-center disabled:opacity-40 transition-all shrink-0 font-semibold"
              aria-label="Send query"
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          </form>
          <div className="text-center mt-2">
            <span className="text-[11px] text-[var(--text-muted)]">
              Press Enter to send, Shift + Enter for new line • Grounded in official examination archives
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
