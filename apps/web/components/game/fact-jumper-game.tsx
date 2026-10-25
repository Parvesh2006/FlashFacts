"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  Trophy,
  Play,
  RotateCcw,
  Volume2,
  VolumeX,
  Sparkles,
  ArrowUp,
  ArrowDown,
  Info,
  Pause,
} from "lucide-react";

// Micro-facts displayed at every 100-point milestone
const EXAM_FACTS = [
  "The Preamble was amended only once — by the 42nd Amendment Act in 1976.",
  "Keezhadi excavations near Madurai prove an urban civilization on the Vaigai river banks dating back to the 6th century BCE.",
  "Article 32 was termed the 'Heart and Soul of the Constitution' by Dr. B.R. Ambedkar.",
  "India's first satellite, Aryabhata, was launched on 19 April 1975.",
  "The Kudavolai electoral system was practiced by the Cholas as recorded in the Uttaramerur inscriptions.",
  "The Western Ghats is one of the world's eight 'hottest hotspots' of biological diversity.",
  "The Swadeshi Steam Navigation Company was established by V.O. Chidambaram Pillai at Tuticorin in 1906.",
  "Project Tiger was launched by the Government of India in April 1973 from Corbett National Park.",
  "The Right to Education became a Fundamental Right via the 86th Constitutional Amendment Act, 2002 (Article 21A).",
  "The Reserve Bank of India was established on April 1, 1935 under the Reserve Bank of India Act, 1934.",
  "Article 17 of the Constitution of India abolishes 'Untouchability' and forbids its practice in any form.",
  "The 73rd Constitutional Amendment Act, 1992 inserted Part IX and the 11th Schedule for Panchayati Raj.",
  "ISRO was founded on August 15, 1969 under the visionary leadership of Dr. Vikram Sarabhai.",
  "The Comptroller and Auditor General (CAG) of India is appointed under Article 148 of the Constitution.",
  "Maneka Gandhi v. Union of India (1978) established that procedure under Article 21 must be just, fair and reasonable.",
];

interface Obstacle {
  x: number;
  y: number;
  width: number;
  height: number;
  type: "ground_hurdle" | "ground_books" | "overhead_drone" | "overhead_banner";
  passed?: boolean;
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  alpha: number;
  size: number;
  color: string;
}

const STORAGE_KEY_HIGH_SCORE = "flashfacts_fact_jumper_highscore";
const STORAGE_KEY_SOUND = "flashfacts_fact_jumper_sound";
const INITIAL_GAME_SPEED = 6.5;
const MAX_GAME_SPEED = 12.5;

function getGameSpeed(score: number): number {
  return Math.min(MAX_GAME_SPEED, INITIAL_GAME_SPEED + Math.max(0, score) * 0.0055);
}

interface PlayerState {
  x: number;
  y: number;
  width: number;
  height: number;
  vy: number;
  isGrounded: boolean;
  isDucking: boolean;
  runFrame: number;
}

