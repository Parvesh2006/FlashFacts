"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { api, setTokenProvider } from "./api";

export interface UserProfile {
  id: string;
  username: string;
  email?: string;
  is_guest: boolean;
  target_exam: string;
  created_at: string;
}

export interface AuthSession {
  access_token: string;
  token_type?: string;
  user: UserProfile;
}

const STUDENT_TOKEN_KEY = "flashfacts_auth_token";
const STUDENT_USER_KEY = "flashfacts_auth_user";
const GUEST_TOKEN_KEY = "flashfacts_guest_token";
const GUEST_USER_KEY = "flashfacts_guest_user";
const AUTH_EVENT = "flashfacts_auth_change";

function sanitizeStorageOnLoad() {
  if (typeof window === "undefined") return;
  try {
    const rawLocal = localStorage.getItem(STUDENT_USER_KEY);
    if (rawLocal) {
      const parsed = JSON.parse(rawLocal);
      if (parsed.is_guest) {
        // Obsolete legacy guest session found in localStorage - purge it safely.
        // A new guest session must always start fresh, never inherit previous guest data.
        localStorage.removeItem(STUDENT_TOKEN_KEY);
        localStorage.removeItem(STUDENT_USER_KEY);
      }
    } else {
      // If token exists in localStorage without a valid student profile, clear it
      localStorage.removeItem(STUDENT_TOKEN_KEY);
    }
  } catch {
    // ignore
  }
}

// Run legacy cleanup on initial load
if (typeof window !== "undefined") {
  sanitizeStorageOnLoad();
}

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;

  // 1. Persistent authenticated student session in localStorage
  try {
    const studentUserRaw = localStorage.getItem(STUDENT_USER_KEY);
    if (studentUserRaw) {
      const user = JSON.parse(studentUserRaw);
      if (!user.is_guest) {
        const studentToken = localStorage.getItem(STUDENT_TOKEN_KEY);
        if (studentToken) return studentToken;
      }
    }
  } catch {}

  // 2. Active guest session in sessionStorage (isolated to current browser session)
  try {
    const guestToken = sessionStorage.getItem(GUEST_TOKEN_KEY);
    if (guestToken) return guestToken;
  } catch {}

  return null;
}

export function getStoredUser(): UserProfile | null {
  if (typeof window === "undefined") return null;

  // 1. Authenticated student from localStorage
  try {
    const studentUserRaw = localStorage.getItem(STUDENT_USER_KEY);
    if (studentUserRaw) {
      const user = JSON.parse(studentUserRaw);
      if (!user.is_guest) return user;
    }
  } catch {}

  // 2. Guest profile from sessionStorage
  try {
    const guestUserRaw = sessionStorage.getItem(GUEST_USER_KEY);
    if (guestUserRaw) {
      return JSON.parse(guestUserRaw);
    }
  } catch {}

  return null;
}

export function saveAuthSession(session: AuthSession) {
  if (typeof window === "undefined") return;

  if (session.user.is_guest) {
    // Guest session: store strictly in sessionStorage (survives refresh, discarded on browser exit)
    sessionStorage.setItem(GUEST_TOKEN_KEY, session.access_token);
    sessionStorage.setItem(GUEST_USER_KEY, JSON.stringify(session.user));
    localStorage.removeItem(STUDENT_TOKEN_KEY);
    localStorage.removeItem(STUDENT_USER_KEY);
  } else {
    // Signed-in student: store persistently in localStorage
    localStorage.setItem(STUDENT_TOKEN_KEY, session.access_token);
    localStorage.setItem(STUDENT_USER_KEY, JSON.stringify(session.user));
    sessionStorage.removeItem(GUEST_TOKEN_KEY);
    sessionStorage.removeItem(GUEST_USER_KEY);
  }

  window.dispatchEvent(new CustomEvent(AUTH_EVENT, { detail: session.user }));
}

export function clearAuthSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STUDENT_TOKEN_KEY);
  localStorage.removeItem(STUDENT_USER_KEY);
  sessionStorage.removeItem(GUEST_TOKEN_KEY);
  sessionStorage.removeItem(GUEST_USER_KEY);
  window.dispatchEvent(new CustomEvent(AUTH_EVENT, { detail: null }));

  // Immediately initialize a fresh guest session for subsequent anonymous usage
  ensureAuthSession().catch(() => {});
}

