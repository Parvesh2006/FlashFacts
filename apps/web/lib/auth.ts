"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { api } from "./api";

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

const TOKEN_KEY = "flashfacts_auth_token";
const USER_KEY = "flashfacts_auth_user";
const AUTH_EVENT = "flashfacts_auth_change";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): UserProfile | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function saveAuthSession(session: AuthSession) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, session.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(session.user));
  window.dispatchEvent(new CustomEvent(AUTH_EVENT, { detail: session.user }));
}

export function clearAuthSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  window.dispatchEvent(new CustomEvent(AUTH_EVENT, { detail: null }));
}

export async function ensureAuthSession(targetExam = "TNPSC Group 4"): Promise<AuthSession> {
  const existingToken = getAuthToken();
  const existingUser = getStoredUser();

  if (existingToken && existingUser) {
    return {
      access_token: existingToken,
      user: existingUser,
    };
  }

  // Request new guest session
  try {
    const session = await api.post<AuthSession>(
      `/api/v1/auth/guest?target_exam=${encodeURIComponent(targetExam)}`
    );
    saveAuthSession(session);
    return session;
  } catch (err) {
    console.error("Failed to initialize guest authentication session", err);
    throw err;
  }
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
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    window.dispatchEvent(new CustomEvent(AUTH_EVENT, { detail: user }));
  }
  return user;
}

// Subscription helper for useSyncExternalStore
let cachedUserSnapshot: UserProfile | null = null;
let cachedRawString: string | null = null;

function getSnapshot(): UserProfile | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (raw !== cachedRawString) {
    cachedRawString = raw;
    try {
      cachedUserSnapshot = raw ? JSON.parse(raw) : null;
    } catch {
      cachedUserSnapshot = null;
    }
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

  return {
    user: mounted ? user : null,
    isLoaded: mounted,
    isAuthenticated: Boolean(user),
    isGuest: Boolean(user?.is_guest),
    isStudent: Boolean(user && !user.is_guest),
    login: loginStudent,
    register: registerStudent,
    loginWithGoogle,
    logout: clearAuthSession,
    updateTargetExam,
    createGuestSession: ensureAuthSession,
  };
}
