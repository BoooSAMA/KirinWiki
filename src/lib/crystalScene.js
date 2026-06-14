import * as THREE from 'three'

let scene, camera, renderer, container
let animationId, resizeHandler

const R = 500          // 星球曲率半径
const GRID_SIZE = 420  // 地板总尺寸
const DIVISIONS = 70   // 格线分割数
const SPACING = GRID_SIZE / DIVISIONS // 6 单位一格
const HALF = GRID_SIZE / 2
const CX = 3           // 中心偏移确保原点在瓷砖中心 (3%6=3)
const CZ = 3

function surfaceY(wx, wz) {
  const d2 = wx * wx + wz * wz
  return d2 >= R * R ? -R : Math.sqrt(R * R - d2) - R
}

function buildCurvedFloor() {
  const SEG = 120
  const positions = []
  const indices = []

  for (let j = 0; j <= SEG; j++) {
    const wz = CZ - HALF + (j / SEG) * GRID_SIZE
    for (let i = 0; i <= SEG; i++) {
      const wx = CX - HALF + (i / SEG) * GRID_SIZE
      positions.push(wx, surfaceY(wx, wz), wz)
    }
  }

  for (let j = 0; j < SEG; j++) {
    for (let i = 0; i < SEG; i++) {
      const a = j * (SEG + 1) + i
      const b = j * (SEG + 1) + i + 1
      const c = (j + 1) * (SEG + 1) + i
      const d = (j + 1) * (SEG + 1) + i + 1
      indices.push(a, b, c)
      indices.push(b, d, c)
    }
  }

  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  geo.setIndex(indices)
  geo.computeVertexNormals()

  return new THREE.Mesh(
    geo,
    new THREE.MeshBasicMaterial({ color: 0xf8f8f8, side: THREE.DoubleSide }),
  )
}

function buildCurvedGrid() {
  const group = new THREE.Group()
  const mat = new THREE.LineBasicMaterial({ color: 0xaaaaaa })
  const LINE_SEG = 40

  // X 向格线（沿 Z 方向排列）
  for (let d = 0; d <= DIVISIONS; d++) {
    const wz = CZ - HALF + d * SPACING
    const pts = []
    for (let s = 0; s <= LINE_SEG; s++) {
      const wx = CX - HALF + (s / LINE_SEG) * GRID_SIZE
      pts.push(new THREE.Vector3(wx, surfaceY(wx, wz), wz))
    }
    const geo = new THREE.BufferGeometry().setFromPoints(pts)
    group.add(new THREE.Line(geo, mat))
  }

  // Z 向格线（沿 X 方向排列）
  for (let d = 0; d <= DIVISIONS; d++) {
    const wx = CX - HALF + d * SPACING
    const pts = []
    for (let s = 0; s <= LINE_SEG; s++) {
      const wz = CZ - HALF + (s / LINE_SEG) * GRID_SIZE
      pts.push(new THREE.Vector3(wx, surfaceY(wx, wz), wz))
    }
    const geo = new THREE.BufferGeometry().setFromPoints(pts)
    group.add(new THREE.Line(geo, mat))
  }

  return group
}

export function createScene(el) {
  container = el

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xffffff)

  const aspect = container.clientWidth / container.clientHeight
  camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 200)
  camera.position.set(0, 5, -7)
  camera.lookAt(0, 4.39, 0)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(container.clientWidth, container.clientHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  container.appendChild(renderer.domElement)

  scene.add(buildCurvedFloor())
  scene.add(buildCurvedGrid())

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