let inFlightGuestSessionPromise: Promise<AuthSession> | null = null;

export async function ensureAuthSession(targetExam = "TNPSC Group 4"): Promise<AuthSession> {
  const existingToken = getAuthToken();
  const existingUser = getStoredUser();

  if (existingToken && existingUser) {
    return {
      access_token: existingToken,
      user: existingUser,
    };
  }

  if (inFlightGuestSessionPromise) {
    return inFlightGuestSessionPromise;
  }

  inFlightGuestSessionPromise = (async () => {
    try {
      const session = await api.post<AuthSession>(
        `/api/v1/auth/guest?target_exam=${encodeURIComponent(targetExam)}`
      );
      saveAuthSession(session);
      return session;
    } catch (err) {
      console.error("Failed to initialize guest authentication session", err);
      throw err;
    } finally {
      inFlightGuestSessionPromise = null;
    }
  })();

  return inFlightGuestSessionPromise;
}

// Register token provider with API client for transparent guest session creation
if (typeof window !== "undefined") {
  setTokenProvider(async () => {
    try {
      const session = await ensureAuthSession();
      return session.access_token;
    } catch {
      return null;
    }
  });
}

export async function loginStudent(username: string, password: string): Promise<UserProfile> {
  const existingUser = getStoredUser();
  const guest_user_id = existingUser?.is_guest ? existingUser.id : undefined;

  const session = await api.post<AuthSession>("/api/v1/auth/login", {
    username,
    password,
    guest_user_id,
  });
  saveAuthSession(session);
  return session.user;
}

export async function registerStudent(
  username: string,
  password: string,
  email?: string,
  target_exam: string = "TNPSC Group 4"
): Promise<UserProfile> {
  const existingUser = getStoredUser();
  const guest_user_id = existingUser?.is_guest ? existingUser.id : undefined;

  const session = await api.post<AuthSession>("/api/v1/auth/register", {
    username,
    password,
    email: email || undefined,
    target_exam,
    guest_user_id,
  });
  saveAuthSession(session);
  return session.user;
}

export async function loginWithGoogle(
  credential: string,
  target_exam: string = "TNPSC Group 4"
): Promise<UserProfile> {
  const existingUser = getStoredUser();
  const guest_user_id = existingUser?.is_guest ? existingUser.id : undefined;

  const session = await api.post<AuthSession>("/api/v1/auth/google", {
    credential,
    target_exam,
    guest_user_id,
  });
  saveAuthSession(session);
  return session.user;
}

export async function updateTargetExam(targetExam: string): Promise<UserProfile> {
  const user = await api.put<UserProfile>("/api/v1/auth/target-exam", {
    target_exam: targetExam,
  });
  if (typeof window !== "undefined") {
    const active = getStoredUser();
    if (active?.is_guest) {
      sessionStorage.setItem(GUEST_USER_KEY, JSON.stringify(user));
    } else {
      localStorage.setItem(STUDENT_USER_KEY, JSON.stringify(user));
    }
    window.dispatchEvent(new CustomEvent(AUTH_EVENT, { detail: user }));
  }
  return user;
}

// Subscription helper for useSyncExternalStore
let cachedUserSnapshot: UserProfile | null = null;
let cachedRawSignature: string | null = null;

function getSnapshot(): UserProfile | null {
  if (typeof window === "undefined") return null;
  const user = getStoredUser();
  const signature = user ? `${user.id}_${user.username}_${user.is_guest}_${user.target_exam}` : "none";
  if (signature !== cachedRawSignature) {
    cachedRawSignature = signature;
    cachedUserSnapshot = user;
  }
  return cachedUserSnapshot;
}

function getServerSnapshot(): null {
  return null;
}

function subscribe(callback: () => void) {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(AUTH_EVENT, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(AUTH_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

export function useAuth() {
  const user = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const activeUser = mounted ? user : null;

  return {
    user: activeUser,
    isLoaded: mounted,
    isAuthenticated: Boolean(activeUser),
    isGuest: Boolean(activeUser?.is_guest),
    isStudent: Boolean(activeUser && !activeUser.is_guest),
    login: loginStudent,
    register: registerStudent,
    loginWithGoogle,
    logout: clearAuthSession,
    updateTargetExam,
    createGuestSession: ensureAuthSession,
  };
}
