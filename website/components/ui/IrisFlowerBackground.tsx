"use client"

import React, { useEffect, useRef, useState, useCallback } from "react"
import Link from "next/link"
import { MessageSquare, Sparkles, Settings as SettingsIcon, ArrowRight, X } from "lucide-react"

export interface IrisFlowerBackgroundProps {
  className?: string
  opacity?: number
  speedSeconds?: number
  tiltDegrees?: number
  glowIntensity?: number
  backgroundGlow?: boolean
  scale?: number
  wireframe?: boolean
  interactivePetals?: boolean
}

/**
 * Ethereal Bioluminescent 3D Iris Flower Background
 * Procedurally generated 3D botanical geometry rendered in real-time with WebGL:
 * - 3 Cascading ruffled Falls petals (0°, 120°, 240°)
 * - 3 Upright arching Standards petals (60°, 180°, 300°)
 * - 3 Central feathered Style Crests
 * - Luminous Golden Beards
 * - Curved organic Stem & Side Bud
 * Features double-sided translucent Fresnel shading, glowing radiating veins,
 * and continuous smooth 360° self-rotation around its vertical axis.
 */
const PETAL_ITEMS = [
  {
    id: "chat",
    baseAngle: (60 * Math.PI) / 180,
    shortLabel: "01 // CHAT",
    numLabel: "01",
    sysTag: "SYS.01 // NEURAL",
    petalLabel: "SYS.01 // NEURAL CORE",
    title: "Local AI Chat",
    desc: "Private neural assistant for offline reasoning, system instructions, and memory indexing.",
    action: "INITIALIZE CHAT",
    href: "/dashboard/chat",
    icon: MessageSquare,
    color: "#06b6d4",
    glowRgba: "rgba(6, 182, 212, 0.45)",
    bgBadge: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
    borderColor: "border-cyan-500/50 hover:border-cyan-400",
    modelPos: [0.294, 1.12, 0.170] as [number, number, number],
  },
  {
    id: "themes",
    baseAngle: (180 * Math.PI) / 180,
    shortLabel: "02 // THEMES",
    numLabel: "02",
    sysTag: "SYS.02 // VISUAL",
    petalLabel: "SYS.02 // VISUAL THEMES",
    title: "Theme Customizer",
    desc: "6 dynamic desktop overlay presentations: Cyber Terminal, Liquid Blob, Equalizer, and more.",
    action: "CUSTOMIZE THEMES",
    href: "/dashboard/settings",
    icon: Sparkles,
    color: "#a855f7",
    glowRgba: "rgba(168, 85, 247, 0.45)",
    bgBadge: "bg-purple-500/15 text-purple-300 border-purple-500/30",
    borderColor: "border-purple-500/50 hover:border-purple-400",
    modelPos: [0.000, 1.12, -0.340] as [number, number, number],
  },
  {
    id: "skills",
    baseAngle: (300 * Math.PI) / 180,
    shortLabel: "03 // SKILLS",
    numLabel: "03",
    sysTag: "SYS.03 // RULES",
    petalLabel: "SYS.03 // SYSTEM RULES",
    title: "Skills & System Rules",
    desc: "Autonomous system automation, VS Code runner, permissions, and private wake word parameters.",
    action: "MANAGE SKILLS",
    href: "/dashboard/settings",
    icon: SettingsIcon,
    color: "#10b981",
    glowRgba: "rgba(16, 185, 129, 0.45)",
    bgBadge: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    borderColor: "border-emerald-500/50 hover:border-emerald-400",
    modelPos: [-0.294, 1.12, 0.170] as [number, number, number],
  },
]

function project3DPoint(
  pos: [number, number, number],
  mv: Float32Array,
  proj: Float32Array,
  w: number,
  h: number
): { x: number; y: number; z: number; facing: boolean } {
  const vx = mv[0] * pos[0] + mv[4] * pos[1] + mv[8] * pos[2] + mv[12]
  const vy = mv[1] * pos[0] + mv[5] * pos[1] + mv[9] * pos[2] + mv[13]
  const vz = mv[2] * pos[0] + mv[6] * pos[1] + mv[10] * pos[2] + mv[14]
  const vw = mv[3] * pos[0] + mv[7] * pos[1] + mv[11] * pos[2] + mv[15]

  const cx = proj[0] * vx + proj[4] * vy + proj[8] * vz + proj[12] * vw
  const cy = proj[1] * vx + proj[5] * vy + proj[9] * vz + proj[13] * vw
  const cz = proj[2] * vx + proj[6] * vy + proj[10] * vz + proj[14] * vw
  const cw = proj[3] * vx + proj[7] * vy + proj[11] * vz + proj[15] * vw

  if (cw <= 0.0001) return { x: -9999, y: -9999, z: 9999, facing: false }

  const ndcX = cx / cw
  const ndcY = cy / cw

  const sx = (ndcX * 0.5 + 0.5) * w
  const sy = (-ndcY * 0.5 + 0.5) * h

  return {
    x: sx,
    y: sy,
    z: cz / cw,
    facing: vz < 0,
  }
}