function drawStickman(
  ctx: CanvasRenderingContext2D,
  p: PlayerState,
  groundY: number,
  time: number,
  state: string,
  distance: number
) {
  ctx.save();
  ctx.strokeStyle = "#0F172A"; // Jet black
  ctx.fillStyle = "#0F172A";
  ctx.lineWidth = 3.2;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  const isRunning = state === "RUNNING" && p.isGrounded && !p.isDucking;
  const isJumping = !p.isGrounded;
  const isDucking = p.isDucking && p.isGrounded;

  if (isDucking) {
    // --- DUCKING / CROUCHING SLIDE ANIMATION ---
    const headX = p.x + 22;
    const headY = p.y - 17;
    const neckX = p.x + 15;
    const neckY = p.y - 14;
    const hipX = p.x - 6;
    const hipY = p.y - 9;

    // Head
    ctx.beginPath();
    ctx.arc(headX, headY, 6.5, 0, Math.PI * 2);
    ctx.fill();

    // Spine (tilted forward)
    ctx.beginPath();
    ctx.moveTo(neckX, neckY);
    ctx.lineTo(hipX, hipY);
    ctx.stroke();

    // Ducking Legs (sliding forward along ground)
    ctx.beginPath();
    ctx.moveTo(hipX, hipY);
    ctx.lineTo(hipX + 16, p.y - 4);
    ctx.lineTo(hipX + 30, p.y - 1);
    ctx.moveTo(hipX, hipY);
    ctx.lineTo(hipX - 10, p.y - 6);
    ctx.lineTo(hipX - 18, p.y - 1);
    ctx.stroke();

    // Ducking Arms (tucked in streamline)
    ctx.beginPath();
    ctx.moveTo(neckX, neckY);
    ctx.lineTo(neckX + 10, p.y - 8);
    ctx.lineTo(neckX + 24, p.y - 5);
    ctx.stroke();
  } else if (isJumping) {
    // --- JUMPING POSTURE ---
    const headX = p.x + 10;
    const headY = p.y - 45;
    const neckX = p.x + 10;
    const neckY = p.y - 38;
    const hipX = p.x + 7;
    const hipY = p.y - 20;

    // Head
    ctx.beginPath();
    ctx.arc(headX, headY, 7, 0, Math.PI * 2);
    ctx.fill();

    // Spine
    ctx.beginPath();
    ctx.moveTo(neckX, neckY);
    ctx.lineTo(hipX, hipY);
    ctx.stroke();

    // Arms raised upward/outward
    ctx.beginPath();
    ctx.moveTo(neckX, neckY + 4);
    ctx.lineTo(neckX - 8, neckY - 10);
    ctx.lineTo(neckX - 12, neckY - 18);
    ctx.moveTo(neckX, neckY + 4);
    ctx.lineTo(neckX + 12, neckY - 8);
    ctx.lineTo(neckX + 16, neckY - 16);
    ctx.stroke();

    // Tucked / angled legs in air
    ctx.beginPath();
    ctx.moveTo(hipX, hipY);
    ctx.lineTo(hipX - 8, hipY + 12);
    ctx.lineTo(hipX + 2, hipY + 18);
    ctx.moveTo(hipX, hipY);
    ctx.lineTo(hipX + 8, hipY + 10);
    ctx.lineTo(hipX + 14, hipY + 16);
    ctx.stroke();
  } else {
    // --- RUNNING / IDLE GAIT ANIMATION ---
    const runCycle = isRunning ? distance * 0.16 : 0;
    const headBob = isRunning ? Math.abs(Math.sin(runCycle)) * 3 : 0;

    const headX = p.x + 10;
    const headY = p.y - 45 + headBob;
    const neckX = p.x + 10;
    const neckY = p.y - 38 + headBob;
    const hipX = p.x + 9;
    const hipY = p.y - 20 + headBob;

    // Head
    ctx.beginPath();
    ctx.arc(headX, headY, 7, 0, Math.PI * 2);
    ctx.fill();

    // Spine
    ctx.beginPath();
    ctx.moveTo(neckX, neckY);
    ctx.lineTo(hipX, hipY);
    ctx.stroke();

    // Running Legs
    const legAngle1 = isRunning ? Math.sin(runCycle) * 0.7 : 0.1;
    const legAngle2 = isRunning ? Math.sin(runCycle + Math.PI) * 0.7 : -0.1;

    const knee1X = hipX + Math.sin(legAngle1) * 12;
    const knee1Y = hipY + Math.cos(legAngle1) * 11;
    const foot1X = knee1X + Math.sin(legAngle1 + 0.3) * 11;
    const foot1Y = Math.min(groundY, knee1Y + Math.cos(legAngle1 + 0.3) * 10);

    ctx.beginPath();
    ctx.moveTo(hipX, hipY);
    ctx.lineTo(knee1X, knee1Y);
    ctx.lineTo(foot1X, foot1Y);
    ctx.stroke();

    const knee2X = hipX + Math.sin(legAngle2) * 12;
    const knee2Y = hipY + Math.cos(legAngle2) * 11;
    const foot2X = knee2X + Math.sin(legAngle2 + 0.3) * 11;
    const foot2Y = Math.min(groundY, knee2Y + Math.cos(legAngle2 + 0.3) * 10);

    ctx.beginPath();
    ctx.moveTo(hipX, hipY);
    ctx.lineTo(knee2X, knee2Y);
    ctx.lineTo(foot2X, foot2Y);
    ctx.stroke();

    // Running Arms
    const armAngle1 = isRunning ? Math.cos(runCycle) * 0.65 : -0.2;
    const armAngle2 = isRunning ? Math.cos(runCycle + Math.PI) * 0.65 : 0.2;

    ctx.beginPath();
    ctx.moveTo(neckX, neckY + 4);
    ctx.lineTo(neckX + Math.sin(armAngle1) * 10, neckY + 4 + Math.cos(armAngle1) * 9);
    ctx.lineTo(neckX + Math.sin(armAngle1 + 0.5) * 18, neckY + 4 + Math.cos(armAngle1 + 0.5) * 16);
    ctx.moveTo(neckX, neckY + 4);
    ctx.lineTo(neckX + Math.sin(armAngle2) * 10, neckY + 4 + Math.cos(armAngle2) * 9);
    ctx.lineTo(neckX + Math.sin(armAngle2 + 0.5) * 18, neckY + 4 + Math.cos(armAngle2 + 0.5) * 16);
    ctx.stroke();
  }

  ctx.restore();
}

