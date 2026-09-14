import { useLayoutEffect, useMemo, useRef } from 'react'
import { useFrame, type ThreeEvent } from '@react-three/fiber'
import * as THREE from 'three'
import type { FieldHealth } from '@/hooks/useFieldHealth'

interface AgroTreeProps {
  health: FieldHealth
  reducedMotion: boolean
  /** Horizontal stage offset (world units) — subtracted from raycast hits so bloom lands correctly. */
  stageOffset: number
}

/** Deterministic PRNG so the tree is identical on every load (no Math.random in render). */
function mulberry32(seed: number): () => number {
  return () => {
    seed |= 0
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const LEAF_COUNT = 650
const FLOWER_COUNT = 80
const PETAL_COUNT = 14
const BLOOM_RADIUS = 1.7
const CANOPY_Y = 3.1

const BUD_COLOR = new THREE.Color('#5f7031')
const BLOOM_COLOR = new THREE.Color('#f9a8d4')
const STRESS_TINT = new THREE.Color('#8a7a4f')
const TMP_COLOR = new THREE.Color()
const TMP_DUMMY = new THREE.Object3D()
const UP = new THREE.Vector3(0, 1, 0)

interface Branch {
  position: [number, number, number]
  quaternion: THREE.Quaternion
  length: number
  tip: THREE.Vector3
  rTop: number
  rBottom: number
}

function growBranches(rand: () => number, count: number, baseY: number, ySpread: number, tiltMin: number, tiltMax: number, lenMin: number, lenMax: number, rTop: number, rBottom: number, phase: number): Branch[] {
  const list: Branch[] = []
  for (let i = 0; i < count; i++) {
    const angle = (i / count) * Math.PI * 2 + phase + rand() * 0.5
    const tilt = tiltMin + rand() * (tiltMax - tiltMin)
    const dir = new THREE.Vector3(
      Math.cos(angle) * Math.sin(tilt),
      Math.cos(tilt),
      Math.sin(angle) * Math.sin(tilt)
    ).normalize()
    const base = new THREE.Vector3(0, baseY + (i % 3) * ySpread, 0)
    const length = lenMin + rand() * (lenMax - lenMin)
    const mid = base.clone().addScaledVector(dir, length / 2)
    list.push({
      position: [mid.x, mid.y, mid.z],
      quaternion: new THREE.Quaternion().setFromUnitVectors(UP, dir),
      length,
      tip: base.clone().addScaledVector(dir, length),
      rTop,
      rBottom,
    })
  }
  return list
}

/**
 * Procedural botanical tree (placeholder for a production GLB).
 *
 * To use a real model: replace the trunk/branch/leaf meshes below with
 * `<primitive object={glb.scene} />` (useGLTF) and attach flower anchors to
 * named bud nodes — the bloom/health logic in useFrame stays the same.
 */
export default function AgroTree({ health, reducedMotion, stageOffset }: AgroTreeProps) {
  const canopyRef = useRef<THREE.Group>(null!)
  const leavesRef = useRef<THREE.InstancedMesh>(null!)
  const flowersRef = useRef<THREE.InstancedMesh>(null!)
  const petalsRef = useRef<THREE.InstancedMesh>(null!)
  const bloom = useRef<Float32Array>(new Float32Array(FLOWER_COUNT))
  const bloomCenter = useRef<THREE.Vector3>(new THREE.Vector3())
  const bloomActive = useRef(false)

  const trunkProfile = useMemo(
    () => [
      new THREE.Vector2(0.42, 0),
      new THREE.Vector2(0.34, 0.18),
      new THREE.Vector2(0.32, 0.6),
      new THREE.Vector2(0.27, 1.1),
      new THREE.Vector2(0.22, 1.6),
      new THREE.Vector2(0.17, 2.0),
      new THREE.Vector2(0.12, 2.25),
    ],
    []
  )

  const branches = useMemo(() => {
    const rand = mulberry32(7)
    return [
      ...growBranches(rand, 6, 1.1, 0.3, 0.55, 0.8, 1.0, 1.45, 0.045, 0.085, 0),
      ...growBranches(rand, 4, 1.85, 0.25, 0.35, 0.55, 0.7, 1.0, 0.03, 0.06, 0.8),
    ]
  }, [])

  const leafData = useMemo(() => {
    const rand = mulberry32(21)
    const positions = new Float32Array(LEAF_COUNT * 3)
    const colors = new Float32Array(LEAF_COUNT * 3)
    const c = new THREE.Color()
    for (let i = 0; i < LEAF_COUNT; i++) {
      const u = rand() * 2 - 1
      const a = rand() * Math.PI * 2
      const s = Math.sqrt(1 - u * u)
      // Spreading canopy: dense outer shell + sparse inner fill for depth
      const outer = i % 4 !== 0
      const shell = outer ? 0.72 + rand() * 0.28 : 0.4 + rand() * 0.3
      positions[i * 3] = s * Math.cos(a) * 1.7 * shell
      positions[i * 3 + 1] = CANOPY_Y + u * 0.95 * shell
      positions[i * 3 + 2] = s * Math.sin(a) * 1.7 * shell
      if (outer) {
        c.setHSL(0.27 + rand() * 0.07, 0.42 + rand() * 0.14, 0.26 + rand() * 0.1)
      } else {
        c.setHSL(0.24 + rand() * 0.08, 0.5 + rand() * 0.15, 0.38 + rand() * 0.12)
      }
      colors[i * 3] = c.r
      colors[i * 3 + 1] = c.g
      colors[i * 3 + 2] = c.b
    }
    return { positions, colors }
  }, [])

  const flowerData = useMemo(() => {
    const rand = mulberry32(99)
    const tips = branches.map((b) => b.tip)
    const arr: { pos: THREE.Vector3; phase: number }[] = []
    for (let i = 0; i < FLOWER_COUNT; i++) {
      if (i % 4 === 3) {
        // A few lone blossoms on the canopy surface for coverage
        const u = rand() * 2 - 1
        const a = rand() * Math.PI * 2
        const s = Math.sqrt(1 - u * u)
        const shell = 0.9 + rand() * 0.18
        arr.push({
          pos: new THREE.Vector3(
            s * Math.cos(a) * 1.7 * shell,
            CANOPY_Y + u * 0.95 * shell,
            s * Math.sin(a) * 1.7 * shell
          ),
          phase: rand() * Math.PI * 2,
        })
      } else {
        // Clustered like real mango panicles around branch tips, pushed toward the light
        const tip = tips[i % tips.length]
        const outward = tip.clone().setY(0).normalize().multiplyScalar(0.28)
        arr.push({
          pos: new THREE.Vector3(
            tip.x + outward.x + (rand() + rand() + rand() - 1.5) * 0.36,
            tip.y + (rand() + rand() + rand() - 1.5) * 0.36,
            tip.z + outward.z + (rand() + rand() + rand() - 1.5) * 0.36
          ),
          phase: rand() * Math.PI * 2,
        })
      }
    }
    return arr
  }, [branches])

  const petalData = useMemo(() => {
    const rand = mulberry32(140)
    return Array.from({ length: PETAL_COUNT }, () => ({
      x: (rand() * 2 - 1) * 2.6,
      z: (rand() * 2 - 1) * 2.6,
      speed: 0.7 + rand() * 0.6,
      phase: rand() * Math.PI * 2,
      yOff: rand() * 5.2,
    }))
  }, [])

  // Static matrices (set once)
  useLayoutEffect(() => {
    const leaves = leavesRef.current
    if (leaves) {
      for (let i = 0; i < LEAF_COUNT; i++) {
        TMP_DUMMY.position.set(
          leafData.positions[i * 3],
          leafData.positions[i * 3 + 1],
          leafData.positions[i * 3 + 2]
        )
        TMP_DUMMY.rotation.set((((i * 13) % 7) / 7) * 1.4, (i * 2.399963) % (Math.PI * 2), 0)
        TMP_DUMMY.scale.setScalar(0.55 + (((i * 37) % 10) / 10) * 0.75)
        TMP_DUMMY.updateMatrix()
        leaves.setMatrixAt(i, TMP_DUMMY.matrix)
      }
      leaves.instanceMatrix.needsUpdate = true
    }
    const flowerMesh = flowersRef.current
    if (flowerMesh) {
      for (let i = 0; i < FLOWER_COUNT; i++) {
        TMP_DUMMY.position.copy(flowerData[i].pos)
        TMP_DUMMY.rotation.set(0, 0, 0)
        TMP_DUMMY.scale.setScalar(0.4)
        TMP_DUMMY.updateMatrix()
        flowerMesh.setMatrixAt(i, TMP_DUMMY.matrix)
        flowerMesh.setColorAt(i, BUD_COLOR)
      }
      flowerMesh.instanceMatrix.needsUpdate = true
      if (flowerMesh.instanceColor) flowerMesh.instanceColor.needsUpdate = true
    }
    const petalMesh = petalsRef.current
    if (petalMesh) {
      for (let i = 0; i < PETAL_COUNT; i++) {
        TMP_DUMMY.position.set(petalData[i].x, 2.4, petalData[i].z)
        TMP_DUMMY.rotation.set(0, 0, 0)
        TMP_DUMMY.scale.setScalar(1)
        TMP_DUMMY.updateMatrix()
        petalMesh.setMatrixAt(i, TMP_DUMMY.matrix)
      }
      petalMesh.instanceMatrix.needsUpdate = true
    }
  }, [leafData, flowerData, petalData])

  // Leaf health tint (re-applied when farm health changes)
  useLayoutEffect(() => {
    const leaves = leavesRef.current
    if (!leaves) return
    for (let i = 0; i < LEAF_COUNT; i++) {
      TMP_COLOR.setRGB(leafData.colors[i * 3], leafData.colors[i * 3 + 1], leafData.colors[i * 3 + 2])
      TMP_COLOR.lerp(STRESS_TINT, (1 - health.vibrance) * 0.55)
      leaves.setColorAt(i, TMP_COLOR)
    }
    if (leaves.instanceColor) leaves.instanceColor.needsUpdate = true
  }, [leafData, health.vibrance])

  useFrame((state, dt) => {
    const t = state.clock.elapsedTime
    const amp = reducedMotion ? 0 : health.sway

    if (canopyRef.current) {
      canopyRef.current.rotation.z = Math.sin(t * 0.5) * 0.02 * amp
      canopyRef.current.rotation.x = Math.cos(t * 0.4) * 0.012 * amp
      canopyRef.current.position.y = Math.sin(t * 0.8) * 0.03 * amp
    }

    const mesh = flowersRef.current
    if (mesh) {
      const k = 1 - Math.exp(-dt * 4)
      for (let i = 0; i < FLOWER_COUNT; i++) {
        const f = flowerData[i]
        let target = 0.16 * health.bloomCeiling
        if (!reducedMotion) {
          // Gentle idle breathing + a slow invitation wave so the interaction is discoverable
          target += Math.sin(t * 1.2 + f.phase) * 0.03
          const wave = Math.sin(t * 0.5 - f.pos.x * 1.2)
          if (wave > 0) target += wave * wave * wave * 0.22 * health.bloomCeiling
        }
        if (bloomActive.current) {
          const dx = f.pos.x - bloomCenter.current.x
          const dy = f.pos.y - bloomCenter.current.y
          const dz = f.pos.z - bloomCenter.current.z
          const d = Math.sqrt(dx * dx + dy * dy + dz * dz)
          const fall = Math.max(0, 1 - d / BLOOM_RADIUS)
          target = Math.min(health.bloomCeiling, Math.pow(fall, 1.5) * 1.2)
        }
        const b = bloom.current[i] + (target - bloom.current[i]) * k
        bloom.current[i] = b
        TMP_DUMMY.position.copy(f.pos)
        TMP_DUMMY.scale.setScalar(Math.max(0.001, 0.45 + b * 1.6))
        TMP_DUMMY.rotation.set(0, f.phase + (reducedMotion ? 0 : t * 0.15 * b), 0)
        TMP_DUMMY.updateMatrix()
        mesh.setMatrixAt(i, TMP_DUMMY.matrix)
        TMP_COLOR.copy(BUD_COLOR).lerp(BLOOM_COLOR, Math.min(1, Math.max(0, b)))
        mesh.setColorAt(i, TMP_COLOR)
      }
      mesh.instanceMatrix.needsUpdate = true
      if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true
    }

    const petals = petalsRef.current
    if (petals && !reducedMotion) {
      for (let i = 0; i < PETAL_COUNT; i++) {
        const p = petalData[i]
        const y = 4.8 - ((t * 0.3 * p.speed + p.yOff) % 5.4)
        TMP_DUMMY.position.set(p.x + Math.sin(t * 0.7 + p.phase) * 0.35, y, p.z)
        TMP_DUMMY.rotation.set(t * 0.6 + p.phase, p.phase, 0)
        TMP_DUMMY.scale.setScalar(1)
        TMP_DUMMY.updateMatrix()
        petals.setMatrixAt(i, TMP_DUMMY.matrix)
      }
      petals.instanceMatrix.needsUpdate = true
    }
  })

  const handlePointerMove = (e: ThreeEvent<PointerEvent>) => {
    // Interaction shell lives in the offset stage group — convert to tree-local coords
    bloomCenter.current.copy(e.point)
    bloomCenter.current.x -= stageOffset
    bloomActive.current = true
  }

  const handlePointerOut = () => {
    bloomActive.current = false
  }

  return (
    <group>
      {/* Trunk with organic taper + root flare */}
      <mesh position={[0, 0, 0]} rotation={[0, 0, 0.03]}>
        <latheGeometry args={[trunkProfile, 12]} />
        <meshStandardMaterial color="#6b4a30" roughness={1} />
      </mesh>

      {/* Swaying canopy: branches + leaves + blossoms + drifting petals */}
      <group ref={canopyRef}>
        {branches.map((b, i) => (
          <mesh key={i} position={b.position} quaternion={b.quaternion}>
            <cylinderGeometry args={[b.rTop, b.rBottom, b.length, 7]} />
            <meshStandardMaterial color="#75553a" roughness={1} />
          </mesh>
        ))}

        <instancedMesh ref={leavesRef} args={[undefined, undefined, LEAF_COUNT]}>
          <icosahedronGeometry args={[0.13, 1]} />
          <meshStandardMaterial roughness={0.9} />
        </instancedMesh>

        <instancedMesh ref={flowersRef} args={[undefined, undefined, FLOWER_COUNT]}>
          <sphereGeometry args={[0.14, 14, 14]} />
          <meshStandardMaterial roughness={0.55} emissive="#571b3a" emissiveIntensity={0.3} />
        </instancedMesh>

        <instancedMesh ref={petalsRef} args={[undefined, undefined, PETAL_COUNT]}>
          <circleGeometry args={[0.05, 8]} />
          <meshStandardMaterial
            color="#f6d9b8"
            roughness={0.8}
            transparent
            opacity={0.6}
            side={THREE.DoubleSide}
          />
        </instancedMesh>

        {/* Transparent (raycastable) interaction shell — cursor blooms nearby buds only */}
        <mesh
          position={[0, CANOPY_Y, 0]}
          onPointerMove={handlePointerMove}
          onPointerOut={handlePointerOut}
        >
          <sphereGeometry args={[2.5, 12, 12]} />
          <meshBasicMaterial transparent opacity={0} depthWrite={false} />
        </mesh>
      </group>
    </group>
  )
}
