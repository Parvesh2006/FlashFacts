"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  Trophy,
  Play,
  RotateCcw,
  Volume2,
  VolumeX,
  ArrowUp,
  ArrowDown,
  Info,
  Pause,
} from "lucide-react";

// --- Canvas & Ground Coordinates: Single Source of Truth ---
export const GAME_CANVAS_WIDTH = 840;
export const GAME_CANVAS_HEIGHT = 320;
export const GAME_GROUND_OFFSET = 40;
export const GAME_GROUND_Y = GAME_CANVAS_HEIGHT - GAME_GROUND_OFFSET; // Exactly 280
export const PLAYER_INITIAL_X = 80;
export const PLAYER_HEIGHT_STAND = 52;
export const PLAYER_HEIGHT_DUCK = 22;

export type ObstacleType =
  | "ground_hurdle"
  | "ground_books"
  | "bird_low"
  | "bird_mid"
  | "bird_high";

export interface Obstacle {
  x: number;
  y: number;
  width: number;
  height: number;
  type: ObstacleType;
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

export interface GamePhysicsConfig {
  initialSpeed: number;        // Comfortable initial speed matching early Chrome T-Rex
  maxSpeed: number;            // Capped upper limit to remain playable
  acceleration: number;        // Gradual speed increment per score point
  gravity: number;             // Downward acceleration per tick
  jumpImpulse: number;         // Controlled vertical impulse (predictable arc, stays inside viewport)
  groundOffset: number;        // Distance from canvas bottom to ground line
  minObstacleGap: number;      // Base minimum spacing between obstacles
}

export const DEFAULT_GAME_CONFIG: GamePhysicsConfig = {
  initialSpeed: 4.8,
  maxSpeed: 9.5,
  acceleration: 0.0035,
  gravity: 0.60,
  jumpImpulse: -10.2,
  groundOffset: GAME_GROUND_OFFSET,
  minObstacleGap: 340,
};

function getGameSpeed(score: number, config: GamePhysicsConfig = DEFAULT_GAME_CONFIG): number {
  return Math.min(config.maxSpeed, config.initialSpeed + Math.max(0, score) * config.acceleration);
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

// --- Animated Stickman Drawing ---
function drawStickman(
  ctx: CanvasRenderingContext2D,
  p: PlayerState,
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

    // Running Legs (feet clamped to p.y = GAME_GROUND_Y)
    const legAngle1 = isRunning ? Math.sin(runCycle) * 0.7 : 0.1;
    const legAngle2 = isRunning ? Math.sin(runCycle + Math.PI) * 0.7 : -0.1;

    const knee1X = hipX + Math.sin(legAngle1) * 12;
    const knee1Y = hipY + Math.cos(legAngle1) * 11;
    const foot1X = knee1X + Math.sin(legAngle1 + 0.3) * 11;
    const foot1Y = Math.min(p.y, knee1Y + Math.cos(legAngle1 + 0.3) * 10);

    ctx.beginPath();
    ctx.moveTo(hipX, hipY);
    ctx.lineTo(knee1X, knee1Y);
    ctx.lineTo(foot1X, foot1Y);
    ctx.stroke();

    const knee2X = hipX + Math.sin(legAngle2) * 12;
    const knee2Y = hipY + Math.cos(legAngle2) * 11;
    const foot2X = knee2X + Math.sin(legAngle2 + 0.3) * 11;
    const foot2Y = Math.min(p.y, knee2Y + Math.cos(legAngle2 + 0.3) * 10);

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

// --- Flying Bird Obstacle Drawing (2-Frame Flapping Wing Animation) ---
function drawBird(
  ctx: CanvasRenderingContext2D,
  obs: Obstacle,
  time: number
) {
  ctx.save();
  ctx.fillStyle = "#0F172A"; // High contrast crisp black
  ctx.strokeStyle = "#0F172A";
  ctx.lineWidth = 2.2;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  const bx = obs.x;
  const by = obs.y;

  // 2-frame wing flap based on time: ~140ms per frame
  const flapFrame = Math.floor(time / 140) % 2;

  // 1. Sleek aerodynamic bird body (flying towards left)
  ctx.beginPath();
  ctx.moveTo(bx + 8, by + 11);
  ctx.lineTo(bx + 26, by + 9);
  ctx.lineTo(bx + 32, by + 11);
  ctx.lineTo(bx + 24, by + 16);
  ctx.lineTo(bx + 11, by + 15);
  ctx.closePath();
  ctx.fill();

  // 2. Beak (pointing forward/left towards player)
  ctx.beginPath();
  ctx.moveTo(bx + 9, by + 9);
  ctx.lineTo(bx + 1, by + 12);
  ctx.lineTo(bx + 9, by + 14);
  ctx.closePath();
  ctx.fill();

  // 3. Eye
  ctx.fillStyle = "#FFFFFF";
  ctx.beginPath();
  ctx.arc(bx + 7, by + 11, 1.2, 0, Math.PI * 2);
  ctx.fill();

  // 4. Wings (2 distinct flapping positions)
  ctx.fillStyle = "#0F172A";
  ctx.strokeStyle = "#0F172A";
  ctx.lineWidth = 2.4;

  if (flapFrame === 0) {
    // Frame 0: Wings UP
    ctx.beginPath();
    ctx.moveTo(bx + 14, by + 10);
    ctx.lineTo(bx + 11, by + 2); // Wing tip high
    ctx.lineTo(bx + 19, by + 4);
    ctx.lineTo(bx + 22, by + 10);
    ctx.closePath();
    ctx.fill();

    // Far wing peek
    ctx.beginPath();
    ctx.moveTo(bx + 18, by + 9);
    ctx.lineTo(bx + 17, by + 4);
    ctx.lineTo(bx + 23, by + 6);
    ctx.stroke();
  } else {
    // Frame 1: Wings DOWN
    ctx.beginPath();
    ctx.moveTo(bx + 14, by + 12);
    ctx.lineTo(bx + 11, by + 20); // Wing tip low
    ctx.lineTo(bx + 19, by + 18);
    ctx.lineTo(bx + 22, by + 12);
    ctx.closePath();
    ctx.fill();

    // Far wing peek
    ctx.beginPath();
    ctx.moveTo(bx + 18, by + 13);
    ctx.lineTo(bx + 17, by + 18);
    ctx.lineTo(bx + 23, by + 16);
    ctx.stroke();
  }

  // 5. Tail feathers
  ctx.beginPath();
  ctx.moveTo(bx + 31, by + 10);
  ctx.lineTo(bx + 36, by + 8);
  ctx.moveTo(bx + 31, by + 12);
  ctx.lineTo(bx + 36, by + 14);
  ctx.stroke();

  ctx.restore();
}

export interface FactJumperGameProps {
  config?: Partial<GamePhysicsConfig>;
  autoStart?: boolean;
  onReturnToApp?: () => void;
}

export function FactJumperGame({ config, autoStart = true, onReturnToApp }: FactJumperGameProps = {}) {
  const physics = { ...DEFAULT_GAME_CONFIG, ...config };
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // High score and sound state
  const [score, setScore] = useState<number>(0);
  const [highScore, setHighScore] = useState<number>(0);
  const [gameState, setGameState] = useState<"IDLE" | "RUNNING" | "PAUSED" | "GAMEOVER">("IDLE");
  const [soundEnabled, setSoundEnabled] = useState<boolean>(true);
  const [isDuckingState, setIsDuckingState] = useState<boolean>(false);

  // Mutable game state held in refs for 60fps render loop
  const gameStateRef = useRef<"IDLE" | "RUNNING" | "PAUSED" | "GAMEOVER">("IDLE");
  const scoreRef = useRef<number>(0);
  const highScoreRef = useRef<number>(0);
  const speedRef = useRef<number>(physics.initialSpeed);
  const distanceRef = useRef<number>(0);
  const lastMilestoneRef = useRef<number>(0);

  // Player physics
  const playerRef = useRef<PlayerState>({
    x: PLAYER_INITIAL_X,
    y: GAME_GROUND_Y,
    width: 24,
    height: PLAYER_HEIGHT_STAND,
    vy: 0,
    isGrounded: true,
    isDucking: false,
    runFrame: 0,
  });

  const obstaclesRef = useRef<Obstacle[]>([]);
  const particlesRef = useRef<Particle[]>([]);
  const nextSpawnDistanceRef = useRef<number>(320);
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

  // Start game - firmly anchor to GAME_GROUND_Y
  const startGame = useCallback(() => {
    gameStateRef.current = "RUNNING";
    setGameState("RUNNING");
    scoreRef.current = 0;
    setScore(0);
    speedRef.current = physics.initialSpeed;
    distanceRef.current = 0;
    lastMilestoneRef.current = 0;
    obstaclesRef.current = [];
    particlesRef.current = [];
    nextSpawnDistanceRef.current = 320;

    // Firm ground coordinate guarantee
    playerRef.current.x = PLAYER_INITIAL_X;
    playerRef.current.y = GAME_GROUND_Y;
    playerRef.current.vy = 0;
    playerRef.current.isGrounded = true;
    playerRef.current.isDucking = false;
    setIsDuckingState(false);
  }, [physics.initialSpeed]);

  // Reset after game over
  const resetGame = useCallback(() => {
    startGame();
  }, [startGame]);

  // Start running as soon as the game page is ready.
  useEffect(() => {
    if (autoStart) {
      startGame();
    }
  }, [startGame, autoStart]);

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
      p.vy = physics.jumpImpulse;
      p.isGrounded = false;
      playSound("jump");

      // Spawn jump dust particles
      for (let i = 0; i < 5; i++) {
        particlesRef.current.push({
          x: p.x + 8 + (Math.random() * 8 - 4),
          y: GAME_GROUND_Y,
          vx: -(Math.random() * 2 + 1),
          vy: -(Math.random() * 2),
          alpha: 0.7,
          size: Math.random() * 3 + 2,
          color: "#94A3B8",
        });
      }
    }
  }, [playSound, startGame, resetGame, resumeGame, physics.jumpImpulse]);

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

