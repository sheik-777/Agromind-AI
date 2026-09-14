import { useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { ContactShadows, OrbitControls } from '@react-three/drei'
import AgroTree from './AgroTree'
import type { FieldHealth } from '@/hooks/useFieldHealth'

interface TreeCanvasProps {
  health: FieldHealth
  reducedMotion: boolean
}

function webglAvailable(): boolean {
  try {
    const c = document.createElement('canvas')
    return !!(
      window.WebGLRenderingContext &&
      (c.getContext('webgl2') || c.getContext('webgl') || c.getContext('experimental-webgl'))
    )
  } catch {
    return false
  }
}

function WebGLFallback() {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-3 px-6 text-center">
      <span className="text-5xl" role="img" aria-label="Tree">
        🌳
      </span>
      <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
        3D is unavailable on this device
      </p>
      <p className="max-w-xs text-xs text-neutral-500 dark:text-neutral-400">
        AgroMind works fully without it — your soil analysis, recommendations and assistant are unaffected.
      </p>
    </div>
  )
}

export default function TreeCanvas({ health, reducedMotion }: TreeCanvasProps) {
  const [supported] = useState(webglAvailable)
  const [viewport] = useState(() =>
    typeof window !== 'undefined'
      ? { wide: window.innerWidth >= 1024, narrow: window.innerWidth < 768 }
      : { wide: true, narrow: false }
  )

  if (!supported) return <WebGLFallback />

  // On desktop the tree lives well right-of-center so copy never collides; on mobile it centers behind.
  const offsetX = viewport.wide ? 4.0 : 0
  const cameraPosition: [number, number, number] = viewport.narrow
    ? [7.4, 4.6, 10.2]
    : [5.6, 3.4, 7.8]

  return (
    <Canvas
      dpr={[1, 1.75]}
      camera={{ position: cameraPosition, fov: 38 }}
      gl={{ antialias: true, alpha: true }}
      aria-label="Interactive 3D farm tree. Drag to orbit, scroll to zoom."
    >
      <ambientLight intensity={0.5} />
      <hemisphereLight args={['#eaf5ec', '#8a6b4f', 0.4]} />
      {/* Warm cinematic key */}
      <directionalLight position={[5, 8, 4]} intensity={1.25} color="#fff1dd" />
      {/* Cool rim for leaf separation */}
      <directionalLight position={[-6, 3.5, -5]} intensity={0.55} color="#cfe4ff" />

      <group position={[offsetX, 0, 0]}>
        <AgroTree health={health} reducedMotion={reducedMotion} stageOffset={offsetX} />
        <ContactShadows position={[0, 0.01, 0]} opacity={0.45} scale={10} blur={2.6} far={4} color="#1a2b1f" />
      </group>

      <OrbitControls
        makeDefault
        target={[offsetX, 2.1, 0]}
        enableDamping
        dampingFactor={0.08}
        enablePan={false}
        minDistance={4.5}
        maxDistance={13}
        minPolarAngle={0.55}
        maxPolarAngle={1.52}
      />
    </Canvas>
  )
}
