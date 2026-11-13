"use client";

import * as THREE from "three";
import React, { useRef, useEffect, useState, useCallback } from "react";

/* ----------------------------- utilities ----------------------------- */

/**
 * Mobile detection for responsive tunnel adjustments
 */
function useIsMobile(breakpoint = 768) {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mq = window.matchMedia(`(max-width: ${breakpoint}px)`);
    setIsMobile(mq.matches);
    const onChange = (e: MediaQueryListEvent) => setIsMobile(e.matches);

    try {
      mq.addEventListener("change", onChange);
      return () => mq.removeEventListener("change", onChange);
    } catch {
      mq.addListener(onChange as any);
      return () => mq.removeListener(onChange as any);
    }
  }, [breakpoint]);

  return isMobile;
}

/* ----------------------------- shared Three.js shader ----------------------------- */

const vertexShader = `void main(){ gl_Position = vec4(position, 1.0); }`;

const fragmentShader = `
uniform float iTime;
uniform vec3 iResolution;
uniform float uPointSize;

#define TAU 6.2831853071795865
#define TUNNEL_LAYERS 48
#define RING_POINTS 96
#define POINT_COLOR_A vec3(1.0)
#define POINT_COLOR_B vec3(0.7)
#define SPEED 0.7

float sq(float x){ return x*x; }

vec2 AngRep(vec2 uv, float angle){
  vec2 polar = vec2(atan(uv.y, uv.x), length(uv));
  polar.x = mod(polar.x + angle/2.0, angle) - angle/2.0;
  return polar.y * vec2(cos(polar.x), sin(polar.x));
}

float sdCircle(vec2 uv, float r){ return length(uv) - r; }

vec3 MixShape(float sd, vec3 fill, vec3 target){
  float blend = smoothstep(0.0, 1.0/iResolution.y, sd);
  return mix(fill, target, blend);
}

vec2 TunnelPath(float x){
  vec2 offs = vec2(
    0.2 * sin(TAU * x * 0.5) + 0.4 * sin(TAU * x * 0.2 + 0.3),
    0.3 * cos(TAU * x * 0.3) + 0.2 * cos(TAU * x * 0.1)
  );
  offs *= smoothstep(1.0, 4.0, x);
  return offs;
}

void main(){
  vec2 res = iResolution.xy / iResolution.y;
  vec2 uv = gl_FragCoord.xy / iResolution.y - res/2.0;
  vec3 color = vec3(0.0);
  float repAngle = TAU / float(RING_POINTS);
  float pointSize = uPointSize / (2.0 * iResolution.y);
  float camZ = iTime * SPEED;
  vec2 camOffs = TunnelPath(camZ);

  for(int i = 1; i <= TUNNEL_LAYERS; i++){
    float pz = 1.0 - (float(i) / float(TUNNEL_LAYERS));
    pz -= mod(camZ, 4.0 / float(TUNNEL_LAYERS));
    vec2 offs = TunnelPath(camZ + pz) - camOffs;
    float ringRad = 0.15 * (1.0 / sq(pz * 0.8 + 0.4));
    if(abs(length(uv + offs) - ringRad) < pointSize * 1.5){
      vec2 aruv = AngRep(uv + offs, repAngle);
      float pdist = sdCircle(aruv - vec2(ringRad, 0), pointSize);
      vec3 ptColor = (mod(float(i/2), 2.0) == 0.0) ? POINT_COLOR_A : POINT_COLOR_B;
      float shade = (1.0 - pz);
      color = MixShape(pdist, ptColor * shade, color);
    }
  }

  gl_FragColor = vec4(color, 1.0);
}
`;

type ThreeContext = {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.OrthographicCamera;
  material: THREE.ShaderMaterial;
  mesh: THREE.Mesh;
  geometry: THREE.PlaneGeometry;
};