  // Main canvas rendering & animation loop with responsive resize guarantee
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Retina / High-DPI display scaling with consistent logical dimensions
    const configureCanvas = () => {
      const dpr = typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1;
      canvas.width = GAME_CANVAS_WIDTH * dpr;
      canvas.height = GAME_CANVAS_HEIGHT * dpr;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.scale(dpr, dpr);
      }
      // Re-anchor grounded player on resize
      if (playerRef.current.isGrounded) {
        playerRef.current.y = GAME_GROUND_Y;
        playerRef.current.vy = 0;
      }
    };

    configureCanvas();
    window.addEventListener("resize", configureCanvas);

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Detect user reduced motion preference
    const prefersReducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const render = (currentTime: number) => {
      animFrameIdRef.current = requestAnimationFrame(render);

      if (!lastTimeRef.current) lastTimeRef.current = currentTime;
      const frameScale = Math.min(2.5, Math.max(0.2, (currentTime - lastTimeRef.current) / (1000 / 60)));
      lastTimeRef.current = currentTime;

      const state = gameStateRef.current;
      const speed = speedRef.current;
      const p = playerRef.current;

      // 1. Dynamic background shade transition between white & light grey
      let bgShade = 255;
      if (!prefersReducedMotion) {
        bgShade = Math.floor(248 + Math.sin(distanceRef.current * 0.0025) * 7);
      }
      ctx.fillStyle = `rgb(${bgShade}, ${bgShade}, ${bgShade})`;
      ctx.fillRect(0, 0, GAME_CANVAS_WIDTH, GAME_CANVAS_HEIGHT);

      // Draw subtle background grid dots for depth
      ctx.fillStyle = "rgba(100, 116, 139, 0.07)";
      for (let gx = 0; gx < GAME_CANVAS_WIDTH; gx += 40) {
        for (let gy = 0; gy < GAME_GROUND_Y; gy += 40) {
          ctx.beginPath();
          ctx.arc(gx, gy, 1, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // 2. Draw ground line with moving track hashes
      ctx.strokeStyle = "#1E293B";
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.moveTo(0, GAME_GROUND_Y);
      ctx.lineTo(GAME_CANVAS_WIDTH, GAME_GROUND_Y);
      ctx.stroke();

      // Moving track ticks
      ctx.strokeStyle = "rgba(100, 116, 139, 0.4)";
      ctx.lineWidth = 1.5;
      const trackOffset = (distanceRef.current % 30);
      for (let tx = -trackOffset; tx < GAME_CANVAS_WIDTH; tx += 30) {
        ctx.beginPath();
        ctx.moveTo(tx, GAME_GROUND_Y + 4);
        ctx.lineTo(tx + 12, GAME_GROUND_Y + 4);
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

        speedRef.current = getGameSpeed(currentPoints, physics);

        // Milestone celebration every 100 points
        const currentHundred = Math.floor(currentPoints / 100);
        if (currentHundred > lastMilestoneRef.current && currentHundred > 0) {
          lastMilestoneRef.current = currentHundred;
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

        // --- Player Physics Update with Firm Ground Clamping ---
        if (!p.isGrounded) {
          // Mid-air ducking gives responsive fast-fall
          const currentGravity = p.isDucking ? physics.gravity * 1.5 : physics.gravity;
          p.vy += currentGravity * frameScale;
          p.y += p.vy * frameScale;

          // Landing detection
          if (p.y >= GAME_GROUND_Y) {
            p.y = GAME_GROUND_Y;
            p.vy = 0;
            p.isGrounded = true;

            // Landing dust
            for (let i = 0; i < 4; i++) {
              particlesRef.current.push({
                x: p.x + 8 + (Math.random() * 8 - 4),
                y: GAME_GROUND_Y,
                vx: -(Math.random() * 2 + 1),
                vy: -(Math.random() * 1.5),
                alpha: 0.6,
                size: Math.random() * 3 + 1,
                color: "#94A3B8",
              });
            }
          }
        } else {
          // Absolute guarantee: running player feet stay pinned to GAME_GROUND_Y
          p.y = GAME_GROUND_Y;
          p.vy = 0;
        }

        // Dust while running on ground
        if (p.isGrounded && Math.random() < 1 - Math.pow(0.75, frameScale)) {
          particlesRef.current.push({
            x: p.x + (p.isDucking ? -5 : 4),
            y: GAME_GROUND_Y - 2,
            vx: -(speed * 0.4 + Math.random() * 1.5),
            vy: -(Math.random() * 1.2),
            alpha: 0.5,
            size: Math.random() * 2.5 + 1.5,
            color: "#CBD5E1",
          });
        }

        // --- Obstacle Generation: Ground Hurdles, Study Books & Flying Birds ---
        if (distanceRef.current >= nextSpawnDistanceRef.current) {
          let obsType: ObstacleType = "ground_hurdle";
          let obsW = 24;
          let obsH = 38;
          let obsY = GAME_GROUND_Y - obsH;

          // For the first 30 points: ground obstacles only for onboarding
          // At score >= 30: fair mix of ground obstacles (55%) and flying birds (45%)
          if (currentPoints < 30) {
            const isHurdle = Math.random() > 0.5;
            obsType = isHurdle ? "ground_hurdle" : "ground_books";
            obsW = isHurdle ? 24 : 32;
            obsH = isHurdle ? 38 : 42;
            obsY = GAME_GROUND_Y - obsH;
          } else {
            const rand = Math.random();
            if (rand < 0.35) {
              // Ground Hurdle
              obsType = "ground_hurdle";
              obsW = 24;
              obsH = 38;
              obsY = GAME_GROUND_Y - obsH;
            } else if (rand < 0.55) {
              // Stack of Study Books
              obsType = "ground_books";
              obsW = 32;
              obsH = 42;
              obsY = GAME_GROUND_Y - obsH;
            } else if (rand < 0.75) {
              // Bird Mid-Flight: flies at chest/head level -> Player MUST DUCK!
              obsType = "bird_mid";
              obsW = 36;
              obsH = 22;
              obsY = GAME_GROUND_Y - 58;
            } else if (rand < 0.90) {
              // Bird Low-Flight: flies low near ground -> Player MUST JUMP!
              obsType = "bird_low";
              obsW = 36;
              obsH = 22;
              obsY = GAME_GROUND_Y - 26;
            } else {
              // Bird High-Flight: flies high overhead -> Player runs underneath (Jumping hits!)
              obsType = "bird_high";
              obsW = 36;
              obsH = 22;
              obsY = GAME_GROUND_Y - 76;
            }
          }

          obstaclesRef.current.push({
            x: GAME_CANVAS_WIDTH + 20,
            y: obsY,
            width: obsW,
            height: obsH,
            type: obsType,
          });

          // Dynamic obstacle gap scales with speed for fair reflex windows
          const minGap = Math.max(physics.minObstacleGap, speed * 58);
          const randomExtra = 130 + Math.random() * 140;
          nextSpawnDistanceRef.current = distanceRef.current + minGap + randomExtra;
        }

        // Move obstacles and check fair multi-box collisions
        for (let i = obstaclesRef.current.length - 1; i >= 0; i--) {
          const obs = obstaclesRef.current[i];
          obs.x -= speed * frameScale;

          // Remove offscreen obstacles
          if (obs.x + obs.width < -30) {
            obstaclesRef.current.splice(i, 1);
            continue;
          }

          // Accurate Hitboxes:
          // Standing: width 18, height 50, y from (p.y - 50) to p.y
          // Ducking: width 32, height 22, y from (p.y - 22) to p.y (crouched low to slide under mid-birds)
          const playerBox = p.isDucking
            ? { x: p.x - 2, y: p.y - 22, w: 32, h: 22 }
            : { x: p.x + 3, y: p.y - 50, w: 18, h: 50 };

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

      // 5. Draw Obstacles: Hurdles, Books & Flying Birds
      for (const obs of obstaclesRef.current) {
        if (obs.type === "ground_hurdle") {
          // Minimalist Track Hurdle
          ctx.fillStyle = "#0F172A";
          ctx.beginPath();
          ctx.rect(obs.x, obs.y, obs.width, 7);
          ctx.fill();
          ctx.fillRect(obs.x + 2, obs.y + 7, 3, obs.height - 7);
          ctx.fillRect(obs.x + obs.width - 5, obs.y + 7, 3, obs.height - 7);
          ctx.fillRect(obs.x, obs.y + obs.height - 2, 7, 2);
          ctx.fillRect(obs.x + obs.width - 7, obs.y + obs.height - 2, 7, 2);
        } else if (obs.type === "ground_books") {
          // Stack of 3 Study Books
          const bookHeight = obs.height / 3;
          for (let b = 0; b < 3; b++) {
            const by = obs.y + b * bookHeight;
            const bw = obs.width - (b === 1 ? 4 : 0);
            const bx = obs.x + (b === 1 ? 2 : 0);
            ctx.fillStyle = "#0F172A";
            ctx.fillRect(bx, by, bw, bookHeight - 2);
            ctx.fillStyle = "#FFFFFF";
            ctx.fillRect(bx + 2, by + 2, 2, bookHeight - 6);
          }
        } else if (obs.type === "bird_low" || obs.type === "bird_mid" || obs.type === "bird_high") {
          // Flying Bird with 2-frame flapping wings
          drawBird(ctx, obs, currentTime);
        }
      }

      // 6. Draw Animated Stickman firmly aligned to ground
      drawStickman(ctx, p, currentTime, state, distanceRef.current);

      // 7. Render In-Game HUD (Speed at top-left, Score & Best at top-right)
      ctx.fillStyle = "#0F172A";
      ctx.font = "bold 15px monospace";
      ctx.textAlign = "right";
      const scoreStr = String(scoreRef.current).padStart(5, "0");
      const highStr = String(highScoreRef.current).padStart(5, "0");
      ctx.fillText(`SCORE: ${scoreStr}`, GAME_CANVAS_WIDTH - 25, 32);

      ctx.fillStyle = "#64748B";
      ctx.font = "12px monospace";
      ctx.fillText(`BEST:  ${highStr}`, GAME_CANVAS_WIDTH - 25, 50);

      // Speed indicator
      ctx.textAlign = "left";
      ctx.fillStyle = "#64748B";
      ctx.font = "11px monospace";
      ctx.fillText(`SPEED: ${(speedRef.current).toFixed(1)}x`, 25, 32);

      // 8. Overlays for PAUSED and GAMEOVER
      if (state === "PAUSED") {
        ctx.fillStyle = "rgba(15, 23, 42, 0.6)";
        ctx.fillRect(0, 0, GAME_CANVAS_WIDTH, GAME_CANVAS_HEIGHT);

        ctx.fillStyle = "#FFFFFF";
        ctx.font = "bold 24px system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("GAME PAUSED", GAME_CANVAS_WIDTH / 2, GAME_CANVAS_HEIGHT / 2 - 10);

        ctx.font = "13px monospace";
        ctx.fillStyle = "#CBD5E1";
        ctx.fillText("Press P or Tap anywhere to Resume", GAME_CANVAS_WIDTH / 2, GAME_CANVAS_HEIGHT / 2 + 20);
      } else if (state === "GAMEOVER") {
        ctx.fillStyle = "rgba(15, 23, 42, 0.82)";
        ctx.fillRect(0, 0, GAME_CANVAS_WIDTH, GAME_CANVAS_HEIGHT);

        ctx.fillStyle = "#EF4444";
        ctx.font = "bold 28px system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("GAME OVER", GAME_CANVAS_WIDTH / 2, GAME_CANVAS_HEIGHT / 2 - 40);

        ctx.fillStyle = "#FFFFFF";
        ctx.font = "bold 16px monospace";
        ctx.fillText(`SCORE: ${scoreRef.current}   |   BEST: ${highScoreRef.current}`, GAME_CANVAS_WIDTH / 2, GAME_CANVAS_HEIGHT / 2 - 5);

        if (scoreRef.current >= highScoreRef.current && scoreRef.current > 0) {
          ctx.fillStyle = "#F59E0B";
          ctx.font = "bold 13px monospace";
          ctx.fillText("★ NEW HIGH SCORE! ★", GAME_CANVAS_WIDTH / 2, GAME_CANVAS_HEIGHT / 2 + 20);
        }

        ctx.fillStyle = "#E2E8F0";
        ctx.font = "13px monospace";
        ctx.fillText("Press SPACE, R, or Tap to Restart", GAME_CANVAS_WIDTH / 2, GAME_CANVAS_HEIGHT / 2 + 46);
      }
    };

    lastTimeRef.current = performance.now();
    animFrameIdRef.current = requestAnimationFrame(render);

    return () => {
      window.removeEventListener("resize", configureCanvas);
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
    };
  }, [playSound, physics]);

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
              Minimalist offline stickman runner • Clear exam hurdles & duck under flying birds
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
          className="w-full aspect-[840/320] block cursor-pointer transition-colors duration-500"
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
            <span>Jump over books & hurdles • Duck under flying birds • P to pause</span>
          </div>
          <span className="shrink-0 flex items-center gap-1 font-semibold text-[var(--brand-primary)]">
            <Trophy className="w-3.5 h-3.5 text-amber-500" />
            <span>100pt Milestones</span>
          </span>
        </div>
      </div>
    </div>
  );
}
