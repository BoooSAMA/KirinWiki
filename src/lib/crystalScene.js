import * as THREE from 'three'

let scene, camera, renderer, container
let animationId, resizeHandler

export function createScene(el) {
  container = el

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xffffff)

  const aspect = container.clientWidth / container.clientHeight
  camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 100)
  camera.position.set(0, 2.5, -7) // 底部中线，20° 俯视；格线横平竖直
  camera.lookAt(0, 0, 0)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(container.clientWidth, container.clientHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  container.appendChild(renderer.domElement)

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(40, 40),
    new THREE.MeshBasicMaterial({ color: 0xf8f8f8, side: THREE.DoubleSide }),
  )
  floor.rotation.x = -Math.PI / 2
  floor.position.y = -0.01 // 微下沉避免与格线 z-fighting
  scene.add(floor)

  const grid = new THREE.GridHelper(40, 10, 0xaaaaaa, 0xaaaaaa)
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
