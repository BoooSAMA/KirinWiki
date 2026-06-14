import * as THREE from 'three'

let scene, camera, renderer, container
let animationId, resizeHandler

export function createScene(el) {
  container = el

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xffffff)

  const aspect = container.clientWidth / container.clientHeight
  camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 100)
  camera.position.set(0, 5, -7) // 降一格 (4)，5° 俯视
  camera.lookAt(0, 4.39, 0) // 7*tan(5°) ≈ 0.61

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(container.clientWidth, container.clientHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  container.appendChild(renderer.domElement)

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(80, 80),
    new THREE.MeshBasicMaterial({ color: 0xf8f8f8, side: THREE.DoubleSide }),
  )
  floor.rotation.x = -Math.PI / 2
  floor.position.set(6, -0.01, 6)
  scene.add(floor)

  const grid = new THREE.GridHelper(80, 20, 0xaaaaaa, 0xaaaaaa)
  grid.position.set(6, 0, 6)
  scene.add(grid)

  resizeHandler = () => {
    const w = container.clientWidth
    const h = container.clientHeight
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    renderer.setSize(w, h)
  }
  window.addEventListener('resize', resizeHandler)

  function animate() {
    animationId = requestAnimationFrame(animate)
    renderer.render(scene, camera)
  }
  animate()
}

export function destroyScene() {
  if (!container) return

  cancelAnimationFrame(animationId)
  window.removeEventListener('resize', resizeHandler)

  scene.traverse((obj) => {
    if (obj.isMesh || obj.isLineSegments || obj.isLine) {
      obj.geometry?.dispose()
      if (Array.isArray(obj.material)) {
        obj.material.forEach(m => m.dispose())
      } else {
        obj.material?.dispose()
      }
    }
  })

  renderer.dispose()
  container.removeChild(renderer.domElement)

  scene = null
  camera = null
  renderer = null
  container = null
}
