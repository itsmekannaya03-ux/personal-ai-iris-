"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";

const BaseCurve: any = THREE.Curve;
class HeartCurve extends BaseCurve {
  getPoint(t: number, optionalTarget = new THREE.Vector3()) {
    const angle = t * Math.PI * 2;
    const x = 16 * Math.pow(Math.sin(angle), 3);
    const y =
      13 * Math.cos(angle) -
      5 * Math.cos(2 * angle) -
      2 * Math.cos(3 * angle) -
      Math.cos(4 * angle);

    return optionalTarget.set(x * 0.002, (y + 6) * 0.002, 0);
  }
}

const sharedHeartCurve = new HeartCurve();

function generatePbrTextures(): {
  colorMap: THREE.CanvasTexture;
  bumpMap: THREE.CanvasTexture;
} {
  const size = 512;
  const canvasC = document.createElement("canvas");
  const canvasB = document.createElement("canvas");
  canvasC.width = canvasB.width = size;
  canvasC.height = canvasB.height = size;
  const ctxC = canvasC.getContext("2d");
  const ctxB = canvasB.getContext("2d");

  if (ctxC && ctxB) {
    ctxC.fillStyle = "#dcdcdc";
    ctxC.fillRect(0, 0, size, size);
    ctxB.fillStyle = "#808080";
    ctxB.fillRect(0, 0, size, size);

    for (let i = 0; i < 8000; i++) {
      const x = Math.random() * size;
      const y = Math.random() * size;
      const r = 0.5 + Math.random() * 1.5;
      const isDark = Math.random() > 0.15;

      ctxC.beginPath();
      ctxC.arc(x, y, r, 0, Math.PI * 2);
      ctxC.fillStyle = isDark ? "#222222" : "#dddddd";
      ctxC.fill();

      ctxB.beginPath();
      ctxB.arc(x, y, r, 0, Math.PI * 2);
      ctxB.fillStyle = isDark ? "#000000" : "#ffffff";
      ctxB.fill();
    }
  }

  const texC = new THREE.CanvasTexture(canvasC);
  const texB = new THREE.CanvasTexture(canvasB);
  texC.wrapS = texB.wrapS = THREE.RepeatWrapping;
  texC.wrapT = texB.wrapT = THREE.RepeatWrapping;
  texC.repeat.set(6, 3);
  texB.repeat.set(6, 3);
  texC.needsUpdate = true;
  texB.needsUpdate = true;

  return { colorMap: texC, bumpMap: texB };
}

function createContactShadowTexture(): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext("2d")!;
  const gradient = ctx.createRadialGradient(128, 128, 10, 128, 128, 120);
  gradient.addColorStop(0, "rgba(0, 0, 0, 0.85)");
  gradient.addColorStop(0.3, "rgba(0, 0, 0, 0.55)");
  gradient.addColorStop(0.7, "rgba(0, 0, 0, 0.18)");
  gradient.addColorStop(1, "rgba(0, 0, 0, 0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 256, 256);
  const tex = new THREE.CanvasTexture(canvas);
  return tex;
}

function createEyeCurves() {
  const w = 0.025;
  const h = 0.035;
  const r = 0.02;
  const g = 0.005;

  const tPath = new THREE.CurvePath<THREE.Vector3>();
  tPath.add(new THREE.LineCurve3(new THREE.Vector3(-w, g, 0), new THREE.Vector3(-w, h - r, 0)));
  tPath.add(new THREE.QuadraticBezierCurve3(new THREE.Vector3(-w, h - r, 0), new THREE.Vector3(-w, h, 0), new THREE.Vector3(-w + r, h, 0)));
  tPath.add(new THREE.LineCurve3(new THREE.Vector3(-w + r, h, 0), new THREE.Vector3(w - r, h, 0)));
  tPath.add(new THREE.QuadraticBezierCurve3(new THREE.Vector3(w - r, h, 0), new THREE.Vector3(w, h, 0), new THREE.Vector3(w, h - r, 0)));
  tPath.add(new THREE.LineCurve3(new THREE.Vector3(w, h - r, 0), new THREE.Vector3(w, g, 0)));

  const bPath = new THREE.CurvePath<THREE.Vector3>();
  bPath.add(new THREE.LineCurve3(new THREE.Vector3(-w, -g, 0), new THREE.Vector3(-w, -(h - r), 0)));
  bPath.add(new THREE.QuadraticBezierCurve3(new THREE.Vector3(-w, -(h - r), 0), new THREE.Vector3(-w, -h, 0), new THREE.Vector3(-w + r, -h, 0)));
  bPath.add(new THREE.LineCurve3(new THREE.Vector3(-w + r, -h, 0), new THREE.Vector3(w - r, -h, 0)));
  bPath.add(new THREE.QuadraticBezierCurve3(new THREE.Vector3(w - r, -h, 0), new THREE.Vector3(w, -h, 0), new THREE.Vector3(w, -(h - r), 0)));
  bPath.add(new THREE.LineCurve3(new THREE.Vector3(w, -(h - r), 0), new THREE.Vector3(w, -g, 0)));

  return { topPath: tPath, bottomPath: bPath };
}

