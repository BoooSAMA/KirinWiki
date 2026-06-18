import * as THREE from 'three'

let scene, camera, renderer, container, envScene
let animationId, resizeHandler, crystal
let floorMesh, hexGrid
let cameraTarget = new THREE.Vector3(2, 5, 5.87)

const R = 500         // 星球曲率半径
const GRID_SIZE = 420 // 地板总尺寸
const HALF = GRID_SIZE / 2
const CX = 3
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

function buildHexGrid() {
  const hexSize = 4
  const colSpacing = 1.5 * hexSize        // 6
  const rowSpacing = Math.sqrt(3) * hexSize // ~6.928
  const rowOffset = rowSpacing / 2          // ~3.464
  const halfH = rowSpacing / 2
  const halfW = hexSize

  const margin = 40
  const xMin = CX - HALF - margin
  const xMax = CX + HALF + margin
  const zMin = CZ - HALF - margin
  const zMax = CZ + HALF + margin

  const cols = Math.ceil((xMax - xMin) / colSpacing) + 2
  const rows = Math.ceil((zMax - zMin) / rowSpacing) + 2

  const drawnEdges = new Set()
  const positions = []

  function edgeKey(ax, az, bx, bz) {
    const ak = `${ax.toFixed(2)},${az.toFixed(2)}`
    const bk = `${bx.toFixed(2)},${bz.toFixed(2)}`
    return ak < bk ? `${ak}-${bk}` : `${bk}-${ak}`
  }

  function addEdge(ax, ay, az, bx, by, bz) {
    const key = edgeKey(ax, az, bx, bz)
    if (!drawnEdges.has(key)) {
      drawnEdges.add(key)
      positions.push(ax, ay, az, bx, by, bz)
    }
  }

  for (let col = 0; col < cols; col++) {
    const cx = xMin + col * colSpacing
    const zOff = (col % 2 === 1) ? rowOffset : 0

    for (let row = 0; row < rows; row++) {
      const cz = zMin + row * rowSpacing + zOff

      // flat-top hexagon 6 顶点（顺时针）
      const vx = [
        cx + halfW,          // 右
        cx + halfW / 2,      // 右下
        cx - halfW / 2,      // 左下
        cx - halfW,          // 左
        cx - halfW / 2,      // 左上
        cx + halfW / 2,      // 右上
      ]
      const vz = [
        cz,
        cz + halfH,
        cz + halfH,
        cz,
        cz - halfH,
        cz - halfH,
      ]

      for (let v = 0; v < 6; v++) {
        const w = (v + 1) % 6
        const vy1 = surfaceY(vx[v], vz[v])
        const vy2 = surfaceY(vx[w], vz[w])
        addEdge(vx[v], vy1, vz[v], vx[w], vy2, vz[w])
      }
    }
  }

  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  return new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ color: 0xaaaaaa }))
}

