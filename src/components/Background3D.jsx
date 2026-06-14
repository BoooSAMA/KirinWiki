import { useEffect, useRef } from 'preact/hooks'
import { createScene, destroyScene } from '../lib/crystalScene'

export default function Background3D() {
  const containerRef = useRef(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    createScene(el)
    return () => destroyScene()
  }, [])

  return (
    <div
      ref={containerRef}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  )
}