function createThreeForCanvas(
  canvas: HTMLCanvasElement,
  width: number,
  height: number,
  pointSize: number = 3.0
): ThreeContext {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  renderer.setPixelRatio(dpr);
  renderer.setSize(width, height);

  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  const material = new THREE.ShaderMaterial({
    uniforms: {
      iTime: { value: 0 },
      iResolution: { value: new THREE.Vector3(width, height, 1) },
      uPointSize: { value: pointSize },
    },
    vertexShader,
    fragmentShader,
  });

  const geometry = new THREE.PlaneGeometry(2, 2);
  const mesh = new THREE.Mesh(geometry, material);
  scene.add(mesh);

  return { renderer, scene, camera, material, mesh, geometry };
}

function disposeThree(ctx: ThreeContext) {
  try {
    ctx.scene.remove(ctx.mesh);
    ctx.mesh.geometry.dispose();
    ctx.material.dispose();
    ctx.renderer.dispose();
  } catch (e) {
    // ignore disposal errors
  }
}

export interface SpaceTunnelBackgroundProps {
  className?: string;
  opacity?: number;
  speed?: number;
  rings?: number;
  pointSize?: number;
}

/**
 * 3D Three.js Dot Space Tunnel Background Animation
 * Pure high-contrast monochrome space tunnel with 96 depth layers of white dots.
 */
export function SpaceTunnelBackground({
  className = "",
  opacity = 0.85,
  pointSize = 3.0,
}: SpaceTunnelBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const ctxRef = useRef<ThreeContext | null>(null);
  const lastTimeRef = useRef<number>(0);
  const animRef = useRef<number | null>(null);
  const pausedRef = useRef<boolean>(false);
  const rafResizeRef = useRef<boolean>(false);

  const animate = useCallback((time: number) => {
    if (!ctxRef.current) return;
    animRef.current = requestAnimationFrame(animate);
    if (pausedRef.current) {
      lastTimeRef.current = time;
      return;
    }
    time *= 0.001;
    const delta = time - (lastTimeRef.current || time);
    lastTimeRef.current = time;
    ctxRef.current.material.uniforms.iTime.value += delta * 0.5;
    ctxRef.current.renderer.render(ctxRef.current.scene, ctxRef.current.camera);
  }, []);

  useEffect(() => {
    if (ctxRef.current) {
      ctxRef.current.material.uniforms.uPointSize.value = pointSize;
    }
  }, [pointSize]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || typeof window === "undefined") return;

    const width = window.innerWidth;
    const height = window.innerHeight;
    try {
      const ctx = createThreeForCanvas(canvas, width, height, pointSize);
      ctxRef.current = ctx;
    } catch (e) {
      console.warn("SpaceTunnel WebGL initialization skipped:", e);
      return;
    }

    const handleResize = () => {
      if (!ctxRef.current) return;
      if (rafResizeRef.current) return;
      rafResizeRef.current = true;
      requestAnimationFrame(() => {
        rafResizeRef.current = false;
        const w = window.innerWidth;
        const h = window.innerHeight;
        ctxRef.current!.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        ctxRef.current!.renderer.setSize(w, h);
        (ctxRef.current!.material.uniforms.iResolution.value as THREE.Vector3).set(w, h, 1);
      });
    };
    window.addEventListener("resize", handleResize);

    const handleVisibility = () => {
      pausedRef.current = !!document.hidden;
    };
    document.addEventListener("visibilitychange", handleVisibility);
    handleVisibility();

    animRef.current = requestAnimationFrame(animate);

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
      window.removeEventListener("resize", handleResize);
      document.removeEventListener("visibilitychange", handleVisibility);
      if (ctxRef.current) {
        disposeThree(ctxRef.current);
        ctxRef.current = null;
      }
    };
  }, [animate, pointSize]);

  return (
    <div
      className={`fixed inset-0 w-full h-full pointer-events-none z-0 overflow-hidden ${className}`}
      style={{ opacity }}
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full block"
        id="tunnel-canvas"
      />
      {/* Soft radial overlay so hero text stays readable */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(10,10,15,0.3) 0%, rgba(10,10,15,0.7) 70%, rgba(10,10,15,0.95) 100%)",
        }}
      />
    </div>
  );
}

export default SpaceTunnelBackground;
