"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  X,
  User,
  Lock,
  Mail,
  GraduationCap,
  Sparkles,
  ArrowRight,
  Loader2,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "@/lib/auth";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTab?: "login" | "register";
  title?: string;
  subtitle?: string;
}

export function AuthModal({
  isOpen,
  onClose,
  defaultTab = "login",
  title,
  subtitle,
}: AuthModalProps) {
  const { user, isGuest, login, register, loginWithGoogle, createGuestSession } = useAuth();
  const [tab, setTab] = useState<"login" | "register">(defaultTab);

  // Form states
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [targetExam, setTargetExam] = useState("TNPSC Group 4");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const googleButtonRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isOpen || !googleButtonRef.current) return;

    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    if (!clientId) {
      setError("Google sign-in is not configured. Please use username login.");
      return;
    }

    type GoogleCredentialResponse = { credential?: string };
    type GoogleIdentityAPI = {
      initialize: (config: {
        client_id: string;
        callback: (response: GoogleCredentialResponse) => void;
      }) => void;
      renderButton: (
        element: HTMLElement,
        options: Record<string, string | number | boolean>
      ) => void;
    };

    type GoogleWindow = Window & {
      google?: { accounts: { id: GoogleIdentityAPI } };
    };

    let cancelled = false;
    const buttonHost = googleButtonRef.current;

    const initializeGoogle = () => {
      const google = (window as GoogleWindow).google;
      if (cancelled || !google || !buttonHost) return;

      buttonHost.replaceChildren();

      google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response) => {
          if (!response.credential || cancelled) {
            setError("Google did not return a valid sign-in credential.");
            return;
          }

          setLoading(true);
          setError(null);
          try {
            await loginWithGoogle(response.credential, targetExam);
            setSuccessMessage("Signed in with Google successfully!");
            window.setTimeout(() => {
              onClose();
              setSuccessMessage(null);
            }, 800);
          } catch (err: unknown) {
            setError(
              err instanceof Error
                ? err.message
                : "Google authentication failed."
            );
          } finally {
            setLoading(false);
          }
        },
      });

      google.accounts.id.renderButton(buttonHost, {
        type: "standard",
        theme: "outline",
        size: "large",
        text: "continue_with",
        shape: "rectangular",
        width: 320,
      });
    };

    const scriptId = "google-identity-services";
    let script = document.getElementById(scriptId) as HTMLScriptElement | null;
    let createdScript = false;

    if ((window as GoogleWindow).google) {
      initializeGoogle();
    } else {
      if (!script) {
        script = document.createElement("script");
        script.id = scriptId;
        script.src = "https://accounts.google.com/gsi/client";
        script.async = true;
        script.defer = true;
        createdScript = true;
      }

      script.addEventListener("load", initializeGoogle);
      if (createdScript) document.head.appendChild(script);
    }

    return () => {
      cancelled = true;
      script?.removeEventListener("load", initializeGoogle);
      if (buttonHost) buttonHost.replaceChildren();
    };
  }, [isOpen, loginWithGoogle, onClose, targetExam]);

  if (!isOpen) return null;

  const exams = [
    "TNPSC Group 4",
    "TNPSC Group 2",
    "TNPSC Group 1",
    "UPSC CSE Prelims",
    "SSC CGL",
  ];

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError("Please enter both username and password");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await login(username.trim(), password);
      setSuccessMessage("Logged in successfully! Welcome back.");
      setTimeout(() => {
        onClose();
        setSuccessMessage(null);
      }, 800);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to log in. Please check your credentials.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError("Please provide a username and password");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters long");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await register(username.trim(), password, email.trim() || undefined, targetExam);
      setSuccessMessage("Account created successfully! Guest progress merged.");
      setTimeout(() => {
        onClose();
        setSuccessMessage(null);
      }, 900);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create account. Username may be taken.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleGuestContinue = async () => {
    setLoading(true);
    setError(null);
    try {
      await createGuestSession(targetExam);
      setSuccessMessage("Guest profile activated! Explore freely.");
      setTimeout(() => {
        onClose();
        setSuccessMessage(null);
      }, 600);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to activate guest profile.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md bg-[var(--surface)] border border-[var(--border)] rounded-2xl shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="relative px-6 pt-6 pb-4 border-b border-[var(--border)] bg-[var(--surface)]">
          <button
            onClick={onClose}
            className="absolute top-5 right-5 p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-muted)] transition-colors"
            aria-label="Close auth dialog"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2 mb-2">
            <span className="soft-badge px-2 py-0.5 text-[11px] font-mono uppercase tracking-wider text-[var(--brand-primary)]">
              Aspirant Portal
            </span>
          </div>

          <h2 className="text-xl font-bold tracking-tight text-[var(--text-primary)]">
            {title || (tab === "login" ? "Sign In to FlashFacts" : "Create Aspirant Account")}
          </h2>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            {subtitle || "Track your personal Mistake Book, sync mock test analytics, and revise smarter across all devices."}
          </p>

          {/* Guest data migration alert banner */}
          {isGuest && (
            <div className="mt-3 p-2.5 rounded-lg bg-[color-mix(in_srgb,var(--brand-primary)_12%,transparent)] border border-[color-mix(in_srgb,var(--brand-primary)_35%,transparent)] flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-[var(--brand-primary)] flex-shrink-0 mt-0.5" />
              <div className="text-[11px] text-[var(--text-primary)]">
                <span className="font-semibold">Seamless Upgrade: </span>
                Your active bookmarks, attempts, and mistakes ({user?.username}) will be merged automatically!
              </div>
            </div>
          )}
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-[var(--border)] bg-[var(--surface-muted)]/50">
          <button
            type="button"
            onClick={() => {
              setTab("login");
              setError(null);
            }}
            className={`flex-1 py-3 text-xs font-semibold text-center border-b-2 transition-colors ${
              tab === "login"
                ? "border-[var(--brand-primary)] text-[var(--brand-primary)] bg-[var(--surface)]"
                : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setTab("register");
              setError(null);
            }}
            className={`flex-1 py-3 text-xs font-semibold text-center border-b-2 transition-colors ${
              tab === "register"
                ? "border-[var(--brand-primary)] text-[var(--brand-primary)] bg-[var(--surface)]"
                : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Body Form */}
        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center gap-2 text-xs text-red-500">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMessage && (
            <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-2 text-xs text-emerald-500">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Official Google Identity Services button */}
          <div className="flex min-h-10 w-full justify-center overflow-hidden">
            <div ref={googleButtonRef} />
          </div>

          <div className="relative flex py-1 items-center">
            <div className="flex-grow border-t border-[var(--border)]"></div>
            <span className="flex-shrink mx-3 text-[10px] uppercase font-mono text-[var(--text-muted)]">
              or with username
            </span>
            <div className="flex-grow border-t border-[var(--border)]"></div>
          </div>

          {/* Login Form */}
          {tab === "login" ? (
            <form onSubmit={handleLoginSubmit} className="space-y-3.5">
              <div>
                <label className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                  Username
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. aspirant_tnpsc"
                    className="control-input w-full pl-9 pr-3 py-2 text-xs font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="control-input w-full pl-9 pr-3 py-2 text-xs font-mono"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary w-full py-2.5 text-xs font-semibold flex items-center justify-center gap-2 mt-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Sign In to FlashFacts"}
                {!loading && <ArrowRight className="w-3.5 h-3.5" />}
              </button>
            </form>
          ) : (
            /* Register Form */
            <form onSubmit={handleRegisterSubmit} className="space-y-3">
              <div>
                <label className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                  Desired Username
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. tnpsc_rank_holder"
                    className="control-input w-full pl-9 pr-3 py-2 text-xs font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                  Email Address (Optional)
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="aspirant@gmail.com"
                    className="control-input w-full pl-9 pr-3 py-2 text-xs font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                  Password (min 6 characters)
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="control-input w-full pl-9 pr-3 py-2 text-xs font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                  Target Competitive Exam
                </label>
                <div className="relative">
                  <GraduationCap className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
                  <select
                    value={targetExam}
                    onChange={(e) => setTargetExam(e.target.value)}
                    className="control-input w-full pl-9 pr-3 py-2 text-xs font-mono"
                  >
                    {exams.map((ex) => (
                      <option key={ex} value={ex}>
                        {ex}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary w-full py-2.5 text-xs font-semibold flex items-center justify-center gap-2 mt-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Aspirant Account"}
                {!loading && <ArrowRight className="w-3.5 h-3.5" />}
              </button>
            </form>
          )}

          {/* Continue as Guest option */}
          {!user && (
            <div className="pt-2 text-center">
              <button
                type="button"
                onClick={handleGuestContinue}
                disabled={loading}
                className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] underline underline-offset-4 transition-colors"
              >
                Or continue as anonymous guest (local session)
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