export function createScene(el) {
  container = el

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xffffff)

  const aspect = container.clientWidth / container.clientHeight
  camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 200)
  camera.position.set(12, 7.5, 6)
  cameraTarget.set(2, 5, 5.87)
  camera.lookAt(cameraTarget)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(container.clientWidth, container.clientHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  container.appendChild(renderer.domElement)

  // 生成环境贴图，让金属材质有东西可反射
  const pmrem = new THREE.PMREMGenerator(renderer)
  envScene = new THREE.Scene()
  envScene.background = new THREE.Color(0xf5f5f5)
  scene.environment = pmrem.fromScene(envScene).texture
  pmrem.dispose()

  let __lastBgHex = null
  window.__setSceneBackground = (hex) => {
    if (!scene || !renderer || hex === __lastBgHex) return
    __lastBgHex = hex

    const color = new THREE.Color(hex)
    scene.background = color

    if (envScene) {
      envScene.background = color
      const pmrem2 = new THREE.PMREMGenerator(renderer)
      scene.environment = pmrem2.fromScene(envScene).texture
      pmrem2.dispose()
    }

    // 根据背景色亮度同步调整地板和网格线颜色
    const r = parseInt(hex.slice(1, 3), 16) / 255
    const g = parseInt(hex.slice(3, 5), 16) / 255
    const b = parseInt(hex.slice(5, 7), 16) / 255
    const bgBrightness = 0.299 * r + 0.587 * g + 0.114 * b
    // 地板: 白天接近 0xf8f8f8, 夜晚最低 0x1a1a1a
    const floorFrac = 0.1 + bgBrightness * 0.87
    // 网格: 白天接近 0xaaaaaa, 夜晚最低 0x404040
    const gridFrac = 0.25 + bgBrightness * 0.42

    const fv = Math.round(floorFrac * 255)
    const gv = Math.round(gridFrac * 255)

    if (floorMesh) {
      floorMesh.material.color.setRGB(fv / 255, fv / 255, fv / 255)
    }
    if (hexGrid) {
      hexGrid.material.color.setRGB(gv / 255, gv / 255, gv / 255)
    }
  }

  floorMesh = buildCurvedFloor()
  hexGrid = buildHexGrid()
  scene.add(floorMesh)
  scene.add(hexGrid)

  // 灯光
  scene.add(new THREE.AmbientLight(0xffffff, 0.4))
  const sun = new THREE.DirectionalLight(0xffffff, 1.8)
  sun.position.set(5, 10, 7)
  scene.add(sun)
  const fill = new THREE.DirectionalLight(0xffffff, 0.5)
  fill.position.set(-4, 2, -5)
  scene.add(fill)

  // 银色金属水晶（末影水晶风格），位置摆远一格，拉高 2×
  const outerMat = new THREE.MeshStandardMaterial({
    color: 0xd0d0d0,
    metalness: 0.85,
    roughness: 0.1,
  })
  const outer = new THREE.Mesh(new THREE.OctahedronGeometry(1.6, 0), outerMat)
  outer.scale.y = 2
  outer.position.set(-1, 4.5, 5.872)
  scene.add(outer)

  const innerMat = new THREE.MeshStandardMaterial({
    color: 0xf0f0f0,
    metalness: 0.95,
    roughness: 0.0,
  })
  const inner = new THREE.Mesh(new THREE.OctahedronGeometry(0.85, 0), innerMat)
  inner.rotation.y = Math.PI / 4
  outer.add(inner)

  crystal = outer

  const shadowCanvas = document.createElement('canvas')
  shadowCanvas.width = 128
  shadowCanvas.height = 128
  const sCtx = shadowCanvas.getContext('2d')
  const grad = sCtx.createRadialGradient(64, 64, 0, 64, 64, 64)
  grad.addColorStop(0, 'rgba(0,0,0,0.7)')
  grad.addColorStop(0.5, 'rgba(0,0,0,0.25)')
  grad.addColorStop(1, 'rgba(0,0,0,0)')
  sCtx.fillStyle = grad
  sCtx.fillRect(0, 0, 128, 128)

  const shadowTex = new THREE.CanvasTexture(shadowCanvas)
  const shadow = new THREE.Mesh(
    new THREE.PlaneGeometry(2.5, 2.5),
    new THREE.MeshBasicMaterial({
      map: shadowTex,
      transparent: true,
      opacity: 0.65,
      depthWrite: false,
    }),
  )
  shadow.rotation.x = -Math.PI / 2
  shadow.position.set(-1, surfaceY(-1, 5.872) + 0.02, 5.872)
  scene.add(shadow)

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
    if (crystal) {
      const t = performance.now() / 1000
      const floatOffset = Math.sin(t * 0.7)
      crystal.rotation.y += 0.008
      crystal.position.y = 4.5 + floatOffset * 0.25
      shadow.scale.setScalar(1 + floatOffset * 0.2)
      shadow.material.opacity = 0.65 - floatOffset * 0.2
    }
    renderer.render(scene, camera)

    // Expose camera state for the debug panel (read by FPS monitor)
    window.__cameraState = {
      pos: { x: camera.position.x, y: camera.position.y, z: camera.position.z },
      look: { x: cameraTarget.x, y: cameraTarget.y, z: cameraTarget.z },
    }
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

  window.__cameraState = null
  renderer.dispose()
  container.removeChild(renderer.domElement)

  scene = null
  camera = null
  renderer = null
  container = null
}