export function FactJumperGame() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // High score and sound state
  const [score, setScore] = useState<number>(0);
  const [highScore, setHighScore] = useState<number>(0);
  const [gameState, setGameState] = useState<"IDLE" | "RUNNING" | "PAUSED" | "GAMEOVER">("IDLE");
  const [soundEnabled, setSoundEnabled] = useState<boolean>(true);
  const [activeFact, setActiveFact] = useState<string | null>(null);
  const [isDuckingState, setIsDuckingState] = useState<boolean>(false);

  // Mutable game state held in refs for 60fps render loop
  const gameStateRef = useRef<"IDLE" | "RUNNING" | "PAUSED" | "GAMEOVER">("IDLE");
  const scoreRef = useRef<number>(0);
  const highScoreRef = useRef<number>(0);
  const speedRef = useRef<number>(INITIAL_GAME_SPEED);
  const distanceRef = useRef<number>(0);
  const lastFactMilestoneRef = useRef<number>(0);

  // Player physics
  const playerRef = useRef({
    x: 80,
    y: 0,
    width: 24,
    height: 52,
    vy: 0,
    isGrounded: true,
    isDucking: false,
    runFrame: 0,
  });

  const obstaclesRef = useRef<Obstacle[]>([]);
  const particlesRef = useRef<Particle[]>([]);
  const nextSpawnDistanceRef = useRef<number>(300);
  const animFrameIdRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number>(0);
  const audioCtxRef = useRef<AudioContext | null>(null);

  // Safe localStorage helper
  const safeGetStorage = (key: string): string | null => {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        return window.localStorage.getItem(key);
      }
    } catch {
      // Storage restricted / private mode
    }
    return null;
  };

  const safeSetStorage = (key: string, val: string) => {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        window.localStorage.setItem(key, val);
      }
    } catch {
      // Storage restricted / private mode
    }
  };

  // Sound synthesis via Web Audio API (completely offline, zero network assets)
  const playSound = useCallback((type: "jump" | "duck" | "score" | "crash") => {
    if (!soundEnabled) return;
    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (!audioCtxRef.current) {
        audioCtxRef.current = new AudioCtx();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === "suspended") {
        ctx.resume();
      }

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      const now = ctx.currentTime;
      if (type === "jump") {
        osc.type = "sine";
        osc.frequency.setValueAtTime(320, now);
        osc.frequency.exponentialRampToValueAtTime(640, now + 0.1);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.1);
        osc.start(now);
        osc.stop(now + 0.1);
      } else if (type === "duck") {
        osc.type = "triangle";
        osc.frequency.setValueAtTime(260, now);
        osc.frequency.linearRampToValueAtTime(180, now + 0.08);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.08);
        osc.start(now);
        osc.stop(now + 0.08);
      } else if (type === "score") {
        osc.type = "sine";
        osc.frequency.setValueAtTime(587.33, now); // D5
        osc.frequency.setValueAtTime(880, now + 0.08); // A5
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.22);
        osc.start(now);
        osc.stop(now + 0.22);
      } else if (type === "crash") {
        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(140, now);
        osc.frequency.exponentialRampToValueAtTime(40, now + 0.25);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.25);
        osc.start(now);
        osc.stop(now + 0.25);
      }
    } catch {
      // AudioContext unavailable
    }
  }, [soundEnabled]);

  // Load saved high score and sound preferences
  useEffect(() => {
    const savedScore = safeGetStorage(STORAGE_KEY_HIGH_SCORE);
    if (savedScore) {
      const parsed = parseInt(savedScore, 10);
      if (!isNaN(parsed)) {
        setHighScore(parsed);
        highScoreRef.current = parsed;
      }
    }

    const savedSound = safeGetStorage(STORAGE_KEY_SOUND);
    if (savedSound !== null) {
      setSoundEnabled(savedSound === "true");
    }
  }, []);

  const toggleSound = () => {
    setSoundEnabled((prev) => {
      const next = !prev;
      safeSetStorage(STORAGE_KEY_SOUND, String(next));
      return next;
    });
  };

  // Start game
  const startGame = useCallback(() => {
    gameStateRef.current = "RUNNING";
    setGameState("RUNNING");
    scoreRef.current = 0;
    setScore(0);
    speedRef.current = INITIAL_GAME_SPEED;
    distanceRef.current = 0;
    lastFactMilestoneRef.current = 0;
    obstaclesRef.current = [];
    particlesRef.current = [];
    nextSpawnDistanceRef.current = 320;
    setActiveFact(null);

    const canvas = canvasRef.current;
    if (canvas) {
      const groundY = canvas.height - 40;
      playerRef.current.y = groundY;
      playerRef.current.vy = 0;
      playerRef.current.isGrounded = true;
      playerRef.current.isDucking = false;
      setIsDuckingState(false);
    }
  }, []);

  // Reset after game over
  const resetGame = useCallback(() => {
    startGame();
  }, [startGame]);

  // Start running as soon as the game page is ready.
  useEffect(() => {
    startGame();
  }, [startGame]);

  // Resume game
  const resumeGame = useCallback(() => {
    gameStateRef.current = "RUNNING";
    setGameState("RUNNING");
    lastTimeRef.current = performance.now();
  }, []);

  // Trigger jump
  const triggerJump = useCallback(() => {
    if (gameStateRef.current === "IDLE") {
      startGame();
      return;
    }
    if (gameStateRef.current === "GAMEOVER") {
      resetGame();
      return;
    }
    if (gameStateRef.current === "PAUSED") {
      resumeGame();
      return;
    }

    const p = playerRef.current;
    if (p.isGrounded && !p.isDucking) {
      p.vy = -13.2;
      p.isGrounded = false;
      playSound("jump");

      // Spawn jump dust particles
      for (let i = 0; i < 5; i++) {
        particlesRef.current.push({
          x: p.x + 8 + (Math.random() * 8 - 4),
          y: p.y,
          vx: -(Math.random() * 2 + 1),
          vy: -(Math.random() * 2),
          alpha: 0.7,
          size: Math.random() * 3 + 2,
          color: "#94A3B8",
        });
      }
    }
  }, [playSound, startGame, resetGame, resumeGame]);

  // Trigger duck
  const setDucking = useCallback((ducking: boolean) => {
    if (gameStateRef.current !== "RUNNING") return;
    const p = playerRef.current;
    if (ducking && !p.isDucking) {
      p.isDucking = true;
      setIsDuckingState(true);
      playSound("duck");
    } else if (!ducking && p.isDucking) {
      p.isDucking = false;
      setIsDuckingState(false);
    }
  }, [playSound]);

  // Pause / Resume toggle
  const togglePause = useCallback(() => {
    if (gameStateRef.current === "RUNNING") {
      gameStateRef.current = "PAUSED";
      setGameState("PAUSED");
    } else if (gameStateRef.current === "PAUSED") {
      gameStateRef.current = "RUNNING";
      setGameState("RUNNING");
      lastTimeRef.current = performance.now();
    }
  }, []);

  // Keyboard controls with scroll prevention and fair repeat blocking
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Prevent browser from scrolling on arrow keys and space when interacting with the game
      if (["Space", "ArrowUp", "ArrowDown", "KeyW", "KeyS", "KeyP", "KeyR"].includes(e.code)) {
        e.preventDefault();
      }

      if (e.code === "Space" || e.code === "ArrowUp" || e.code === "KeyW") {
        if (!e.repeat) {
          triggerJump();
        }
      } else if (e.code === "ArrowDown" || e.code === "KeyS") {
        setDucking(true);
      } else if (e.code === "KeyP") {
        if (!e.repeat) {
          togglePause();
        }
      } else if (e.code === "KeyR") {
        if (!e.repeat && gameStateRef.current === "GAMEOVER") {
          resetGame();
        }
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === "ArrowDown" || e.code === "KeyS") {
        setDucking(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown, { passive: false });
    window.addEventListener("keyup", handleKeyUp, { passive: false });

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [triggerJump, setDucking, togglePause, resetGame]);

  // Main canvas rendering & animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Retina display scaling
    const dpr = typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1;
    const logicalWidth = 840;
    const logicalHeight = 320;

    canvas.width = logicalWidth * dpr;
    canvas.height = logicalHeight * dpr;
    ctx.scale(dpr, dpr);

    const groundY = logicalHeight - 40;
    playerRef.current.y = groundY;

    // Detect user reduced motion preference
    const prefersReducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const render = (currentTime: number) => {
      animFrameIdRef.current = requestAnimationFrame(render);

      if (!lastTimeRef.current) lastTimeRef.current = currentTime;
      const frameScale = Math.min(3, Math.max(0, (currentTime - lastTimeRef.current) / (1000 / 60)));
      lastTimeRef.current = currentTime;

      const state = gameStateRef.current;
      const speed = speedRef.current;
      const p = playerRef.current;

      // 1. Dynamic background shade transition between white & light grey
      // Subtle oscillation between #FFFFFF, #F8F9FA, #F1F3F5, #E9ECEF
      let bgShade = 255;
      if (!prefersReducedMotion) {
        bgShade = Math.floor(248 + Math.sin(distanceRef.current * 0.0025) * 7);
      }
      ctx.fillStyle = `rgb(${bgShade}, ${bgShade}, ${bgShade})`;
      ctx.fillRect(0, 0, logicalWidth, logicalHeight);

      // Draw subtle background grid/pattern dots for depth
      ctx.fillStyle = "rgba(100, 116, 139, 0.07)";
      for (let gx = 0; gx < logicalWidth; gx += 40) {
        for (let gy = 0; gy < groundY; gy += 40) {
          ctx.beginPath();
          ctx.arc(gx, gy, 1, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // 2. Draw ground line with moving track hashes
      ctx.strokeStyle = "#1E293B";
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.moveTo(0, groundY);
      ctx.lineTo(logicalWidth, groundY);
      ctx.stroke();

      // Moving track ticks
      ctx.strokeStyle = "rgba(100, 116, 139, 0.4)";
      ctx.lineWidth = 1.5;
      const trackOffset = (distanceRef.current % 30);
      for (let tx = -trackOffset; tx < logicalWidth; tx += 30) {
        ctx.beginPath();
        ctx.moveTo(tx, groundY + 4);
        ctx.lineTo(tx + 12, groundY + 4);
        ctx.stroke();
      }

      // 3. Update game mechanics if RUNNING
      if (state === "RUNNING") {
        distanceRef.current += speed * frameScale;
        const currentPoints = Math.floor(distanceRef.current / 10);
        scoreRef.current = currentPoints;
        setScore(currentPoints);

        // Update high score
        if (currentPoints > highScoreRef.current) {
          highScoreRef.current = currentPoints;
          setHighScore(currentPoints);
          safeSetStorage(STORAGE_KEY_HIGH_SCORE, String(currentPoints));
        }

        speedRef.current = getGameSpeed(currentPoints);

        // Milestone Fact Announcement every 100 points
        const currentHundred = Math.floor(currentPoints / 100);
        if (currentHundred > lastFactMilestoneRef.current && currentHundred > 0) {
          lastFactMilestoneRef.current = currentHundred;
          const factIndex = (currentHundred - 1) % EXAM_FACTS.length;
          setActiveFact(EXAM_FACTS[factIndex]);
          playSound("score");

          // Burst milestone particles
          for (let i = 0; i < 20; i++) {
            particlesRef.current.push({
              x: p.x + 20,
              y: p.y - 30,
              vx: (Math.random() - 0.5) * 8,
              vy: (Math.random() - 0.5) * 8,
              alpha: 1.0,
              size: Math.random() * 4 + 2,
              color: i % 2 === 0 ? "#F59E0B" : "#3B82F6",
            });
          }
        }

        // Player physics update
        if (!p.isGrounded) {
          p.vy += 0.65 * frameScale; // Gravity stays consistent across refresh rates.
          p.y += p.vy * frameScale;

          if (p.y >= groundY) {
            p.y = groundY;
            p.vy = 0;
            p.isGrounded = true;

            // Landing dust
            for (let i = 0; i < 4; i++) {
              particlesRef.current.push({
                x: p.x + 8 + (Math.random() * 8 - 4),
                y: groundY,
                vx: -(Math.random() * 2 + 1),
                vy: -(Math.random() * 1.5),
                alpha: 0.6,
                size: Math.random() * 3 + 1,
                color: "#94A3B8",
              });
            }
          }
        }

        // Dust while running on ground
        if (p.isGrounded && Math.random() < 1 - Math.pow(0.75, frameScale)) {
          particlesRef.current.push({
            x: p.x + (p.isDucking ? -5 : 4),
            y: groundY - 2,
            vx: -(speed * 0.4 + Math.random() * 1.5),
            vy: -(Math.random() * 1.2),
            alpha: 0.5,
            size: Math.random() * 2.5 + 1.5,
            color: "#CBD5E1",
          });
        }

        // Spawn obstacles with fair spacing
        if (distanceRef.current >= nextSpawnDistanceRef.current) {
          const rand = Math.random();
          let obsType: Obstacle["type"] = "ground_hurdle";
          let obsW = 22;
          let obsH = 38;
          let obsY = groundY - obsH;

          // 30% chance for overhead obstacles that require ducking
          if (rand > 0.7) {
            obsType = rand > 0.85 ? "overhead_drone" : "overhead_banner";
            obsW = 38;
            obsH = 22;
            // Placed at head level: standing hits it, ducking slides under it!
            obsY = groundY - 58;
          } else if (rand > 0.35) {
            obsType = "ground_books";
            obsW = 34;
            obsH = 42;
            obsY = groundY - obsH;
          }

          obstaclesRef.current.push({
            x: logicalWidth + 20,
            y: obsY,
            width: obsW,
            height: obsH,
            type: obsType,
          });

          // Next spawn interval scales with speed for fair reflex windows
          const minGap = Math.max(300, speed * 52);
          const randomExtra = 140 + Math.random() * 140;
          nextSpawnDistanceRef.current = distanceRef.current + minGap + randomExtra;
        }

        // Move obstacles and check collisions
        for (let i = obstaclesRef.current.length - 1; i >= 0; i--) {
          const obs = obstaclesRef.current[i];
          obs.x -= speed * frameScale;

          // Remove offscreen obstacles
          if (obs.x + obs.width < -30) {
            obstaclesRef.current.splice(i, 1);
            continue;
          }

          // Accurate Multi-Box Collision Detection
          // Standing hitbox: width 22, height 52, y from p.y - 52 to p.y
          // Ducking hitbox: width 34, height 24, y from p.y - 24 to p.y (crouched low)
          const playerBox = p.isDucking
            ? { x: p.x - 4, y: p.y - 24, w: 34, h: 24 }
            : { x: p.x + 2, y: p.y - 52, w: 20, h: 52 };

          // Bounding box overlap with 3px grace margin for fair gameplay
          const collision =
            playerBox.x + 3 < obs.x + obs.width - 3 &&
            playerBox.x + playerBox.w - 3 > obs.x + 3 &&
            playerBox.y + 3 < obs.y + obs.height - 3 &&
            playerBox.y + playerBox.h - 3 > obs.y + 3;

          if (collision) {
            gameStateRef.current = "GAMEOVER";
            setGameState("GAMEOVER");
            playSound("crash");

            // Crash particles
            for (let c = 0; c < 25; c++) {
              particlesRef.current.push({
                x: p.x + 12,
                y: p.y - 26,
                vx: (Math.random() - 0.5) * 10,
                vy: (Math.random() - 0.5) * 10,
                alpha: 1.0,
                size: Math.random() * 4 + 2,
                color: "#EF4444",
              });
            }
            break;
          }
        }
      }

      // 4. Update and render particles
      for (let i = particlesRef.current.length - 1; i >= 0; i--) {
        const pt = particlesRef.current[i];
        pt.x += pt.vx * frameScale;
        pt.y += pt.vy * frameScale;
        pt.alpha -= 0.025 * frameScale;
        if (pt.alpha <= 0) {
          particlesRef.current.splice(i, 1);
          continue;
        }

        ctx.fillStyle = pt.color;
        ctx.globalAlpha = Math.max(0, pt.alpha);
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, pt.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1.0;
      }

      // 5. Draw Obstacles
      for (const obs of obstaclesRef.current) {
        ctx.fillStyle = "#0F172A"; // High contrast solid black
        ctx.strokeStyle = "#0F172A";
        ctx.lineWidth = 2;

        if (obs.type === "ground_hurdle") {
          // Minimalist Track Hurdle
          ctx.beginPath();
          // Crossbar
          ctx.rect(obs.x, obs.y, obs.width, 7);
          ctx.fill();
          // Two legs
          ctx.fillRect(obs.x + 2, obs.y + 7, 3, obs.height - 7);
          ctx.fillRect(obs.x + obs.width - 5, obs.y + 7, 3, obs.height - 7);
          // Ground feet
          ctx.fillRect(obs.x, obs.y + obs.height - 2, 7, 2);
          ctx.fillRect(obs.x + obs.width - 7, obs.y + obs.height - 2, 7, 2);
        } else if (obs.type === "ground_books") {
          // Stack of 3 Study Books (FlashFacts Exam Theme)
          const bookHeight = obs.height / 3;
          for (let b = 0; b < 3; b++) {
            const by = obs.y + b * bookHeight;
            const bw = obs.width - (b === 1 ? 4 : 0);
            const bx = obs.x + (b === 1 ? 2 : 0);
            ctx.fillStyle = "#0F172A";
            ctx.fillRect(bx, by, bw, bookHeight - 2);
            // Spine highlight
            ctx.fillStyle = "#FFFFFF";
            ctx.fillRect(bx + 2, by + 2, 2, bookHeight - 6);
          }
        } else if (obs.type === "overhead_drone") {
          // Flying Exam Surveillance Drone (Overhead obstacle - duck to pass!)
          // Propeller line
          ctx.beginPath();
          ctx.moveTo(obs.x - 4, obs.y + 3);
          ctx.lineTo(obs.x + obs.width + 4, obs.y + 3);
          ctx.stroke();
          // Drone body
          ctx.fillRect(obs.x + 6, obs.y + 4, obs.width - 12, obs.height - 8);
          // Blinking warning beacon
          ctx.fillStyle = Math.floor(currentTime / 200) % 2 === 0 ? "#EF4444" : "#F59E0B";
          ctx.beginPath();
          ctx.arc(obs.x + obs.width / 2, obs.y + obs.height / 2, 3, 0, Math.PI * 2);
          ctx.fill();
          // Legs
          ctx.strokeStyle = "#0F172A";
          ctx.beginPath();
          ctx.moveTo(obs.x + 8, obs.y + obs.height - 4);
          ctx.lineTo(obs.x + 6, obs.y + obs.height);
          ctx.moveTo(obs.x + obs.width - 8, obs.y + obs.height - 4);
          ctx.lineTo(obs.x + obs.width - 6, obs.y + obs.height);
          ctx.stroke();
        } else if (obs.type === "overhead_banner") {
          // Overhead Exam Alert Ribbon
          ctx.fillRect(obs.x, obs.y, obs.width, obs.height - 4);
          ctx.fillStyle = "#FFFFFF";
          ctx.font = "bold 9px monospace";
          ctx.fillText("DUCK", obs.x + 7, obs.y + 12);
        }
      }

      // 6. Draw Animated Stickman
      drawStickman(ctx, p, groundY, currentTime, state, distanceRef.current);

      // 7. Render In-Game HUD (Score, Best Score, Speed)
      ctx.fillStyle = "#0F172A";
      ctx.font = "bold 15px monospace";
      ctx.textAlign = "right";
      const scoreStr = String(scoreRef.current).padStart(5, "0");
      const highStr = String(highScoreRef.current).padStart(5, "0");
      ctx.fillText(`SCORE: ${scoreStr}`, logicalWidth - 25, 32);

      ctx.fillStyle = "#64748B";
      ctx.font = "12px monospace";
      ctx.fillText(`BEST:  ${highStr}`, logicalWidth - 25, 50);

      // Speed indicator
      ctx.textAlign = "left";
      ctx.fillStyle = "#64748B";
      ctx.font = "11px monospace";
      ctx.fillText(`SPEED: ${(speedRef.current).toFixed(1)}x`, 25, 32);

      // Active Exam Fact Banner at top center
      if (activeFact) {
        ctx.save();
        ctx.fillStyle = "#1E293B";
        ctx.font = "11px system-ui, -apple-system, sans-serif";
        ctx.textAlign = "center";
        const maxFactWidth = logicalWidth - 360;
        let truncated = activeFact;
        if (ctx.measureText(truncated).width > maxFactWidth) {
          while (ctx.measureText(truncated + "...").width > maxFactWidth && truncated.length > 10) {
            truncated = truncated.slice(0, -1);
          }
          truncated += "...";
        }

        ctx.fillStyle = "rgba(245, 158, 11, 0.12)";
        ctx.strokeStyle = "#F59E0B";
        ctx.lineWidth = 1;
        const bannerW = ctx.measureText(truncated).width + 36;
        ctx.beginPath();
        ctx.roundRect((logicalWidth - bannerW) / 2, 14, bannerW, 26, 6);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = "#D97706";
        ctx.font = "bold 10px monospace";
        ctx.fillText("★ EXAM FACT: ", (logicalWidth - bannerW) / 2 + 48, 30);
        ctx.fillStyle = "#1E293B";
        ctx.font = "11px system-ui, sans-serif";
        ctx.fillText(truncated, (logicalWidth + 60) / 2, 30);
        ctx.restore();
      }

      // 8. Overlays for PAUSED and GAMEOVER
      if (state === "PAUSED") {
        ctx.fillStyle = "rgba(15, 23, 42, 0.6)";
        ctx.fillRect(0, 0, logicalWidth, logicalHeight);

        ctx.fillStyle = "#FFFFFF";
        ctx.font = "bold 24px system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("GAME PAUSED", logicalWidth / 2, logicalHeight / 2 - 10);

        ctx.font = "13px monospace";
        ctx.fillStyle = "#CBD5E1";
        ctx.fillText("Press P or Tap anywhere to Resume", logicalWidth / 2, logicalHeight / 2 + 20);
      } else if (state === "GAMEOVER") {
        ctx.fillStyle = "rgba(15, 23, 42, 0.82)";
        ctx.fillRect(0, 0, logicalWidth, logicalHeight);

        ctx.fillStyle = "#EF4444";
        ctx.font = "bold 28px system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("GAME OVER", logicalWidth / 2, logicalHeight / 2 - 40);

        ctx.fillStyle = "#FFFFFF";
        ctx.font = "bold 16px monospace";
        ctx.fillText(`SCORE: ${scoreRef.current}   |   BEST: ${highScoreRef.current}`, logicalWidth / 2, logicalHeight / 2 - 5);

        if (scoreRef.current >= highScoreRef.current && scoreRef.current > 0) {
          ctx.fillStyle = "#F59E0B";
          ctx.font = "bold 13px monospace";
          ctx.fillText("★ NEW HIGH SCORE! ★", logicalWidth / 2, logicalHeight / 2 + 20);
        }

        ctx.fillStyle = "#E2E8F0";
        ctx.font = "13px monospace";
        ctx.fillText("Press SPACE, R, or Tap to Restart", logicalWidth / 2, logicalHeight / 2 + 46);
      }
    };

    lastTimeRef.current = performance.now();
    animFrameIdRef.current = requestAnimationFrame(render);

    return () => {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
    };
  }, [activeFact, playSound]);

  // Canvas click / touch handler: split controls (top 65% = jump, bottom 35% = duck)
  const handleCanvasPointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    if (gameStateRef.current === "IDLE") {
      startGame();
      return;
    }
    if (gameStateRef.current === "GAMEOVER") {
      resetGame();
      return;
    }
    if (gameStateRef.current === "PAUSED") {
      resumeGame();
      return;
    }

    const rect = e.currentTarget.getBoundingClientRect();
    const relativeY = e.clientY - rect.top;
    const height = rect.height;

    if (relativeY > height * 0.65) {
      setDucking(true);
    } else {
      triggerJump();
    }
  };

  const handleCanvasPointerUp = () => {
    if (playerRef.current.isDucking) {
      setDucking(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      {/* Game Header Bar */}
      <div className="editorial-card p-4 sm:p-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[var(--surface-muted)] flex items-center justify-center font-bold text-lg text-[var(--brand-primary)]">
            🏃
          </div>
          <div>
            <h2 className="headline text-xl sm:text-2xl font-bold flex items-center gap-2">
              <span>Fact Jumper</span>
              <span className="soft-badge text-[10px] font-mono uppercase bg-[var(--brand-primary-soft)] text-[var(--brand-primary)]">
                Offline
              </span>
            </h2>
            <p className="meta-text text-xs">
              Minimalist offline stickman runner • Clear exam hurdles & duck under drones
            </p>
          </div>
        </div>

        {/* Action Controls & Score Pills */}
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border bg-[var(--surface-muted)] text-xs font-mono">
            <Trophy className="w-3.5 h-3.5 text-amber-500" />
            <span className="text-[var(--text-secondary)]">BEST:</span>
            <span className="font-bold text-[var(--text-primary)]">{highScore}</span>
          </div>

          <button
            type="button"
            onClick={toggleSound}
            className="control p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            title={soundEnabled ? "Mute Game Sound" : "Enable Game Sound"}
            aria-label="Toggle sound"
          >
            {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </button>

          {gameState === "RUNNING" && (
            <button
              type="button"
              onClick={togglePause}
              className="control p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              title="Pause Game"
              aria-label="Pause game"
            >
              <Pause className="w-4 h-4" />
            </button>
          )}

          {gameState === "PAUSED" && (
            <button
              type="button"
              onClick={resumeGame}
              className="brand-button text-xs font-mono px-3 py-1.5 flex items-center gap-1"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Resume</span>
            </button>
          )}

          {gameState === "GAMEOVER" && (
            <button
              type="button"
              onClick={resetGame}
              className="brand-button text-xs font-mono px-3 py-1.5 flex items-center gap-1"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Restart</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Canvas Frame */}
      <div className="relative rounded-2xl overflow-hidden border border-[var(--border-subtle)] shadow-sm bg-white touch-none select-none">
        <canvas
          ref={canvasRef}
          onPointerDown={handleCanvasPointerDown}
          onPointerUp={handleCanvasPointerUp}
          onPointerCancel={handleCanvasPointerUp}
          className="w-full aspect-[2.6/1] block cursor-pointer transition-colors duration-500"
          title="Click upper area to Jump, lower area to Duck"
        />
      </div>

      {/* Controls Bar & Mobile Touch Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Mobile / Click On-Screen Buttons */}
        <div className="editorial-card p-3 flex gap-2">
          <button
            type="button"
            onPointerDown={(e) => {
              e.preventDefault();
              triggerJump();
            }}
            className="flex-1 py-3 px-4 rounded-xl font-mono text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 bg-[var(--surface-muted)] hover:bg-[var(--brand-primary-soft)] hover:text-[var(--brand-primary)] border transition-colors active:scale-95"
          >
            <ArrowUp className="w-4 h-4" />
            <span>JUMP (SPACE / UP)</span>
          </button>

          <button
            type="button"
            onPointerDown={(e) => {
              e.preventDefault();
              setDucking(true);
            }}
            onPointerUp={(e) => {
              e.preventDefault();
              setDucking(false);
            }}
            onPointerLeave={() => setDucking(false)}
            onPointerCancel={() => setDucking(false)}
            className={`flex-1 py-3 px-4 rounded-xl font-mono text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 border transition-all active:scale-95 ${
              isDuckingState
                ? "bg-[var(--brand-primary)] text-white border-[var(--brand-primary)]"
                : "bg-[var(--surface-muted)] hover:bg-[var(--surface-elevated)]"
            }`}
          >
            <ArrowDown className="w-4 h-4" />
            <span>DUCK (HOLD DOWN)</span>
          </button>
        </div>

        {/* Quick Instructions & Fact Milestone Info */}
        <div className="editorial-card p-3 flex items-center justify-between text-xs font-mono text-[var(--text-secondary)]">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-[var(--brand-primary)] shrink-0" />
            <span>Jump over books & hurdles • Duck under low drones • P to pause</span>
          </div>
          <span className="shrink-0 flex items-center gap-1 font-semibold text-[var(--brand-primary)]">
            <Sparkles className="w-3.5 h-3.5" />
            <span>100pts = New Fact</span>
          </span>
        </div>
      </div>
    </div>
  );
}