export function IrisFlowerBackground({
  className = "",
  opacity = 0.72,
  speedSeconds = 70,
  tiltDegrees = -20,
  glowIntensity = 3,
  backgroundGlow = true,
  scale = 0.80,
  wireframe = false,
  interactivePetals = false,
}: IrisFlowerBackgroundProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  const [liveWireframe, setLiveWireframe] = useState(wireframe)
  const [liveGlow, setLiveGlow] = useState(glowIntensity)

  const speedSecondsRef = useRef(speedSeconds)
  speedSecondsRef.current = speedSeconds

  const tiltDegreesRef = useRef(tiltDegrees)
  tiltDegreesRef.current = tiltDegrees

  const scaleRef = useRef(scale)
  scaleRef.current = scale

  const interactivePetalsRef = useRef(interactivePetals)
  interactivePetalsRef.current = interactivePetals

  const liveWireframeRef = useRef(liveWireframe)
  liveWireframeRef.current = liveWireframe

  const liveGlowRef = useRef(liveGlow)
  liveGlowRef.current = liveGlow

  useEffect(() => {
    setLiveWireframe(wireframe)
  }, [wireframe])

  useEffect(() => {
    setLiveGlow(glowIntensity)
  }, [glowIntensity])

  useEffect(() => {
    const handleWireframe = () => setLiveWireframe((w) => !w)
    const handleGlow = (e: any) => setLiveGlow(Number(e.detail?.glow ?? 8))
    window.addEventListener("iris-wireframe-toggle", handleWireframe)
    window.addEventListener("iris-glow-change", handleGlow)
    return () => {
      window.removeEventListener("iris-wireframe-toggle", handleWireframe)
      window.removeEventListener("iris-glow-change", handleGlow)
    }
  }, [])

  const [activePetals, setActivePetals] = useState<Record<string, boolean>>({
    chat: false,
    themes: false,
    skills: false,
  })
  const activePetalsRef = useRef(activePetals)
  activePetalsRef.current = activePetals

  const currentCoordsRef = useRef<Array<{ x: number; y: number; facing: boolean }>>([
    { x: -999, y: -999, facing: true },
    { x: -999, y: -999, facing: true },
    { x: -999, y: -999, facing: true },
  ])

  const [openCoords, setOpenCoords] = useState<Array<{ x: number; y: number }>>([
    { x: 0, y: 0 },
    { x: 0, y: 0 },
    { x: 0, y: 0 },
  ])

  const targetAngleYRef = useRef<number | null>(null)
  const [hoveredPetalId, setHoveredPetalId] = useState<string | null>(null)

  const dot0Ref = useRef<HTMLDivElement | null>(null)
  const dot1Ref = useRef<HTMLDivElement | null>(null)
  const dot2Ref = useRef<HTMLDivElement | null>(null)
  const dotRefs = [dot0Ref, dot1Ref, dot2Ref]

  const togglePetal = (id: string) => {
    setActivePetals((prev) => {
      const isCurrentlyOpen = Boolean(prev[id])

      if (isCurrentlyOpen) {
        // Retract this petal and resume continuous 360° rotation
        targetAngleYRef.current = null
        const updated = { ...prev, [id]: false }
        const allOpen = Object.values(updated).every(Boolean)
        const anyOpen = Object.values(updated).some(Boolean)
        if (typeof window !== "undefined") {
          window.dispatchEvent(new CustomEvent("iris-petals-state", { detail: { allOpen, anyOpen } }))
        }
        return updated
      } else {
        // Select this petal:
        // "if it is rotating and i select one it will come to center and the line will come and to te box and the box apper"
        const item = PETAL_ITEMS.find((p) => p.id === id)
        if (item) {
          // targetAngleY brings this petal right to the front-center (angleY + baseAngle = 0 => angleY = -baseAngle)
          targetAngleYRef.current = -item.baseAngle
        }

        const coords = currentCoordsRef.current.map((c) => ({ x: c.x, y: c.y }))
        setOpenCoords(coords)

        // Open this petal (and close other individual petals if not all expanded)
        const updated = { chat: false, themes: false, skills: false, [id]: true }
        const allOpen = false
        const anyOpen = true
        if (typeof window !== "undefined") {
          window.dispatchEvent(new CustomEvent("iris-petals-state", { detail: { allOpen, anyOpen } }))
        }
        return updated
      }
    })
  }

  const toggleAll = useCallback(() => {
    setActivePetals((prev) => {
      const anyOpen = Object.values(prev).some(Boolean)
      const nextVal = !anyOpen
      targetAngleYRef.current = null // in expand-all, keep current rotation or hold

      const updated = { chat: nextVal, themes: nextVal, skills: nextVal }
      const coords = currentCoordsRef.current.map((c) => ({ x: c.x, y: c.y }))
      setOpenCoords(coords)
      if (typeof window !== "undefined") {
        window.dispatchEvent(
          new CustomEvent("iris-petals-state", {
            detail: { allOpen: nextVal, anyOpen: nextVal },
          })
        )
      }
      return updated
    })
  }, [])

  useEffect(() => {
    if (!interactivePetals) return
    const handleToggleEvent = () => toggleAll()
    window.addEventListener("iris-toggle-petals", handleToggleEvent)
    return () => window.removeEventListener("iris-toggle-petals", handleToggleEvent)
  }, [interactivePetals, toggleAll])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const gl = canvas.getContext("webgl", { antialias: true, alpha: true })
    if (!gl) return

    // Vertex Shader
    const vsSource = `
      attribute vec3 aPosition;
      attribute vec3 aNormal;
      attribute vec2 aUv;
      attribute float aPartType; // 0=Fall, 1=Standard, 2=Crest, 3=Stem, 4=Beard

      uniform mat4 uProjection;
      uniform mat4 uModelView;
      uniform mat3 uNormalMatrix;
      uniform float uTime;

      varying vec3 vNormal;
      varying vec3 vViewPosition;
      varying vec2 vUv;
      varying float vPartType;

      void main() {
        vec3 pos = aPosition;

        // Multi-frequency organic breathing wave
        float breathe1 = sin(uTime * 1.3 + pos.y * 1.6) * 0.018;
        float breathe2 = cos(uTime * 0.8 + pos.x * 2.0) * 0.008;
        pos.xz += aNormal.xz * (breathe1 + breathe2);

        vec4 mvPos = uModelView * vec4(pos, 1.0);
        gl_Position = uProjection * mvPos;

        vViewPosition = -mvPos.xyz;
        vNormal = normalize(uNormalMatrix * aNormal);
        vUv = aUv;
        vPartType = aPartType;
      }
    `

    // Fragment Shader: Realistic Radiating Vein Networks, Subsurface Sheen, Velvety Texture
    const fsSource = `
      precision mediump float;

      varying vec3 vNormal;
      varying vec3 vViewPosition;
      varying vec2 vUv;
      varying float vPartType;

      uniform float uTime;
      uniform float uGlowIntensity;

      void main() {
        vec3 normal = normalize(vNormal);
        if (!gl_FrontFacing) normal = -normal;

        vec3 viewDir = normalize(vViewPosition);

        // Double-sided Fresnel rim luminescence
        float NdotV = abs(dot(normal, viewDir));
        float fresnel = pow(1.0 - NdotV, 2.3);

        // Core botanical palette
        vec3 pureWhite    = vec3(0.96, 0.98, 1.0);
        vec3 icyCyan      = vec3(0.42, 0.82, 1.0);
        vec3 deepViolet   = vec3(0.68, 0.44, 0.98);
        vec3 goldenBeard  = vec3(1.0, 0.78, 0.25);
        vec3 stemEmerald  = vec3(0.32, 0.54, 0.42);

        // Velvety specular highlight (anisotropic micro-fiber sheen)
        vec3 lightDir = normalize(vec3(0.2, 0.9, 0.5));
        vec3 halfVec = normalize(lightDir + viewDir);
        float spec = pow(max(0.0, abs(dot(normal, halfVec))), 28.0) * 0.5;

        vec3 finalColor = pureWhite;
        float alpha = 0.88;

        if (vPartType < 0.5) {
          // --- FALL PETAL: Fan-radiating veining, ruffled margin translucency ---
          vec2 origin = vec2(0.5, 0.0);
          vec2 delta = vUv - origin;
          float angle = atan(delta.x, max(delta.y, 0.001));
          float dist = length(delta);

          // 1. Primary radiating botanical veins (26 fan spokes)
          float primaryVeins = sin(angle * 26.0) * 0.5 + 0.5;
          primaryVeins = pow(primaryVeins, 4.2);

          // 2. Secondary delicate micro-veins (62 fine spokes)
          float microVeins = sin(angle * 62.0 + dist * 14.0) * 0.5 + 0.5;
          microVeins = pow(microVeins, 3.2) * 0.45;

          // 3. Central spine midrib definition
          float midrib = 1.0 - smoothstep(0.0, 0.10, abs(vUv.x - 0.5));

          // 4. Petal edge thinness
          float edgeThinness = smoothstep(0.15, 0.85, abs(vUv.x - 0.5) * 2.0);

          finalColor = mix(deepViolet * 0.35, pureWhite, vUv.y * 0.75 + 0.25);
          finalColor += icyCyan * (fresnel * (uGlowIntensity * 0.13) + (primaryVeins + microVeins) * 0.35);
          finalColor += pureWhite * (midrib * 0.38 + spec * 0.6);
          alpha = mix(0.58, 0.94, fresnel + midrib * 0.35 + edgeThinness * 0.15);

        } else if (vPartType < 1.5) {
          // --- STANDARD PETAL: Upright gossamer domed crown with silky curved neat rim ---
          float vCenter = abs(vUv.x - 0.5) * 2.0;
          float verticalVeins = sin(vUv.x * 38.0) * 0.5 + 0.5;
          verticalVeins = pow(verticalVeins, 3.5) * 0.35;
          float crownFrills = sin(vUv.x * 24.0 + vUv.y * 10.0) * 0.5 + 0.5;

          finalColor = mix(icyCyan * 0.28, pureWhite, 0.72);
          finalColor += icyCyan * (fresnel * (uGlowIntensity * 0.15) + crownFrills * 0.18 + verticalVeins * 0.22);
          finalColor += pureWhite * spec * 0.5;

          // Clear, neat curved rim highlight at the upper petal ending
          float apexGlow = smoothstep(0.82, 1.0, vUv.y) * 0.38;
          finalColor += pureWhite * apexGlow;

          alpha = mix(0.55, 0.92, fresnel * 1.35 + vCenter * 0.18);

        } else if (vPartType < 2.5) {
          // --- STYLE CRESTS: Serrated central wingtips ---
          float serration = sin(vUv.y * 45.0) * 0.1;
          finalColor = mix(deepViolet * 0.85, pureWhite, 0.65);
          finalColor += icyCyan * (fresnel * (uGlowIntensity * 0.08) + serration);
          finalColor += pureWhite * spec * 0.5;
          alpha = 0.88;

        } else if (vPartType < 3.5) {
          // --- STEM ---
          float stemFresnel = pow(1.0 - NdotV, 2.8);
          finalColor = mix(stemEmerald * 0.6, icyCyan * 0.6, stemFresnel);
          finalColor += pureWhite * (spec * 0.4 + 0.2);
          alpha = 0.96;

        } else if (vPartType < 4.5) {
          // --- GOLDEN BEARD: Plush textured cilia hairs ---
          float hairTexture = sin(vUv.x * 30.0) * sin(vUv.y * 40.0) * 0.25 + 0.75;
          finalColor = goldenBeard * (1.35 * hairTexture) + vec3(0.25, 0.15, 0.0);
          finalColor += pureWhite * spec * 0.7;
          alpha = 0.98;

        } else {
          // --- BOTANICAL ENSIFORM IRIS LEAF (vPartType = 5.0) ---
          // 1. Primary longitudinal parallel veins (monocot anatomy)
          float leafVeins = sin(vUv.x * 38.0) * 0.5 + 0.5;
          leafVeins = pow(leafVeins, 4.0) * 0.38;

          // 2. Secondary delicate parallel micro-veins
          float leafMicroVeins = sin(vUv.x * 84.0) * 0.5 + 0.5;
          leafMicroVeins = pow(leafMicroVeins, 3.2) * 0.24;

          // 3. Crisp central midrib keel line
          float leafMidrib = 1.0 - smoothstep(0.0, 0.075, abs(vUv.x - 0.5));

          // 4. Razor-thin glowing translucent blade margins
          float edgeGlow = smoothstep(0.32, 0.50, abs(vUv.x - 0.5));

          // 5. Fresnel rim luminescence
          float leafFresnel = pow(1.0 - NdotV, 2.4);

          // Ethereal foliage coloring matching the reference photo
          finalColor = mix(stemEmerald * 0.65, icyCyan * 0.85, vUv.y * 0.45 + leafFresnel * 0.5);
          finalColor += pureWhite * (leafMidrib * 0.52 + (leafVeins + leafMicroVeins) * 0.45 + spec * 0.5);
          finalColor += icyCyan * (edgeGlow * 0.55 + leafFresnel * (uGlowIntensity * 0.12));
          alpha = mix(0.75, 0.96, leafFresnel * 0.7 + leafMidrib * 0.3 + edgeGlow * 0.25);
        }

        gl_FragColor = vec4(finalColor, alpha);
      }
    `

    function createShader(glContext: WebGLRenderingContext, type: number, src: string) {
      const s = glContext.createShader(type)
      if (!s) return null
      glContext.shaderSource(s, src)
      glContext.compileShader(s)
      if (!glContext.getShaderParameter(s, glContext.COMPILE_STATUS)) {
        glContext.deleteShader(s)
        return null
      }
      return s
    }

    const vs = createShader(gl, gl.VERTEX_SHADER, vsSource)
    const fs = createShader(gl, gl.FRAGMENT_SHADER, fsSource)
    if (!vs || !fs) return

    const program = gl.createProgram()
    if (!program) return
    gl.attachShader(program, vs)
    gl.attachShader(program, fs)
    gl.linkProgram(program)
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return

    const locs = {
      aPosition: gl.getAttribLocation(program, "aPosition"),
      aNormal: gl.getAttribLocation(program, "aNormal"),
      aUv: gl.getAttribLocation(program, "aUv"),
      aPartType: gl.getAttribLocation(program, "aPartType"),
      uProjection: gl.getUniformLocation(program, "uProjection"),
      uModelView: gl.getUniformLocation(program, "uModelView"),
      uNormalMatrix: gl.getUniformLocation(program, "uNormalMatrix"),
      uTime: gl.getUniformLocation(program, "uTime"),
      uGlowIntensity: gl.getUniformLocation(program, "uGlowIntensity"),
    }

    // =========================================================================
    // 3D GEOMETRY GENERATION
    // =========================================================================
    const positions: number[] = []
    const normals: number[] = []
    const uvs: number[] = []
    const partTypes: number[] = []
    const indices: number[] = []
    const lineIndices: number[] = []
    let vertexOffset = 0

    function addQuad(
      p0: number[], p1: number[], p2: number[], p3: number[],
      n0: number[], n1: number[], n2: number[], n3: number[],
      uv0: number[], uv1: number[], uv2: number[], uv3: number[],
      partType: number
    ) {
      positions.push(...p0, ...p1, ...p2, ...p3)
      normals.push(...n0, ...n1, ...n2, ...n3)
      uvs.push(...uv0, ...uv1, ...uv2, ...uv3)
      partTypes.push(partType, partType, partType, partType)

      const i0 = vertexOffset
      const i1 = vertexOffset + 1
      const i2 = vertexOffset + 2
      const i3 = vertexOffset + 3

      indices.push(i0, i1, i2, i0, i2, i3)
      lineIndices.push(i0, i1, i1, i2, i2, i3, i3, i0, i0, i2)
      vertexOffset += 4
    }

    function rotateY(p: number[], angle: number) {
      const cosA = Math.cos(angle)
      const sinA = Math.sin(angle)
      return [p[0] * cosA + p[2] * sinA, p[1], -p[0] * sinA + p[2] * cosA]
    }

    // 1. Three Detailed Cascading Fall Petals with Voluptuous Curves (0°, 120°, 240°)
    const fallStepsU = 44
    const fallStepsV = 32
    for (let pIdx = 0; pIdx < 3; pIdx++) {
      const baseAngle = (pIdx * 120 * Math.PI) / 180
      const grid: number[][][] = []
      const normGrid: number[][][] = []
      const uvGrid: number[][][] = []

      for (let i = 0; i <= fallStepsU; i++) {
        const u = i / fallStepsU // 0 (claw) to 1 (ruffled drooping apron)
        grid[i] = []
        normGrid[i] = []
        uvGrid[i] = []

        // Deeper voluptuous downward cascading curve (~15% larger & grander)
        const r = 0.09 + Math.sin(Math.pow(u, 0.85) * Math.PI * 0.88) * 0.96 + u * 0.20
        const y = 0.06 + Math.sin(u * Math.PI * 0.65) * 0.32 - Math.pow(u, 1.95) * 1.18
        const widthMax = 0.58 * Math.sin(u * Math.PI * 0.92) * (1.0 - Math.pow(u - 0.72, 2.0) * 0.75)

        for (let j = 0; j <= fallStepsV; j++) {
          const v = j / fallStepsV
          const vCentered = (v - 0.5) * 2.0

          const x = vCentered * widthMax

          // Multi-harmonic realistic ruffles & curves:
          const edgeFactor = Math.pow(Math.abs(vCentered), 1.4)
          const primaryFold = Math.sin(u * 9.0 + vCentered * 3.5) * 0.065 * edgeFactor
          const ripple = Math.sin(u * 22.0 + vCentered * 7.0) * 0.04 * Math.pow(Math.abs(vCentered), 1.8) * (0.3 + u * 0.7)
          const microCrinkle = Math.sin(u * 50.0) * 0.015 * Math.pow(Math.abs(vCentered), 2.4)
          const pleat = Math.sin(vCentered * 16.0 * (0.6 + u * 0.8)) * 0.016 * u

          // 3D Petal Twist & Deep Parabolic Downward Drape
          const drape = -Math.pow(vCentered, 2.0) * 0.14 * Math.sin(u * Math.PI * 0.95)
          const twist = vCentered * Math.sin(u * Math.PI) * 0.065
          const tipReflex = Math.pow(Math.max(0.0, u - 0.80) / 0.20, 2.0) * 0.065 * (1.0 - Math.abs(vCentered) * 0.4)

          const totalDisplacement = primaryFold + ripple + microCrinkle + pleat + drape + twist + tipReflex

          const localP = [x, y + totalDisplacement, r]
          const worldP = rotateY(localP, baseAngle)

          const localN = [
            vCentered * 0.5 + Math.cos(vCentered * 16.0) * 0.1,
            Math.cos(u * Math.PI * 0.72) * 0.7,
            Math.sin(u * Math.PI * 0.72) * 0.7 + (1.0 - Math.abs(vCentered)) * 0.35,
          ]
          const worldN = rotateY(localN, baseAngle)

          grid[i][j] = worldP
          normGrid[i][j] = worldN
          uvGrid[i][j] = [v, u]
        }
      }

      for (let i = 0; i < fallStepsU; i++) {
        for (let j = 0; j < fallStepsV; j++) {
          addQuad(
            grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1],
            normGrid[i][j], normGrid[i + 1][j], normGrid[i + 1][j + 1], normGrid[i][j + 1],
            uvGrid[i][j], uvGrid[i + 1][j], uvGrid[i + 1][j + 1], uvGrid[i][j + 1],
            0.0
          )
        }
      }

      // Plush 3D Bearded Crest (3 staggered rows of fuzzy beard filaments)
      const beardSteps = 20
      for (let b = 0; b < beardSteps; b++) {
        const u0 = 0.06 + (b / beardSteps) * 0.44
        const u1 = 0.06 + ((b + 1) / beardSteps) * 0.44
        const midJ = Math.floor(fallStepsV / 2)

        const p0 = rotateY([-0.018, grid[Math.floor(u0 * fallStepsU)][midJ][1] + 0.024, grid[Math.floor(u0 * fallStepsU)][midJ][2]], baseAngle)
        const p1 = rotateY([-0.018, grid[Math.floor(u1 * fallStepsU)][midJ][1] + 0.024, grid[Math.floor(u1 * fallStepsU)][midJ][2]], baseAngle)
        const p2 = rotateY([ 0.018, grid[Math.floor(u1 * fallStepsU)][midJ][1] + 0.024, grid[Math.floor(u1 * fallStepsU)][midJ][2]], baseAngle)
        const p3 = rotateY([ 0.018, grid[Math.floor(u0 * fallStepsU)][midJ][1] + 0.024, grid[Math.floor(u0 * fallStepsU)][midJ][2]], baseAngle)

        const bn = rotateY([0, 1, 0], baseAngle)
        addQuad(p0, p1, p2, p3, bn, bn, bn, bn, [0, 0], [0, 1], [1, 1], [1, 0], 4.0)

        const tuftHeight = 0.018 + Math.sin((b / beardSteps) * Math.PI) * 0.015
        const pTuftL0 = rotateY([ -0.032, grid[Math.floor(u0 * fallStepsU)][midJ][1] + tuftHeight, grid[Math.floor(u0 * fallStepsU)][midJ][2] ], baseAngle)
        const pTuftL1 = rotateY([ -0.032, grid[Math.floor(u1 * fallStepsU)][midJ][1] + tuftHeight, grid[Math.floor(u1 * fallStepsU)][midJ][2] ], baseAngle)
        const pTuftR1 = rotateY([  0.032, grid[Math.floor(u1 * fallStepsU)][midJ][1] + tuftHeight, grid[Math.floor(u1 * fallStepsU)][midJ][2] ], baseAngle)
        const pTuftR0 = rotateY([  0.032, grid[Math.floor(u0 * fallStepsU)][midJ][1] + tuftHeight, grid[Math.floor(u0 * fallStepsU)][midJ][2] ], baseAngle)
        addQuad(pTuftL0, pTuftL1, pTuftR1, pTuftR0, bn, bn, bn, bn, [0, 0], [0, 1], [1, 1], [1, 0], 4.0)
      }
    }

    // 2. Three Detailed Standards Petals with Inward Crown Arches (60°, 180°, 300°)
    // Smooth, neat, elegant curved upper endings with natural dome apex
    const stdStepsU = 44
    const stdStepsV = 32
    for (let pIdx = 0; pIdx < 3; pIdx++) {
      const baseAngle = ((pIdx * 120 + 60) * Math.PI) / 180
      const grid: number[][][] = []
      const normGrid: number[][][] = []
      const uvGrid: number[][][] = []

      for (let i = 0; i <= stdStepsU; i++) {
        const u = i / stdStepsU
        grid[i] = []
        normGrid[i] = []
        uvGrid[i] = []

        // Upright vertical profile with elegant inward-arching dome curve
        const yBase = 0.08 + Math.pow(u, 0.78) * 1.26
        const rBase = 0.08 + Math.sin(Math.pow(u, 0.72) * Math.PI * 0.78) * 0.42 - Math.pow(Math.max(0.0, u - 0.62), 1.8) * 0.48

        // Elegant curved dome envelope that tapers neatly and smoothly at the apex:
        // Ensures width curves smoothly to a neat, rounded apex at the top (u=1.0)
        // while maintaining full voluptuous width throughout the body
        const domeWidthEnvelope = Math.sin(Math.pow(u, 0.70) * Math.PI) * Math.pow(Math.max(0.0, 1.0 - Math.pow(u, 5.0)), 0.4)
        const widthMax = 0.46 * domeWidthEnvelope

        // Smooth margin factor (crinkles smoothly vanish near the apex tip so the ending is neat and clear)
        const marginSmooth = Math.pow(Math.max(0.0, 1.0 - Math.pow(u, 3.2)), 1.2)

        for (let j = 0; j <= stdStepsV; j++) {
          const v = j / stdStepsV
          const vCentered = (v - 0.5) * 2.0

          const x = vCentered * widthMax

          // Natural rounded apex curve: Center is taller, lateral margins curve smoothly downward
          const apexArch = (1.0 - vCentered * vCentered) * 0.07 * Math.pow(u, 2.2)
          const y = yBase + apexArch

          // Upper margin fluting, flutter, and deep concave dome arch
          const ruffle = Math.sin(u * 14.0 + vCentered * 5.0) * 0.042 * Math.pow(Math.abs(vCentered), 1.5) * (0.2 + u * 0.8) * marginSmooth
          const crinkle = Math.sin(u * 32.0) * 0.010 * Math.pow(Math.abs(vCentered), 2.0) * marginSmooth
          const cup = -(1.0 - vCentered * vCentered) * 0.12 * Math.sin(u * Math.PI * 0.85)

          const localP = [x, y, rBase + ruffle + crinkle + cup]
          const worldP = rotateY(localP, baseAngle)

          // Smooth curved normals across the dome
          const ny = Math.cos(u * Math.PI * 0.75) * 0.35 - Math.pow(u, 1.5) * 0.45
          const nz = -Math.sin(u * Math.PI * 0.75) * 0.65 - (1.0 - u) * 0.3
          const localN = [vCentered * 0.5, ny, nz]
          const worldN = rotateY(localN, baseAngle)

          grid[i][j] = worldP
          normGrid[i][j] = worldN
          uvGrid[i][j] = [v, u]
        }
      }

      for (let i = 0; i < stdStepsU; i++) {
        for (let j = 0; j < stdStepsV; j++) {
          addQuad(
            grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1],
            normGrid[i][j], normGrid[i + 1][j], normGrid[i + 1][j + 1], normGrid[i][j + 1],
            uvGrid[i][j], uvGrid[i + 1][j], uvGrid[i + 1][j + 1], uvGrid[i][j + 1],
            1.0
          )
        }
      }
    }

    // 3. Three Style Crests with Split Wingtips
    for (let pIdx = 0; pIdx < 3; pIdx++) {
      const baseAngle = (pIdx * 120 * Math.PI) / 180
      const crestSteps = 14
      for (let i = 0; i < crestSteps; i++) {
        const u0 = i / crestSteps
        const u1 = (i + 1) / crestSteps
        const y0 = 0.08 + u0 * 0.48
        const y1 = 0.08 + u1 * 0.48
        const r0 = 0.04 + u0 * 0.24
        const r1 = 0.04 + u1 * 0.24
        const split = u0 > 0.65 ? (u0 - 0.65) * 0.08 : 0.0
        const w0 = 0.04 + u0 * 0.09 + split
        const w1 = 0.04 + u1 * 0.09 + (u1 > 0.65 ? (u1 - 0.65) * 0.08 : 0.0)

        const p0 = rotateY([-w0, y0, r0], baseAngle)
        const p1 = rotateY([-w1, y1, r1], baseAngle)
        const p2 = rotateY([ w1, y1, r1], baseAngle)
        const p3 = rotateY([ w0, y0, r0], baseAngle)
        const cn = rotateY([0, 0.7, 0.7], baseAngle)

        addQuad(p0, p1, p2, p3, cn, cn, cn, cn, [0, u0], [0, u1], [1, u1], [1, u0], 2.0)
      }
    }

    // 4. Botanical S-Curve Stem & Realistic Tapering
    const stemSegments = 48
    const stemRadial = 12

    function getStemCenter(t: number) {
      const y = 0.05 - t * 2.25
      // Realistic botanical 3D S-curve
      const x = Math.sin(t * Math.PI * 1.15) * 0.16 - Math.sin(t * t * Math.PI * 2.0) * 0.08
      const z = Math.sin(t * Math.PI * 1.4) * 0.08 - Math.cos(t * Math.PI) * 0.04 + 0.04
      // Ovary swell at top, slight node bump at bud branch (t=0.42), slender natural base taper
      const nodeFactor = Math.exp(-Math.pow((t - 0.42) / 0.07, 2.0)) * 0.009
      const rad = (0.046 - t * 0.016) + (1.0 - Math.min(1.0, t * 4.0)) * 0.014 + nodeFactor
      return { x, y, z, rad }
    }

    for (let s = 0; s < stemSegments; s++) {
      const t0 = s / stemSegments
      const t1 = (s + 1) / stemSegments
      const pt0 = getStemCenter(t0)
      const pt1 = getStemCenter(t1)

      for (let r = 0; r < stemRadial; r++) {
        const a0 = (r / stemRadial) * Math.PI * 2
        const a1 = ((r + 1) / stemRadial) * Math.PI * 2

        const p0 = [pt0.x + Math.cos(a0) * pt0.rad, pt0.y, pt0.z + Math.sin(a0) * pt0.rad]
        const p1 = [pt1.x + Math.cos(a0) * pt1.rad, pt1.y, pt1.z + Math.sin(a0) * pt1.rad]
        const p2 = [pt1.x + Math.cos(a1) * pt1.rad, pt1.y, pt1.z + Math.sin(a1) * pt1.rad]
        const p3 = [pt0.x + Math.cos(a1) * pt0.rad, pt0.y, pt0.z + Math.sin(a1) * pt0.rad]

        const n0 = [Math.cos(a0), 0, Math.sin(a0)]
        const n1 = [Math.cos(a1), 0, Math.sin(a1)]

        addQuad(p0, p1, p2, p3, n0, n0, n1, n1, [r/stemRadial, t0], [r/stemRadial, t1], [(r+1)/stemRadial, t1], [(r+1)/stemRadial, t0], 3.0)
      }
    }

    // 5. Three Botanical Calyx Spathe Leaves Emerging from Flower Bloom Base (Not attached to branch)
    // Emerge directly from the flower receptacle collar (y=0.06) and flare outward into space like curved leafy petals
    const calyxStepsU = 32
    const calyxStepsV = 16
    for (let cIdx = 0; cIdx < 3; cIdx++) {
      const baseAngle = ((cIdx * 120 + 60) * Math.PI) / 180 // Alternating between the 3 main fall petals
      const grid: number[][][] = []
      const normGrid: number[][][] = []
      const uvGrid: number[][][] = []

      for (let i = 0; i <= calyxStepsU; i++) {
        const u = i / calyxStepsU // 0 at flower receptacle base, 1 at outer spear tip
        grid[i] = []
        normGrid[i] = []
        uvGrid[i] = []

        // Emerges directly from flower bloom base collar (y=0.06), curves downward and arches outward like a petal
        const y = 0.06 - Math.pow(u, 1.35) * 0.58
        const r = 0.07 + Math.sin(Math.pow(u, 0.78) * Math.PI * 0.74) * 0.52 + u * 0.16
        const widthMax = 0.165 * Math.sin(u * Math.PI * 0.88) * (1.0 - Math.pow(u, 2.4))

        for (let j = 0; j <= calyxStepsV; j++) {
          const v = j / calyxStepsV
          const s = (v - 0.5) * 2.0
          const x = s * widthMax

          // V-shaped midrib keel and organic fluting
          const keel = -(1.0 - s * s) * 0.024 * Math.sin(u * Math.PI * 0.95)
          const flute = Math.sin(u * 14.0 + s * 3.5) * 0.018 * Math.pow(Math.abs(s), 1.6) * u
          const drape = -s * s * 0.045 * u

          const localP = [x, y + keel + flute + drape, r]
          const worldP = rotateY(localP, baseAngle)

          const localN = [s * 0.45, 0.65, 0.65]
          const worldN = rotateY(localN, baseAngle)

          grid[i][j] = worldP
          normGrid[i][j] = worldN
          uvGrid[i][j] = [v, u]
        }
      }

      for (let i = 0; i < calyxStepsU; i++) {
        for (let j = 0; j < calyxStepsV; j++) {
          addQuad(
            grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1],
            normGrid[i][j], normGrid[i + 1][j], normGrid[i + 1][j + 1], normGrid[i][j + 1],
            uvGrid[i][j], uvGrid[i + 1][j], uvGrid[i + 1][j + 1], uvGrid[i][j + 1],
            5.0 // PartType: Botanical Leaf
          )
        }
      }
    }

    // Upload to GPU
    const posBuffer = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(positions), gl.STATIC_DRAW)

    const normBuffer = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, normBuffer)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(normals), gl.STATIC_DRAW)

    const uvBuffer = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, uvBuffer)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(uvs), gl.STATIC_DRAW)

    const partBuffer = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, partBuffer)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(partTypes), gl.STATIC_DRAW)

    const indexBuffer = gl.createBuffer()
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer)
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(indices), gl.STATIC_DRAW)
    const indexCount = indices.length

    const lineIndexBuffer = gl.createBuffer()
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, lineIndexBuffer)
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(lineIndices), gl.STATIC_DRAW)
    const lineIndexCount = lineIndices.length

    // Matrix calculations
    const projMatrix = new Float32Array(16)
    const viewMatrix = new Float32Array(16)
    const modelMatrix = new Float32Array(16)
    const mvMatrix = new Float32Array(16)
    const normalMatrix = new Float32Array(9)

    function mat4Perspective(out: Float32Array, fovRad: number, aspect: number, near: number, far: number) {
      const f = 1.0 / Math.tan(fovRad / 2)
      out.fill(0)
      out[0] = f / aspect
      out[5] = f
      out[10] = (far + near) / (near - far)
      out[11] = -1
      out[14] = (2 * far * near) / (near - far)
    }

    function mat4Identity(out: Float32Array) {
      out.fill(0)
      out[0] = 1; out[5] = 1; out[10] = 1; out[15] = 1
    }

    function mat4Multiply(out: Float32Array, a: Float32Array, b: Float32Array) {
      const a00 = a[0], a01 = a[1], a02 = a[2], a03 = a[3]
      const a10 = a[4], a11 = a[5], a12 = a[6], a13 = a[7]
      const a20 = a[8], a21 = a[9], a22 = a[10], a23 = a[11]
      const a30 = a[12], a31 = a[13], a32 = a[14], a33 = a[15]

      for (let i = 0; i < 4; i++) {
        const b0 = b[i*4], b1 = b[i*4+1], b2 = b[i*4+2], b3 = b[i*4+3]
        out[i*4]   = b0*a00 + b1*a10 + b2*a20 + b3*a30
        out[i*4+1] = b0*a01 + b1*a11 + b2*a21 + b3*a31
        out[i*4+2] = b0*a02 + b1*a12 + b2*a22 + b3*a32
        out[i*4+3] = b0*a03 + b1*a13 + b2*a23 + b3*a33
      }
    }

    let angleY = 0
    let animId: number
    let lastTime = performance.now()

    // 15 degrees angle on the opposite side (mouse movement disabled as requested)
    const fixedTiltX = (tiltDegrees * Math.PI) / 180

    // High-performance cached dimensions — eliminates forced reflow/layout thrashing inside requestAnimationFrame
    let cachedCW = typeof window !== "undefined" ? window.innerWidth : 1000
    let cachedCH = typeof window !== "undefined" ? window.innerHeight : 1000

    const updateDimensions = () => {
      if (!canvas) return
      const rect = canvas.getBoundingClientRect()
      // Cap DPR at 1.5 for ultra-sharp visuals without 4K GPU fill-rate throttling
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5)
      const w = Math.round(rect.width * dpr)
      const h = Math.round(rect.height * dpr)
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w
        canvas.height = h
        gl.viewport(0, 0, w, h)
      }
      if (containerRef.current) {
        const cRect = containerRef.current.getBoundingClientRect()
        cachedCW = cRect.width || window.innerWidth
        cachedCH = cRect.height || window.innerHeight
      }
    }

    updateDimensions()
    window.addEventListener("resize", updateDimensions, { passive: true })

    const render = (now: number) => {
      const delta = (now - lastTime) / 1000
      lastTime = now

      // Smooth continuous self-rotation with cinematic rotate-to-center when a petal is selected
      if (targetAngleYRef.current !== null) {
        const target = targetAngleYRef.current
        const diff = Math.atan2(Math.sin(target - angleY), Math.cos(target - angleY))
        if (Math.abs(diff) > 0.003) {
          angleY += diff * 0.12 // smooth ease-out rotation bringing selected petal to front-center!
        } else {
          angleY = target
        }
      } else {
        const isAnyOpen = activePetalsRef.current && Object.values(activePetalsRef.current).some(Boolean)
        const currentSpeed = speedSecondsRef.current
        if (currentSpeed > 0 && !isAnyOpen) {
          angleY += (delta * Math.PI * 2) / currentSpeed
        }
      }

      gl.clearColor(0.0, 0.0, 0.0, 0.0)
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT)

      gl.enable(gl.DEPTH_TEST)
      gl.depthFunc(gl.LEQUAL)
      gl.enable(gl.BLEND)
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)

      gl.useProgram(program)

      const aspect = canvas.width / (canvas.height || 1)
      // Full Desktop Hologram: edge-to-edge desktop framing without boxed constraints
      let fov = (42 * Math.PI) / 180
      let camDist = -3.85
      if (aspect < 0.9) {
        // Portrait mode: adjust camera distance so horizontal falls fit comfortably
        camDist = -3.85 / Math.max(0.60, aspect * 1.10)
      }
      mat4Perspective(projMatrix, fov, aspect, 0.1, 100.0)

      mat4Identity(viewMatrix)
      viewMatrix[14] = camDist

      // User adjustable perspective straight in line
      const currentTiltX = (tiltDegreesRef.current * Math.PI) / 180
      const cosX = Math.cos(currentTiltX), sinX = Math.sin(currentTiltX)
      const rotX = new Float32Array([
        1, 0, 0, 0,
        0, cosX, -sinX, 0,
        0, sinX, cosX, 0,
        0, 0, 0, 1
      ])
      const tempView = new Float32Array(16)
      mat4Multiply(tempView, viewMatrix, rotX)

      mat4Identity(modelMatrix)
      // Pure continuous 360° rotation around vertical axis (~30% screen size)
      const s = scaleRef.current
      const cosY = Math.cos(angleY), sinY = Math.sin(angleY)
      const rotY = new Float32Array([
        cosY * s, 0, sinY * s, 0,
        0, s, 0, 0,
        -sinY * s, 0, cosY * s, 0,
        0, 0, 0, 1
      ])

      // Dynamic vertical centering matching the exact tilt angle and scale
      const ty = 0.435 * Math.cos(currentTiltX) + 0.10 * Math.sin(currentTiltX)
      const trans = new Float32Array([
        1, 0, 0, 0,
        0, 1, 0, 0,
        0, 0, 1, 0,
        0, ty * s, 0, 1
      ])

      const tempM = new Float32Array(16)
      mat4Multiply(tempM, trans, rotY)
      mat4Multiply(mvMatrix, tempView, tempM)

      // Project the 3 Standards petal anchors onto screen coordinates using cached dimensions (ZERO reflow)
      if (interactivePetalsRef.current && containerRef.current) {
        const p0 = project3DPoint(PETAL_ITEMS[0].modelPos, mvMatrix, projMatrix, cachedCW, cachedCH)
        const p1 = project3DPoint(PETAL_ITEMS[1].modelPos, mvMatrix, projMatrix, cachedCW, cachedCH)
        const p2 = project3DPoint(PETAL_ITEMS[2].modelPos, mvMatrix, projMatrix, cachedCW, cachedCH)

        currentCoordsRef.current = [p0, p1, p2]

        if (dot0Ref.current) {
          dot0Ref.current.style.transform = `translate3d(${p0.x}px, ${p0.y}px, 0) translate(-50%, -50%)`
          dot0Ref.current.style.opacity = p0.facing ? "1" : "0.45"
        }
        if (dot1Ref.current) {
          dot1Ref.current.style.transform = `translate3d(${p1.x}px, ${p1.y}px, 0) translate(-50%, -50%)`
          dot1Ref.current.style.opacity = p1.facing ? "1" : "0.45"
        }
        if (dot2Ref.current) {
          dot2Ref.current.style.transform = `translate3d(${p2.x}px, ${p2.y}px, 0) translate(-50%, -50%)`
          dot2Ref.current.style.opacity = p2.facing ? "1" : "0.45"
        }
      }

      normalMatrix[0] = mvMatrix[0]; normalMatrix[1] = mvMatrix[1]; normalMatrix[2] = mvMatrix[2]
      normalMatrix[3] = mvMatrix[4]; normalMatrix[4] = mvMatrix[5]; normalMatrix[5] = mvMatrix[6]
      normalMatrix[6] = mvMatrix[8]; normalMatrix[7] = mvMatrix[9]; normalMatrix[8] = mvMatrix[10]

      gl.uniformMatrix4fv(locs.uProjection, false, projMatrix)
      gl.uniformMatrix4fv(locs.uModelView, false, mvMatrix)
      gl.uniformMatrix3fv(locs.uNormalMatrix, false, normalMatrix)
      gl.uniform1f(locs.uTime, now * 0.001)
      gl.uniform1f(locs.uGlowIntensity, liveGlowRef.current)

      gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer)
      gl.vertexAttribPointer(locs.aPosition, 3, gl.FLOAT, false, 0, 0)
      gl.enableVertexAttribArray(locs.aPosition)

      gl.bindBuffer(gl.ARRAY_BUFFER, normBuffer)
      gl.vertexAttribPointer(locs.aNormal, 3, gl.FLOAT, false, 0, 0)
      gl.enableVertexAttribArray(locs.aNormal)

      gl.bindBuffer(gl.ARRAY_BUFFER, uvBuffer)
      gl.vertexAttribPointer(locs.aUv, 2, gl.FLOAT, false, 0, 0)
      gl.enableVertexAttribArray(locs.aUv)

      gl.bindBuffer(gl.ARRAY_BUFFER, partBuffer)
      gl.vertexAttribPointer(locs.aPartType, 1, gl.FLOAT, false, 0, 0)
      gl.enableVertexAttribArray(locs.aPartType)

      if (liveWireframeRef.current) {
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, lineIndexBuffer)
        gl.drawElements(gl.LINES, lineIndexCount, gl.UNSIGNED_SHORT, 0)
      } else {
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer)
        gl.drawElements(gl.TRIANGLES, indexCount, gl.UNSIGNED_SHORT, 0)
      }

      animId = requestAnimationFrame(render)
    }

    animId = requestAnimationFrame(render)

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener("resize", updateDimensions)
      gl.deleteBuffer(posBuffer)
      gl.deleteBuffer(normBuffer)
      gl.deleteBuffer(uvBuffer)
      gl.deleteBuffer(partBuffer)
      gl.deleteBuffer(indexBuffer)
      gl.deleteBuffer(lineIndexBuffer)
      gl.deleteProgram(program)
      gl.deleteShader(vs)
      gl.deleteShader(fs)
    }
  }, [])

  return (
    <div
      ref={containerRef}
      className={`fixed inset-0 overflow-hidden select-none pointer-events-none z-0 flex items-center justify-center ${className}`}
    >
      {/* Ambient bioluminescent background glow volumes (scaled full for desktop) */}
      {backgroundGlow && (
        <>
          <div className="absolute w-[800px] h-[800px] lg:w-[1300px] lg:h-[1300px] rounded-full bg-iris-600/15 blur-[160px] -top-20 -left-20 pointer-events-none" />
          <div className="absolute w-[850px] h-[850px] lg:w-[1400px] lg:h-[1400px] rounded-full bg-purple-600/15 blur-[170px] -bottom-24 -right-24 pointer-events-none" />
          <div className="absolute w-[700px] h-[700px] lg:w-[1100px] lg:h-[1100px] rounded-full bg-cyan-500/10 blur-[140px] top-1/3 right-1/4 pointer-events-none" />
        </>
      )}

      {/* Cybernetic Orbital Ring Accent (Behind the 3D flower) */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <svg
          viewBox="0 0 800 800"
          className={`${
            scale <= 0.6
              ? "w-[500px] h-[500px] md:w-[600px] md:h-[600px]"
              : "w-[750px] h-[750px] md:w-[1000px] md:h-[1000px] lg:w-[1350px] lg:h-[1350px]"
          } opacity-25`}
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <g className="animate-iris-reverse" style={{ transformOrigin: "400px 400px" }}>
            <circle
              cx="400"
              cy="400"
              r="370"
              stroke="#6366f1"
              strokeWidth="0.75"
              strokeOpacity="0.3"
              strokeDasharray="4 8"
            />
            <circle
              cx="400"
              cy="400"
              r="330"
              stroke="#a855f7"
              strokeWidth="0.6"
              strokeOpacity="0.35"
              strokeDasharray="16 12 4 12"
            />
            <circle
              cx="400"
              cy="400"
              r="280"
              stroke="#06b6d4"
              strokeWidth="0.75"
              strokeOpacity="0.25"
              strokeDasharray="8 16"
            />
          </g>
        </svg>
      </div>

      {/* Main Procedural 3D WebGL Flower Canvas (Holographic Stage) */}
      <div
        className="relative w-full h-full flex items-center justify-center transition-opacity duration-1000"
        style={{ opacity }}
      >
        {/* Layer 1: Ethereal Multi-Stop Aurora Bloom behind the Bloom */}
        {backgroundGlow && (
          <div
            className={`iris-aurora-glow absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full pointer-events-none ${
              scale <= 0.6
                ? "w-[440px] h-[440px] md:w-[540px] md:h-[540px]"
                : "w-[680px] h-[680px] md:w-[950px] md:h-[950px] lg:w-[1250px] lg:h-[1250px]"
            }`}
            style={{
              background:
                "radial-gradient(circle, rgba(165, 243, 252, 0.22) 0%, rgba(99, 102, 241, 0.16) 35%, rgba(168, 85, 247, 0.08) 65%, transparent 75%)",
              filter: "blur(65px)",
            }}
          />
        )}

        {/* Layer 2: Real 3D WebGL Canvas (Hardware accelerated WebGL with zero compositor lag) */}
        <canvas
          ref={canvasRef}
          className="w-full h-full z-0 cursor-default"
        />

        {/* Layer 3: Central Core Breathing Radiance */}
        {backgroundGlow && (
          <div
            className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-indigo-500/25 blur-[75px] animate-iris-breathe pointer-events-none ${
              scale <= 0.6
                ? "w-48 h-48 md:w-56 md:h-56"
                : "w-64 h-64 md:w-80 md:h-80 lg:w-96 lg:h-96"
            }`}
          />
        )}

        {/* Layer 4: Cinematic Anamorphic Horizontal Lens Glint */}
        {backgroundGlow && (
          <div
            className={`iris-anamorphic-streak absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 ${
              scale <= 0.6
                ? "w-[520px] md:w-[680px]"
                : "w-[750px] md:w-[1100px] lg:w-[1450px]"
            }`}
          />
        )}

        {/* Layer 5: Stem Base Grounding Flare */}
        {backgroundGlow && (
          <div
            className="absolute rounded-full pointer-events-none opacity-40 blur-[35px]"
            style={{
              top: `${50 + scale * 26}%`,
              left: "50%",
              transform: "translateX(-50%)",
              width: scale <= 0.6 ? "180px" : "280px",
              height: scale <= 0.6 ? "60px" : "90px",
              background: "radial-gradient(ellipse, rgba(56, 189, 248, 0.4) 0%, rgba(99, 102, 241, 0.2) 60%, transparent 80%)",
            }}
          />
        )}

        {/* Layer 6: Realistic Floating Bioluminescent Pollen & Energy Spores */}
        {backgroundGlow && [
          { top: `${50 - scale * 18}%`, left: "46%", tx: "-25px", ty: "-160px", d: "7s", del: "0s", s: "3px", c: "#e0f2fe", b: "0 0 10px #38bdf8" },
          { top: `${50 - scale * 10}%`, left: "54%", tx: "35px", ty: "-190px", d: "8.5s", del: "1.2s", s: "2.5px", c: "#fef08a", b: "0 0 8px #f59e0b" },
          { top: `${50 - scale * 14}%`, left: "42%", tx: "-40px", ty: "-170px", d: "6.8s", del: "2.5s", s: "3.5px", c: "#c084fc", b: "0 0 12px #a855f7" },
          { top: `${50 - scale * 6}%`, left: "58%", tx: "45px", ty: "-210px", d: "9s", del: "0.8s", s: "2px", c: "#a5f3fc", b: "0 0 8px #06b6d4" },
          { top: `${50 - scale * 2}%`, left: "48%", tx: "15px", ty: "-180px", d: "7.5s", del: "3.2s", s: "3px", c: "#ffffff", b: "0 0 12px #818cf8" },
          { top: `${50 - scale * 22}%`, left: "52%", tx: "-15px", ty: "-150px", d: "6.2s", del: "1.8s", s: "2px", c: "#fef08a", b: "0 0 6px #fbbf24" },
          { top: `${50 + scale * 4}%`, left: "44%", tx: "-30px", ty: "-200px", d: "8.2s", del: "4.1s", s: "3px", c: "#818cf8", b: "0 0 10px #6366f1" },
          { top: `${50 - scale * 4}%`, left: "56%", tx: "25px", ty: "-175px", d: "7.8s", del: "2.1s", s: "2.5px", c: "#e0e7ff", b: "0 0 8px #a5b4fc" },
        ].map((sp, idx) => (
          <span
            key={idx}
            className="iris-spore z-10"
            style={{
              top: sp.top,
              left: sp.left,
              width: sp.s,
              height: sp.s,
              backgroundColor: sp.c,
              boxShadow: sp.b,
              // @ts-expect-error custom CSS properties
              "--tx": sp.tx,
              "--ty": sp.ty,
              "--duration": sp.d,
              "--delay": sp.del,
            }}
          />
        ))}
      </div>

      {/* Subtle Holographic Scanlines (Full screen, no boxed vignette borders) */}
      <div
        className="absolute inset-0 pointer-events-none z-10 opacity-15"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, rgba(6, 182, 212, 0.04) 0px, rgba(6, 182, 212, 0.04) 1px, transparent 1px, transparent 4px)",
        }}
      />

      {/* 3D Rotating Petals Interactive Overlay */}
      {interactivePetals && (
        <div className="absolute inset-0 pointer-events-none z-20 overflow-hidden">
          <style jsx>{`
            @keyframes sciFiFlow {
              to {
                stroke-dashoffset: -32;
              }
            }
          `}</style>

          {/* Holographic Laser Leader Lines connecting Petal Reticles to HUD Stations */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none overflow-visible">
            {PETAL_ITEMS.map((item, i) => {
              const isOpen = Boolean(activePetals[item.id])
              const cx = openCoords[i]?.x || 0
              const cy = openCoords[i]?.y || 0
              if (!cx && !cy) return null

              const cW = containerRef.current?.clientWidth || 1000
              const cH = containerRef.current?.clientHeight || 800

              let d = ""
              let targetX = 0
              let targetY = 0

              if (cW >= 768) {
                if (i === 0) {
                  // Left Dock: Neural Core (Chat)
                  const cardTop = Math.max(90, Math.min(cH - 260, cy - 60))
                  targetX = 334 // right edge of Card 0 (24 + 310)
                  targetY = cardTop + 55
                  const midX = Math.max(targetX + 30, cx - Math.min(120, Math.abs(cx - targetX) * 0.45))
                  d = `M ${cx} ${cy} L ${midX} ${targetY} L ${targetX} ${targetY}`
                } else if (i === 1) {
                  // Top Dock: Visual Themes
                  const centerX = Math.round(cW / 2)
                  targetX = Math.max(340, Math.min(cW - 650, centerX - 155)) + 155
                  targetY = 190 // bottom edge of top card (14 + 176)
                  d = `M ${cx} ${cy} L ${cx} ${targetY + 28} L ${targetX} ${targetY}`
                } else {
                  // Right Dock: System Rules (Skills)
                  const cardTop = Math.max(90, Math.min(cH - 260, cy - 60))
                  targetX = cW - 334 // left edge of Card 2
                  targetY = cardTop + 55
                  const midX = Math.min(targetX - 30, cx + Math.min(120, Math.abs(targetX - cx) * 0.45))
                  d = `M ${cx} ${cy} L ${midX} ${targetY} L ${targetX} ${targetY}`
                }
              } else {
                targetX = cx
                targetY = cH - 210
                d = `M ${cx} ${cy} L ${cx} ${targetY}`
              }

              return (
                <g key={`laser-${item.id}`} style={{ opacity: isOpen ? 1 : 0, transition: "opacity 0.25s ease" }}>
                  {/* Holographic glowing path */}
                  <path
                    d={d}
                    stroke={item.color}
                    strokeWidth={1.5}
                    strokeDasharray="6 6"
                    fill="none"
                    style={{
                      animation: "sciFiFlow 1.2s linear infinite",
                      filter: `drop-shadow(0 0 6px ${item.color})`,
                    }}
                  />

                  {/* Petal Anchor Node */}
                  <polygon
                    points={`${cx},${cy - 4} ${cx + 4},${cy} ${cx},${cy + 4} ${cx - 4},${cy}`}
                    fill={item.color}
                  />

                  {/* Terminal Card Dock Connector */}
                  <circle cx={targetX} cy={targetY} r="3" fill="#ffffff" stroke={item.color} strokeWidth="1.5" />
                </g>
              )
            })}
          </svg>

          {/* The 3 Holographic Target Beacons on Petals in 3D Space */}
          {PETAL_ITEMS.map((item, i) => {
            const isOpen = Boolean(activePetals[item.id])
            const isHovered = hoveredPetalId === item.id

            return (
              <div
                key={item.id}
                ref={dotRefs[i]}
                onClick={() => togglePetal(item.id)}
                onMouseEnter={() => setHoveredPetalId(item.id)}
                onMouseLeave={() => setHoveredPetalId(null)}
                className="absolute top-0 left-0 pointer-events-auto cursor-pointer group select-none flex flex-col items-center"
                style={{
                  willChange: "transform",
                  zIndex: 35,
                }}
              >
                {/* Cyber Reticle (Micro HUD Diamond & Target Brackets) */}
                <div className="relative w-6 h-6 flex items-center justify-center">
                  {/* Rotating Corner Brackets (HUD Reticle) */}
                  <div
                    className={`absolute inset-0 rounded-sm border transition-all duration-300 ${
                      isOpen || isHovered ? "rotate-45 scale-125" : "rotate-0 scale-100"
                    }`}
                    style={{
                      borderColor: isOpen ? item.color : isHovered ? "#ffffff" : `${item.color}90`,
                      boxShadow: isOpen || isHovered ? `0 0 12px ${item.color}` : "none",
                    }}
                  />

                  {/* Center Photon Dot */}
                  <div
                    className="w-1.5 h-1.5 rounded-full transition-all duration-200"
                    style={{
                      backgroundColor: isOpen || isHovered ? "#ffffff" : item.color,
                      boxShadow: `0 0 6px ${isOpen || isHovered ? "#ffffff" : item.color}`,
                    }}
                  />

                  {/* Subtle radar scan ring when open */}
                  {isOpen && (
                    <div
                      className="absolute -inset-2 rounded-full border pointer-events-none animate-ping"
                      style={{ borderColor: `${item.color}60` }}
                    />
                  )}
                </div>

                {/* Sleek Monospace Telemetry Micro-Pill */}
                <div
                  className="mt-1 px-1.5 py-0.5 rounded font-mono text-[9px] font-bold tracking-wider whitespace-nowrap border backdrop-blur-md transition-all duration-200 flex items-center gap-1"
                  style={{
                    backgroundColor: "rgba(5, 7, 18, 0.92)",
                    borderColor: isOpen || isHovered ? item.color : "rgba(255, 255, 255, 0.15)",
                    color: isOpen || isHovered ? "#ffffff" : "rgba(255, 255, 255, 0.75)",
                    boxShadow: isOpen || isHovered ? `0 0 10px ${item.glowRgba}` : "none",
                  }}
                >
                  <span
                    className="w-1 h-1 rounded-full animate-pulse"
                    style={{ backgroundColor: item.color }}
                  />
                  <span>{isHovered || isOpen ? item.shortLabel : item.numLabel}</span>
                </div>
              </div>
            )
          })}

          {/* Sci-Fi HUD Docked Telemetry Panels (ZERO OVERLAP) */}
          {PETAL_ITEMS.map((item, i) => {
            const isOpen = Boolean(activePetals[item.id])
            const cx = openCoords[i]?.x || 0
            const cy = openCoords[i]?.y || 0
            const cW = containerRef.current?.clientWidth || 1000
            const cH = containerRef.current?.clientHeight || 800

            let cardStyle: React.CSSProperties = {}
            if (cW >= 768) {
              if (i === 0) {
                // Left Dock (Neural Core // Chat)
                cardStyle = {
                  left: 24,
                  top: Math.max(90, Math.min(cH - 260, cy - 60)),
                  width: 310,
                }
              } else if (i === 1) {
                // Top Dock (Visual Themes)
                const centerX = Math.round(cW / 2)
                cardStyle = {
                  left: Math.max(340, Math.min(cW - 650, centerX - 155)),
                  top: 14,
                  width: 310,
                }
              } else {
                // Right Dock (System Rules // Skills)
                cardStyle = {
                  left: cW - 334,
                  top: Math.max(90, Math.min(cH - 260, cy - 60)),
                  width: 310,
                }
              }
            } else {
              cardStyle = {
                left: 16,
                right: 16,
                bottom: 20,
                width: cW - 32,
              }
            }

            return (
              <div
                key={`card-${item.id}`}
                className="absolute pointer-events-auto z-30 transition-all duration-300"
                style={{
                  ...cardStyle,
                  opacity: isOpen ? 1 : 0,
                  transform: isOpen ? "translateY(0) scale(1)" : "translateY(8px) scale(0.96)",
                  pointerEvents: isOpen ? "auto" : "none",
                  transition: isOpen
                    ? "opacity 0.25s cubic-bezier(0.16, 1, 0.3, 1), transform 0.25s cubic-bezier(0.16, 1, 0.3, 1)"
                    : "opacity 0.15s ease-in, transform 0.15s ease-in",
                }}
              >
                {/* Sci-Fi HUD Terminal Panel */}
                <div
                  className="relative p-4 rounded-xl bg-[#060814]/94 backdrop-blur-2xl border border-white/10 shadow-2xl overflow-hidden"
                  style={{
                    boxShadow: isOpen
                      ? `0 12px 35px -8px ${item.glowRgba}, inset 0 0 0 1px ${item.color}30`
                      : "none",
                  }}
                >
                  {/* Holographic 4-Corner Crosshair Brackets */}
                  <span className="absolute top-0 left-0 w-2.5 h-2.5 border-t-2 border-l-2 pointer-events-none" style={{ borderColor: item.color }} />
                  <span className="absolute top-0 right-0 w-2.5 h-2.5 border-t-2 border-r-2 pointer-events-none" style={{ borderColor: item.color }} />
                  <span className="absolute bottom-0 left-0 w-2.5 h-2.5 border-b-2 border-l-2 pointer-events-none" style={{ borderColor: item.color }} />
                  <span className="absolute bottom-0 right-0 w-2.5 h-2.5 border-b-2 border-r-2 pointer-events-none" style={{ borderColor: item.color }} />

                  {/* Top Glowing Laser Edge */}
                  <div
                    className="absolute top-0 left-0 right-0 h-[1.5px] pointer-events-none"
                    style={{
                      background: `linear-gradient(90deg, transparent 0%, ${item.color} 50%, transparent 100%)`,
                      boxShadow: `0 0 8px ${item.color}`,
                    }}
                  />

                  {/* Sci-Fi Header Telemetry Bar */}
                  <div className="flex items-center justify-between border-b border-white/5 pb-2 mb-2.5">
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: item.color }} />
                      <span className="text-[10px] font-mono tracking-widest text-white/50 uppercase">
                        {item.petalLabel}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => togglePetal(item.id)}
                      aria-label="Close card"
                      className="w-5 h-5 rounded flex items-center justify-center text-white/40 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>

                  {/* Card Body */}
                  <div className="flex items-start gap-2.5 mb-2.5">
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center border flex-shrink-0 mt-0.5"
                      style={{
                        backgroundColor: `${item.color}15`,
                        borderColor: `${item.color}40`,
                        color: item.color,
                        boxShadow: `0 0 10px ${item.glowRgba}`,
                      }}
                    >
                      <item.icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white tracking-wide">{item.title}</h3>
                      <p className="text-xs text-white/60 leading-relaxed mt-0.5 line-clamp-2">
                        {item.desc}
                      </p>
                    </div>
                  </div>

                  {/* Sci-Fi Action Button */}
                  <Link
                    href={item.href}
                    prefetch={true}
                    className="w-full flex items-center justify-between px-3 py-1.5 rounded-lg border text-xs font-mono font-semibold tracking-wider transition-all duration-75 active:scale-[0.98] group/btn cursor-pointer"
                    style={{
                      backgroundColor: `${item.color}15`,
                      borderColor: `${item.color}50`,
                      color: "#ffffff",
                    }}
                  >
                    <span className="flex items-center gap-1.5">
                      <span style={{ color: item.color }}>&gt;</span>
                      <span>{item.action}</span>
                    </span>
                    <ArrowRight
                      className="w-3.5 h-3.5 transition-transform duration-100 group-hover/btn:translate-x-1"
                      style={{ color: item.color }}
                    />
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
