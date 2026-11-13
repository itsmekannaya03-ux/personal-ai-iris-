import React, { useEffect, useRef } from 'react'

export default function IrisFlowerBackground({
  opacity = 0.55,
  speedSeconds = 70,
  tiltDegrees = -23,
  glowIntensity = 3,
  backgroundGlow = true,
  scale = 0.80,
}) {
  const canvasRef = useRef(null)

  const speedSecondsRef = useRef(speedSeconds)
  speedSecondsRef.current = speedSeconds

  const tiltDegreesRef = useRef(tiltDegrees)
  tiltDegreesRef.current = tiltDegrees

  const glowIntensityRef = useRef(glowIntensity)
  glowIntensityRef.current = glowIntensity

  const scaleRef = useRef(scale)
  scaleRef.current = scale

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const gl = canvas.getContext('webgl', { antialias: true, alpha: true })
    if (!gl) return

    const vsSource = `
      attribute vec3 aPosition;
      attribute vec3 aNormal;
      attribute vec2 aUv;
      attribute float aPartType;

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
          // --- STANDARD PETAL: Upright gossamer domed crown with scalloped frills ---
          float vCenter = abs(vUv.x - 0.5) * 2.0;
          float verticalVeins = sin(vUv.x * 38.0) * 0.5 + 0.5;
          verticalVeins = pow(verticalVeins, 3.5) * 0.35;
          float crownFrills = sin(vUv.x * 28.0 + vUv.y * 12.0) * 0.5 + 0.5;

          finalColor = mix(icyCyan * 0.30, pureWhite, 0.70);
          finalColor += icyCyan * (fresnel * (uGlowIntensity * 0.15) + crownFrills * 0.22 + verticalVeins * 0.25);
          finalColor += pureWhite * spec * 0.45;
          alpha = mix(0.50, 0.90, fresnel * 1.35 + vCenter * 0.2);

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

    function createShader(glContext, type, src) {
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
      aPosition: gl.getAttribLocation(program, 'aPosition'),
      aNormal: gl.getAttribLocation(program, 'aNormal'),
      aUv: gl.getAttribLocation(program, 'aUv'),
      aPartType: gl.getAttribLocation(program, 'aPartType'),
      uProjection: gl.getUniformLocation(program, 'uProjection'),
      uModelView: gl.getUniformLocation(program, 'uModelView'),
      uNormalMatrix: gl.getUniformLocation(program, 'uNormalMatrix'),
      uTime: gl.getUniformLocation(program, 'uTime'),
      uGlowIntensity: gl.getUniformLocation(program, 'uGlowIntensity'),
    }

    const positions = []
    const normals = []
    const uvs = []
    const partTypes = []
    const indices = []
    let vertexOffset = 0

    function addQuad(p0, p1, p2, p3, n0, n1, n2, n3, uv0, uv1, uv2, uv3, partType) {
      positions.push(...p0, ...p1, ...p2, ...p3)
      normals.push(...n0, ...n1, ...n2, ...n3)
      uvs.push(...uv0, ...uv1, ...uv2, ...uv3)
      partTypes.push(partType, partType, partType, partType)
      indices.push(
        vertexOffset, vertexOffset + 1, vertexOffset + 2,
        vertexOffset, vertexOffset + 2, vertexOffset + 3
      )
      vertexOffset += 4
    }

    function rotateY(p, angle) {
      const cosA = Math.cos(angle)
      const sinA = Math.sin(angle)
      return [p[0] * cosA + p[2] * sinA, p[1], -p[0] * sinA + p[2] * cosA]
    }

    // 1. Three Detailed Cascading Fall Petals with Voluptuous Curves (0°, 120°, 240°)
    const fallStepsU = 44
    const fallStepsV = 32
    for (let pIdx = 0; pIdx < 3; pIdx++) {
      const baseAngle = (pIdx * 120 * Math.PI) / 180
      const grid = []
      const normGrid = []
      const uvGrid = []

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
    const stdStepsU = 38
    const stdStepsV = 26
    for (let pIdx = 0; pIdx < 3; pIdx++) {
      const baseAngle = ((pIdx * 120 + 60) * Math.PI) / 180
      const grid = []
      const normGrid = []
      const uvGrid = []

      for (let i = 0; i <= stdStepsU; i++) {
        const u = i / stdStepsU
        grid[i] = []
        normGrid[i] = []
        uvGrid[i] = []

        // Upright vertical profile with voluptuous inward arching dome curve
        const y = 0.08 + Math.pow(u, 0.78) * 1.25
        const r = 0.08 + Math.sin(Math.pow(u, 0.75) * Math.PI * 0.80) * 0.44 - Math.pow(Math.max(0.0, u - 0.65), 1.9) * 0.52
        const widthMax = 0.40 * Math.sin(u * Math.PI * 0.88)

        for (let j = 0; j <= stdStepsV; j++) {
          const v = j / stdStepsV
          const vCentered = (v - 0.5) * 2.0

          const x = vCentered * widthMax

          // Upper margin fluting, flutter, and deep concave dome arch
          const ruffle = Math.sin(u * 16.0 + vCentered * 6.0) * 0.055 * Math.pow(Math.abs(vCentered), 1.4) * (0.2 + u * 0.8)
          const crinkle = Math.sin(u * 38.0) * 0.016 * Math.pow(Math.abs(vCentered), 2.0)
          const cup = -(1.0 - vCentered * vCentered) * 0.11 * Math.sin(u * Math.PI * 0.9)

          const localP = [x, y, r + ruffle + crinkle + cup]
          const worldP = rotateY(localP, baseAngle)

          const localN = [vCentered * 0.6, 0.3, -0.7]
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

    function getStemCenter(t) {
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
      const grid = []
      const normGrid = []
      const uvGrid = []

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

    // Buffers
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

    const projMatrix = new Float32Array(16)
    const viewMatrix = new Float32Array(16)
    const modelMatrix = new Float32Array(16)
    const mvMatrix = new Float32Array(16)
    const normalMatrix = new Float32Array(9)

    function mat4Perspective(out, fovRad, aspect, near, far) {
      const f = 1.0 / Math.tan(fovRad / 2)
      out.fill(0)
      out[0] = f / aspect
      out[5] = f
      out[10] = (far + near) / (near - far)
      out[11] = -1
      out[14] = (2 * far * near) / (near - far)
    }

    function mat4Identity(out) {
      out.fill(0)
      out[0] = 1; out[5] = 1; out[10] = 1; out[15] = 1
    }

    function mat4Multiply(out, a, b) {
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
    let animId
    let lastTime = performance.now()

    // 15 degrees angle on the opposite side (mouse movement disabled as requested)
    const fixedTiltX = (tiltDegrees * Math.PI) / 180

    const render = (now) => {
      const rect = canvas.getBoundingClientRect()
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const w = Math.round(rect.width * dpr)
      const h = Math.round(rect.height * dpr)
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w
        canvas.height = h
        gl.viewport(0, 0, w, h)
      }

      const delta = (now - lastTime) / 1000
      lastTime = now

      const currentSpeed = speedSecondsRef.current
      if (currentSpeed > 0) {
        angleY += (delta * Math.PI * 2) / currentSpeed
      }

      gl.clearColor(0.0, 0.0, 0.0, 0.0)
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT)
      gl.enable(gl.DEPTH_TEST)
      gl.depthFunc(gl.LEQUAL)
      gl.enable(gl.BLEND)
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)

      gl.useProgram(program)

      const aspect = canvas.width / canvas.height
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

      normalMatrix[0] = mvMatrix[0]; normalMatrix[1] = mvMatrix[1]; normalMatrix[2] = mvMatrix[2]
      normalMatrix[3] = mvMatrix[4]; normalMatrix[4] = mvMatrix[5]; normalMatrix[5] = mvMatrix[6]
      normalMatrix[6] = mvMatrix[8]; normalMatrix[7] = mvMatrix[9]; normalMatrix[8] = mvMatrix[10]

      gl.uniformMatrix4fv(locs.uProjection, false, projMatrix)
      gl.uniformMatrix4fv(locs.uModelView, false, mvMatrix)
      gl.uniformMatrix3fv(locs.uNormalMatrix, false, normalMatrix)
      gl.uniform1f(locs.uTime, now * 0.001)
      gl.uniform1f(locs.uGlowIntensity, glowIntensityRef.current)

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

      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer)
      gl.drawElements(gl.TRIANGLES, indexCount, gl.UNSIGNED_SHORT, 0)

      animId = requestAnimationFrame(render)
    }

    animId = requestAnimationFrame(render)

    return () => {
      cancelAnimationFrame(animId)
      gl.deleteBuffer(posBuffer)
      gl.deleteBuffer(normBuffer)
      gl.deleteBuffer(uvBuffer)
      gl.deleteBuffer(partBuffer)
      gl.deleteBuffer(indexBuffer)
      gl.deleteProgram(program)
      gl.deleteShader(vs)
      gl.deleteShader(fs)
    }
  }, [])

  return (
    <div
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
        userSelect: 'none',
        zIndex: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          opacity,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'opacity 1s ease',
        }}
      >
        {/* Layer 1: Ethereal Aurora Bloom (restored background glow) */}
        {backgroundGlow && (
          <div
            className="iris-aurora-glow"
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: scale <= 0.6 ? '440px' : '720px',
              height: scale <= 0.6 ? '440px' : '720px',
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(165, 243, 252, 0.22) 0%, rgba(99, 102, 241, 0.16) 35%, rgba(168, 85, 247, 0.08) 65%, transparent 75%)',
              filter: 'blur(65px)',
              pointerEvents: 'none',
            }}
          />
        )}

        {/* Layer 2: 3D WebGL Canvas */}
        <canvas
          ref={canvasRef}
          style={{
            width: '100%',
            height: '100%',
          }}
        />

        {/* Layer 3: Central Core Radiance (restored background glow) */}
        {backgroundGlow && (
          <div
            className="animate-iris-breathe"
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: scale <= 0.6 ? '200px' : '280px',
              height: scale <= 0.6 ? '200px' : '280px',
              borderRadius: '50%',
              background: 'rgba(99, 102, 241, 0.22)',
              filter: 'blur(75px)',
              pointerEvents: 'none',
            }}
          />
        )}

        {/* Layer 4: Anamorphic Horizontal Glint (restored background glow) */}
        {backgroundGlow && (
          <div
            className="iris-anamorphic-streak"
            style={{
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: scale <= 0.6 ? '540px' : '850px',
              zIndex: 10,
            }}
          />
        )}

        {/* Layer 5: Floating Bioluminescent Pollen Spores (restored) */}
        {backgroundGlow && [
          { top: `${50 - scale * 18}%`, left: '46%', tx: '-25px', ty: '-160px', d: '7s', del: '0s', s: '3px', c: '#e0f2fe', b: '0 0 10px #38bdf8' },
          { top: `${50 - scale * 10}%`, left: '54%', tx: '35px', ty: '-190px', d: '8.5s', del: '1.2s', s: '2.5px', c: '#fef08a', b: '0 0 8px #f59e0b' },
          { top: `${50 - scale * 14}%`, left: '42%', tx: '-40px', ty: '-170px', d: '6.8s', del: '2.5s', s: '3.5px', c: '#c084fc', b: '0 0 12px #a855f7' },
          { top: `${50 - scale * 6}%`, left: '58%', tx: '45px', ty: '-210px', d: '9s', del: '0.8s', s: '2px', c: '#a5f3fc', b: '0 0 8px #06b6d4' },
          { top: `${50 - scale * 2}%`, left: '48%', tx: '15px', ty: '-180px', d: '7.5s', del: '3.2s', s: '3px', c: '#ffffff', b: '0 0 12px #818cf8' },
          { top: `${50 - scale * 22}%`, left: '52%', tx: '-15px', ty: '-150px', d: '6.2s', del: '1.8s', s: '2px', c: '#fef08a', b: '0 0 6px #fbbf24' },
        ].map((sp, idx) => (
          <span
            key={idx}
            className="iris-spore"
            style={{
              top: sp.top,
              left: sp.left,
              width: sp.s,
              height: sp.s,
              backgroundColor: sp.c,
              boxShadow: sp.b,
              zIndex: 10,
              '--tx': sp.tx,
              '--ty': sp.ty,
              '--duration': sp.d,
              '--delay': sp.del,
            }}
          />
        ))}

        {/* Layer 6: Subtle Holographic Scanlines (Full screen, no boxed vignette borders) */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            pointerEvents: 'none',
            zIndex: 10,
            opacity: 0.15,
            backgroundImage: 'repeating-linear-gradient(0deg, rgba(6, 182, 212, 0.04) 0px, rgba(6, 182, 212, 0.04) 1px, transparent 1px, transparent 4px)',
          }}
        />
      </div>
    </div>
  )
}