export interface RobotCharacterProps {
  color?: string;
  pantallaColor?: string;
  pantallaBrillo?: number;
  scale?: number;
  theme?: "dark" | "light";
  className?: string;
  onRobotClick?: () => void;
  isTyping?: boolean;
}

export function RobotCharacter({
  color = "#c4c4c4",
  pantallaColor = "#00ffc6",
  pantallaBrillo = 1.2,
  scale = 1.35,
  theme = "light",
  className = "",
  onRobotClick,
  isTyping = false,
}: RobotCharacterProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const isLovedRef = useRef(false);
  const loveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [isLovedState, setIsLovedState] = useState(false);
  const isTypingRef = useRef(isTyping);

  useEffect(() => {
    isTypingRef.current = isTyping;
  }, [isTyping]);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const isLight = theme === "light";

    // --- Scene, Camera, Renderer ---
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(36, width / height, 0.1, 100);
    camera.position.set(0, 1.4, 7.8);
    camera.lookAt(0, -0.4, 0);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "high-performance" });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      container.appendChild(renderer.domElement);
    } catch (err) {
      console.warn("RobotCharacter WebGL unavailable:", err);
      return;
    }

    // --- Lighting ---
    const ambientLight = new THREE.AmbientLight(0xffffff, isLight ? 1.2 : 0.95);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x00ffe2, isLight ? 1.4 : 1.3);
    dirLight1.position.set(2, 7, 4);
    dirLight1.castShadow = true;
    dirLight1.shadow.mapSize.width = 1024;
    dirLight1.shadow.mapSize.height = 1024;
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xdbdbdb, isLight ? 1.0 : 0.8);
    dirLight2.position.set(-6, 3, -4);
    scene.add(dirLight2);

    const blueRimLight = new THREE.DirectionalLight(0x6366f1, isLight ? 1.2 : 1.6);
    blueRimLight.position.set(6, -2, -3);
    scene.add(blueRimLight);

    // --- PBR Textures ---
    const { colorMap, bumpMap } = generatePbrTextures();

    // --- Robot Hierarchy & Ground Height ---
    const GROUND_Y = -1.55; // Ground floor height
    const robotRoot = new THREE.Group();
    robotRoot.position.set(0, GROUND_Y + 0.43 * scale, 0);
    robotRoot.scale.set(scale, scale, scale);
    scene.add(robotRoot);

    // Subtle Cyber Floor Grid (establishes the full ground plane across the screen)
    const floorGrid = new THREE.GridHelper(
      40,
      40,
      isLight ? 0x06b6d4 : 0x00ffc6,
      isLight ? 0xcbd5e1 : 0x1e293b
    );
    floorGrid.position.set(0, GROUND_Y, 0);
    (floorGrid.material as THREE.Material).transparent = true;
    (floorGrid.material as THREE.Material).opacity = isLight ? 0.45 : 0.12;
    scene.add(floorGrid);

    // Contact Shadow on the Ground Plane
    const shadowTex = createContactShadowTexture();
    const shadowGeo = new THREE.PlaneGeometry(2.0 * scale, 2.0 * scale);
    const shadowMat = new THREE.MeshBasicMaterial({
      map: shadowTex,
      transparent: true,
      opacity: isLight ? 0.35 : 0.85,
      depthWrite: false,
    });
    const shadowMesh = new THREE.Mesh(shadowGeo, shadowMat);
    shadowMesh.rotation.x = -Math.PI / 2;
    shadowMesh.position.set(0, GROUND_Y + 0.002, 0);
    scene.add(shadowMesh);

    // Grid Floor Ring helper on the ground
    const gridCircleGeo = new THREE.RingGeometry(0.85 * scale, 0.88 * scale, 64);
    const gridCircleMat = new THREE.MeshBasicMaterial({
      color: 0x00ffc6,
      transparent: true,
      opacity: isLight ? 0.4 : 0.2,
      side: THREE.DoubleSide,
    });
    const gridRing = new THREE.Mesh(gridCircleGeo, gridCircleMat);
    gridRing.rotation.x = -Math.PI / 2;
    gridRing.position.set(0, GROUND_Y + 0.003, 0);
    scene.add(gridRing);

    // Materials
    const chassisMat = new THREE.MeshStandardMaterial({
      color: color,
      map: colorMap,
      bumpMap: bumpMap,
      bumpScale: 0.005,
      roughness: 0.85,
      metalness: 0.15,
    });

    const headMat = new THREE.MeshStandardMaterial({
      color: 0x111111,
      roughness: 0.95,
      metalness: 0.1,
    });

    // Body
    const bodyGroup = new THREE.Group();
    robotRoot.add(bodyGroup);

    const bodyMesh = new THREE.Mesh(
      new THREE.SphereGeometry(0.43, 64, 64, 0, Math.PI * 2, Math.PI * 0.15, Math.PI * 0.85),
      chassisMat
    );
    bodyMesh.castShadow = true;
    bodyMesh.receiveShadow = true;
    bodyGroup.add(bodyMesh);

    // Body Bevel Torus
    const bevelMesh = new THREE.Mesh(
      new THREE.TorusGeometry(0.235, 0.025, 32, 64),
      chassisMat
    );
    bevelMesh.position.set(0, 0.34, 0);
    bevelMesh.rotation.x = Math.PI / 2;
    bodyGroup.add(bevelMesh);

    // Neck Lathe
    const neckPoints = [
      new THREE.Vector2(0.1, -0.05),
      new THREE.Vector2(0.215, -0.05),
      new THREE.Vector2(0.28, 0.02),
      new THREE.Vector2(0.295, 0.045),
      new THREE.Vector2(0.27, 0.055),
      new THREE.Vector2(0.1, 0.055),
    ];
    const neckMesh = new THREE.Mesh(new THREE.LatheGeometry(neckPoints, 64), chassisMat);
    neckMesh.position.set(0, 0.38, 0);
    bodyGroup.add(neckMesh);

    // Head Group
    const headGroup = new THREE.Group();
    headGroup.position.set(0, 0.6, 0);
    bodyGroup.add(headGroup);

    const headMesh = new THREE.Mesh(new THREE.SphereGeometry(0.28, 64, 64), headMat);
    headMesh.castShadow = true;
    headGroup.add(headMesh);

    // Glass Visor Capsule with Fresnel glow
    const capsuleUniforms = {
      color: { value: new THREE.Color(pantallaColor) },
      power: { value: 3.8 },
      intensity: { value: pantallaBrillo },
    };
    const capsuleMat = new THREE.ShaderMaterial({
      uniforms: capsuleUniforms,
      vertexShader: `
        varying vec3 vNormal;
        varying vec3 vViewPosition;
        void main() {
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          vViewPosition = -mvPosition.xyz;
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        uniform vec3 color;
        uniform float power;
        uniform float intensity;
        varying vec3 vNormal;
        varying vec3 vViewPosition;
        void main() {
          vec3 normal = normalize(vNormal);
          vec3 viewDir = normalize(vViewPosition);
          float fresnel = 1.0 - max(dot(viewDir, normal), 0.0);
          fresnel = pow(fresnel, power);
          gl_FragColor = vec4(color, fresnel * intensity);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const capsuleMesh = new THREE.Mesh(new THREE.SphereGeometry(0.3, 64, 64), capsuleMat);
    headGroup.add(capsuleMesh);

    // Eyes
    const { topPath, bottomPath } = createEyeCurves();
    const eyeMat = new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false, transparent: true });
    const heartMat = new THREE.MeshBasicMaterial({ color: 0xff3366, toneMapped: false });

    function createSingleEye(isLeft: boolean) {
      const eyeGroup = new THREE.Group();
      eyeGroup.position.set(isLeft ? -0.07 : 0.07, -0.02, 0.29);
      eyeGroup.rotation.set(0, isLeft ? -0.2 : 0.2, 0);

      const normalGroup = new THREE.Group();
      const topMesh = new THREE.Mesh(new THREE.TubeGeometry(topPath, 20, 0.0035, 8, false), eyeMat);
      const btmMesh = new THREE.Mesh(new THREE.TubeGeometry(bottomPath, 20, 0.0035, 8, false), eyeMat);
      normalGroup.add(topMesh, btmMesh);
      eyeGroup.add(normalGroup);

      const heartMesh = new THREE.Mesh(new THREE.TubeGeometry(sharedHeartCurve as any, 64, 0.0035, 8, true), heartMat);
      heartMesh.visible = false;
      eyeGroup.add(heartMesh);

      return { eyeGroup, normalGroup, heartMesh };
    }

    const leftEye = createSingleEye(true);
    const rightEye = createSingleEye(false);
    headGroup.add(leftEye.eyeGroup);
    headGroup.add(rightEye.eyeGroup);

    // Ears & Antennas
    const earBaseMat = new THREE.MeshStandardMaterial({ color: 0xf0f0f0, roughness: 0.5 });
    const earRingMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });
    const earCenterMat = new THREE.MeshStandardMaterial({ color: 0xcccccc, roughness: 0.8 });
    const antBaseMat = new THREE.MeshStandardMaterial({ color: 0x999999, roughness: 0.4, metalness: 0.5 });
    const antStickMat = new THREE.MeshStandardMaterial({ color: 0xd0d0d0, roughness: 0.4, metalness: 0.2 });
    const antTipMat = new THREE.MeshStandardMaterial({ color: 0xff3366, roughness: 0.2, toneMapped: false });

    function createEar(isLeft: boolean) {
      const g = new THREE.Group();
      const dir = isLeft ? -1 : 1;
      g.position.set(dir * 0.29, 0, 0);
      g.scale.setScalar(1.25);

      const base = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.025, 32), earBaseMat);
      base.rotation.z = Math.PI / 2;
      g.add(base);

      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.032, 0.008, 16, 32), earRingMat);
      ring.position.x = dir * 0.012;
      ring.rotation.z = Math.PI / 2;
      g.add(ring);

      const center = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.005, 32), earCenterMat);
      center.position.x = dir * 0.012;
      center.rotation.z = Math.PI / 2;
      g.add(center);

      const antGroup = new THREE.Group();
      antGroup.position.set(dir * 0.015, 0.035, 0);
      antGroup.rotation.x = -0.4;

      const aBase = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.008, 0.02, 16), antBaseMat);
      aBase.position.y = 0.01;
      antGroup.add(aBase);

      const aStick = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.003, 0.1, 8), antStickMat);
      aStick.position.y = 0.06;
      antGroup.add(aStick);

      const aTip = new THREE.Mesh(new THREE.SphereGeometry(0.006, 16, 16), antTipMat);
      aTip.position.y = 0.11;
      antGroup.add(aTip);

      g.add(antGroup);
      return g;
    }

    headGroup.add(createEar(true));
    headGroup.add(createEar(false));

    // --- Cursor & Movement Tracking Across the WHOLE SCREEN (ON THE GROUND) ---
    let pointer = { x: 0, y: 0 };
    let targetGroundPos = new THREE.Vector3(0, GROUND_Y + 0.43 * scale, 0);

    // Track input focus globally so typing state is 100% responsive
    let internalTyping = false;
    const onFocusIn = (e: FocusEvent) => {
      const target = e.target as HTMLElement | null;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.getAttribute("contenteditable") === "true")) {
        internalTyping = true;
      }
    };
    const onFocusOut = () => {
      internalTyping = false;
    };
    window.addEventListener("focusin", onFocusIn);
    window.addEventListener("focusout", onFocusOut);

    // Calculate ground coordinates to dock stably right beside the login card
    const getBesideCardPosition = (w: number, h: number) => {
      const cardEl = document.getElementById("login-card") || document.querySelector("form");
      if (cardEl) {
        const rect = cardEl.getBoundingClientRect();
        const isMobile = w < 768;
        // On desktop: dock ~135px to the left of the card border (beside the card)
        // On mobile: center on screen
        const targetScreenX = isMobile ? rect.left + rect.width * 0.5 : Math.max(90, rect.left - 135);
        const ndcX = (targetScreenX / w) * 2 - 1;
        const vFovRad = (camera.fov * Math.PI) / 180;
        const visibleHeightAtFloor = 2 * Math.tan(vFovRad / 2) * camera.position.z;
        const visibleWidthAtFloor = visibleHeightAtFloor * (w / h);
        const dockedX = ndcX * (visibleWidthAtFloor / 2);
        const dockedZ = isMobile ? 1.0 : 0.05;
        return { x: dockedX, z: dockedZ };
      }
      return { x: 0.6, z: 0.05 };
    };

    const updateFromCoords = (clientX: number, clientY: number) => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      pointer.x = (clientX / w) * 2 - 1;
      pointer.y = -((clientY / h) * 2 - 1);

      const activeTyping = isTypingRef.current || internalTyping;
      if (activeTyping) {
        // While typing in box: dock beside the box and do not follow mouse position
        const beside = getBesideCardPosition(w, h);
        targetGroundPos.x = beside.x;
        targetGroundPos.y = GROUND_Y + 0.43 * scale;
        targetGroundPos.z = beside.z;
        return;
      }

      // Frustum dimensions at ground plane distance
      const vFovRad = (camera.fov * Math.PI) / 180;
      const visibleHeightAtFloor = 2 * Math.tan(vFovRad / 2) * camera.position.z;
      const visibleWidthAtFloor = visibleHeightAtFloor * (w / h);

      // Move freely around the screen
      const maxGroundX = (visibleWidthAtFloor / 2) * 0.92;
      const mappedX = THREE.MathUtils.clamp(pointer.x * (visibleWidthAtFloor / 2) * 0.92, -maxGroundX, maxGroundX);

      // When moving behind the card (right side of screen), ensure depth is behind card (z <= -0.9)
      let mappedZ: number;
      if (pointer.x > 0.12) {
        mappedZ = Math.min(-0.9, -pointer.y * 1.5 - 0.4);
      } else {
        mappedZ = THREE.MathUtils.clamp(-pointer.y * 2.2, -2.4, 2.0);
      }

      targetGroundPos.x = mappedX;
      targetGroundPos.y = GROUND_Y + 0.43 * scale; // STRICTLY LOCKED ON GROUND!
      targetGroundPos.z = mappedZ;
    };

    const onPointerMove = (e: MouseEvent) => {
      updateFromCoords(e.clientX, e.clientY);
    };
    window.addEventListener("mousemove", onPointerMove);

    const onTouchMove = (e: TouchEvent) => {
      if (e.touches && e.touches.length > 0) {
        updateFromCoords(e.touches[0].clientX, e.touches[0].clientY);
      }
    };
    window.addEventListener("touchmove", onTouchMove, { passive: true });

    // Raycaster for click interaction on the robot anywhere on the screen
    const raycaster = new THREE.Raycaster();
    const mouseVec = new THREE.Vector2();

    const triggerHeartLove = () => {
      isLovedRef.current = true;
      setIsLovedState(true);
      if (loveTimeoutRef.current) clearTimeout(loveTimeoutRef.current);
      loveTimeoutRef.current = setTimeout(() => {
        isLovedRef.current = false;
        setIsLovedState(false);
      }, 2500);
      onRobotClick?.();
    };

    const onClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      // Do not intercept if user clicked on form inputs, buttons, or links
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "BUTTON" ||
          target.tagName === "A" ||
          target.closest("button") ||
          target.closest("input") ||
          target.closest("a"))
      ) {
        return;
      }

      const rect = renderer.domElement.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      mouseVec.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseVec.y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      raycaster.setFromCamera(mouseVec, camera);

      const intersects = raycaster.intersectObjects([bodyMesh, headMesh, capsuleMesh], true);
      if (intersects.length > 0) {
        triggerHeartLove();
      }
    };

    window.addEventListener("click", onClick);

    // Resize Handler
    const onResize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    // --- Animation Loop ---
    let reqId: number;
    let clock = new THREE.Clock();

    // Reusable 3D vector objects for gaze calculations (avoids GC allocations per frame)
    const mouseRayVec = new THREE.Vector3();
    const rayDir = new THREE.Vector3();
    const headWorldPos = new THREE.Vector3();
    const gazePoint = new THREE.Vector3();

    const animate = () => {
      reqId = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      const elapsed = clock.getElapsedTime();

      // Update target ground position if user is typing/focusing input
      const activeTyping = isTypingRef.current || internalTyping;
      if (activeTyping) {
        const w = window.innerWidth;
        const h = window.innerHeight;
        const beside = getBesideCardPosition(w, h);
        targetGroundPos.x = beside.x;
        targetGroundPos.z = beside.z;
      }

      // 1. Move Robot on the GROUND (X and Z only, Y is locked to ground!)
      const moveSpeed = activeTyping ? 5.5 : 4.5;
      robotRoot.position.x = THREE.MathUtils.lerp(robotRoot.position.x, targetGroundPos.x, moveSpeed * delta);
      robotRoot.position.z = THREE.MathUtils.lerp(robotRoot.position.z, targetGroundPos.z, moveSpeed * delta);
      robotRoot.position.y = GROUND_Y + 0.43; // Always on ground!

      // 2. Synchronize Contact Shadow and Floor Ring on the ground plane
      shadowMesh.position.x = robotRoot.position.x;
      shadowMesh.position.z = robotRoot.position.z;
      gridRing.position.x = robotRoot.position.x;
      gridRing.position.z = robotRoot.position.z;

      // 3. Body Banking/Leaning into Movement (stands stably upright when beside the box)
      const vx = targetGroundPos.x - robotRoot.position.x;
      const vz = targetGroundPos.z - robotRoot.position.z;
      const targetRoll = activeTyping ? 0 : -vx * 0.35;
      const targetPitch = activeTyping ? 0 : vz * 0.25;

      bodyGroup.rotation.z = THREE.MathUtils.lerp(bodyGroup.rotation.z, targetRoll, 8.0 * delta);
      bodyGroup.rotation.x = THREE.MathUtils.lerp(bodyGroup.rotation.x, targetPitch, 8.0 * delta);

      // Body gentle idle breathing bob (subtle 2mm bounce on ground)
      bodyGroup.position.y = Math.sin(elapsed * 2.5) * 0.012;

      // 4. Head & Face Following Cursor in 3D Space (Precision Gaze Tracking)
      headGroup.getWorldPosition(headWorldPos);

      // Unproject mouse cursor NDC to cast ray from camera through screen cursor
      mouseRayVec.set(pointer.x, pointer.y, 0.5).unproject(camera);
      rayDir.copy(mouseRayVec).sub(camera.position).normalize();

      // Find intersection with gaze plane in front of the robot towards camera
      const gazePlaneZ = Math.max(headWorldPos.z + 1.2, 1.2);
      const tRay = (gazePlaneZ - camera.position.z) / rayDir.z;
      gazePoint.copy(camera.position).addScaledVector(rayDir, tRay);

      // 3D vector from robot head to cursor
      const dx = gazePoint.x - headWorldPos.x;
      const dy = gazePoint.y - headWorldPos.y;
      const dz = gazePoint.z - headWorldPos.z;
      const distXZ = Math.hypot(dx, dz);

      // Yaw: positive when cursor is to the right -> head turns right
      const targetYaw = Math.atan2(dx, dz);
      // Pitch: negative when cursor is above -> face tilts up
      const targetPitchVal = -Math.atan2(dy, distXZ);

      // Clamping to natural physical neck mobility
      const clampedYaw = THREE.MathUtils.clamp(targetYaw, -1.2, 1.2);
      const clampedPitch = THREE.MathUtils.clamp(targetPitchVal, -0.65, 0.65);

      // Compensate for body roll and pitch so gaze is pure and locked onto cursor
      const compensatedPitch = clampedPitch - bodyGroup.rotation.x;
      const compensatedYaw = clampedYaw;

      headGroup.rotation.y = THREE.MathUtils.lerp(headGroup.rotation.y, compensatedYaw, 12.0 * delta);
      headGroup.rotation.x = THREE.MathUtils.lerp(headGroup.rotation.x, compensatedPitch, 12.0 * delta);

      // 5. Eye Blinking, Rotation & Pupil Tracking
      const isLoved = isLovedRef.current;
      leftEye.normalGroup.visible = !isLoved;
      rightEye.normalGroup.visible = !isLoved;
      leftEye.heartMesh.visible = isLoved;
      rightEye.heartMesh.visible = isLoved;

      // Eyes rotation and pupils shifting inside the visor to watch cursor
      const eyeYaw = THREE.MathUtils.clamp(compensatedYaw * 0.35, -0.28, 0.28);
      const eyePitch = THREE.MathUtils.clamp(-compensatedPitch * 0.35, -0.22, 0.22);

      leftEye.normalGroup.position.x = THREE.MathUtils.lerp(leftEye.normalGroup.position.x, eyeYaw * 0.012, 14.0 * delta);
      leftEye.normalGroup.position.y = THREE.MathUtils.lerp(leftEye.normalGroup.position.y, eyePitch * 0.012, 14.0 * delta);
      rightEye.normalGroup.position.x = THREE.MathUtils.lerp(rightEye.normalGroup.position.x, eyeYaw * 0.012, 14.0 * delta);
      rightEye.normalGroup.position.y = THREE.MathUtils.lerp(rightEye.normalGroup.position.y, eyePitch * 0.012, 14.0 * delta);

      leftEye.eyeGroup.rotation.y = THREE.MathUtils.lerp(leftEye.eyeGroup.rotation.y, -0.2 + eyeYaw * 0.45, 14.0 * delta);
      rightEye.eyeGroup.rotation.y = THREE.MathUtils.lerp(rightEye.eyeGroup.rotation.y, 0.2 + eyeYaw * 0.45, 14.0 * delta);
      leftEye.eyeGroup.rotation.x = THREE.MathUtils.lerp(leftEye.eyeGroup.rotation.x, compensatedPitch * 0.35, 14.0 * delta);
      rightEye.eyeGroup.rotation.x = THREE.MathUtils.lerp(rightEye.eyeGroup.rotation.x, compensatedPitch * 0.35, 14.0 * delta);

      const blinkCycle = 3.2;
      const blinkDuration = 0.16;
      const cycle = elapsed % blinkCycle;
      let targetScaleY = 1.0;

      if (cycle < blinkDuration && !isLoved) {
        const progress = cycle / blinkDuration;
        targetScaleY = Math.max(0.05, 1.0 - Math.sin(progress * Math.PI));
      }

      leftEye.eyeGroup.scale.set(1.1, 1.1 * targetScaleY, 1.1);
      rightEye.eyeGroup.scale.set(1.1, 1.1 * targetScaleY, 1.1);

      // Render
      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(reqId);
      window.removeEventListener("mousemove", onPointerMove);
      window.removeEventListener("touchmove", onTouchMove);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("click", onClick);
      window.removeEventListener("focusin", onFocusIn);
      window.removeEventListener("focusout", onFocusOut);
      if (loveTimeoutRef.current) clearTimeout(loveTimeoutRef.current);
      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
      colorMap.dispose();
      bumpMap.dispose();
      shadowTex.dispose();
    };
  }, [color, pantallaColor, pantallaBrillo, scale, theme, onRobotClick]);

  return (
    <div className={`relative w-full h-full select-none pointer-events-none ${className}`}>
      {/* Fullscreen 3D Canvas Mount Point */}
      <div ref={mountRef} className="w-full h-full" />
    </div>
  );
}

export default RobotCharacter;
