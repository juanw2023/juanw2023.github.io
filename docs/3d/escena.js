import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

// Two frames leave a paint opportunity for the HTML before WebGL setup.
function schedule() { requestAnimationFrame(() => requestAnimationFrame(start)); }
if (document.readyState === 'complete') schedule();
else window.addEventListener('load', schedule, { once: true });

async function start() {
  const canvas = document.createElement('canvas');
  canvas.className = 'scene';
  canvas.setAttribute('aria-hidden', 'true');
  let renderer, environment, texture, plane, glass, model;
  let frame = 0, previous = 0, baseY = 0;
  const dark = matchMedia('(prefers-color-scheme: dark)');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, .1, 100);
  camera.position.z = 8;
  const core = new THREE.Group();
  scene.add(core);
  const words = document.createElement('canvas');
  words.width = 2048;
  words.height = 1536;
  const context = words.getContext('2d');

  function disposeObject(object) {
    object?.traverse(node => {
      node.geometry?.dispose();
      for (const material of [].concat(node.material || [])) material.dispose();
    });
  }
  function cleanup() {
    cancelAnimationFrame(frame);
    window.removeEventListener('resize', resize);
    document.removeEventListener('visibilitychange', motion);
    dark.removeEventListener('change', recolor);
    reduced.removeEventListener('change', motion);
    disposeObject(model);
    disposeObject(plane);
    glass?.dispose();
    texture?.dispose();
    environment?.dispose();
    renderer?.dispose();
    canvas.remove();
  }
  function recolor() {
    context.fillStyle = dark.matches ? '#0F0F0F' : '#EBEAE8';
    context.fillRect(0, 0, words.width, words.height);
    context.fillStyle = dark.matches ? '#30302E' : '#C7C6C3';
    context.font = '900 230px Inter, sans-serif';
    context.textAlign = 'center';
    ['WONG CAVERO', '46098608', 'LIMA'].forEach((word, i) => {
      context.fillText(word, 1024, 510 + i * 290, 1980);
    });
    texture.needsUpdate = true;
    if (reduced.matches && !document.hidden) requestDraw();
  }
  function resize() {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    renderer.setSize(innerWidth, innerHeight);
    const height = 16 * Math.tan(THREE.MathUtils.degToRad(20));
    const width = height * camera.aspect;
    const mobile = innerWidth <= 600;
    core.position.x = width * (mobile ? .16 : .29);
    baseY = mobile ? -height * .15 : 0;
    core.position.y = baseY;
    core.scale.setScalar(mobile ? .48 : .95);
    plane.scale.set(width * 1.6, height * 1.6, 1);
    if (reduced.matches && !document.hidden) requestDraw();
  }
  function requestDraw() {
    if (!frame) frame = requestAnimationFrame(draw);
  }
  function draw(now) {
    frame = 0;
    const delta = previous ? Math.min((now - previous) / 1000, .1) : 0;
    previous = now;
    const range = document.documentElement.scrollHeight - innerHeight;
    const progress = reduced.matches ? 0 : THREE.MathUtils.clamp(scrollY / Math.max(1, range), 0, 1);
    core.rotation.y = THREE.MathUtils.damp(core.rotation.y, progress * Math.PI * 4, 2, delta);
    core.position.y = THREE.MathUtils.damp(core.position.y, baseY + progress * .3, 2, delta);
    plane.position.y = -progress * .35;
    renderer.render(scene, camera);
    if (!reduced.matches && !document.hidden) requestDraw();
  }
  function motion() {
    cancelAnimationFrame(frame);
    frame = 0;
    previous = 0;
    if (reduced.matches) {
      core.rotation.y = 0;
      core.position.y = baseY;
    }
    if (!document.hidden) requestDraw();
  }
  try {
    // Probe first: WebGLRenderer logs an error when WebGL is unavailable.
    const gl = canvas.getContext('webgl2', { alpha: true, antialias: true });
    if (!gl || !context) return;
    renderer = new THREE.WebGLRenderer({ canvas, context: gl, antialias: true, alpha: true });
    renderer.setClearColor(0x000000, 0);
    const pmrem = new THREE.PMREMGenerator(renderer);
    const room = new RoomEnvironment();
    environment = pmrem.fromScene(room, .04);
    scene.environment = environment.texture;
    room.dispose();
    pmrem.dispose();
    // Fetch/parse ourselves so a failed model never logs a loader error.
    const response = await fetch('/3d/nucleo.glb');
    if (!response.ok) throw new Error('Optional model unavailable');
    const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
    model = (await loader.parseAsync(await response.arrayBuffer(), '/3d/')).scene;
    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3());
    const extent = Math.max(size.x, size.y, size.z);
    if (!Number.isFinite(extent) || extent <= 0) throw new Error('Empty model');
    model.position.sub(box.getCenter(new THREE.Vector3()));
    const normalized = new THREE.Group();
    normalized.add(model);
    normalized.scale.setScalar(3.5 / extent);
    core.add(normalized);
    glass = new THREE.MeshPhysicalMaterial({ color: 0xffffff, transmission: 1, thickness: 1.2,
      roughness: .08, ior: 1.5, iridescence: .4, dispersion: 4 });
    model.traverse(node => {
      if (node.isMesh) {
        for (const material of [].concat(node.material || [])) material.dispose();
        node.material = glass;
      }
    });
    await document.fonts.ready;
    texture = new THREE.CanvasTexture(words);
    texture.colorSpace = THREE.SRGBColorSpace;
    plane = new THREE.Mesh(new THREE.PlaneGeometry(1, 1),
      new THREE.MeshBasicMaterial({ map: texture }));
    plane.position.z = -2.5;
    scene.add(plane);
    recolor();
    resize();
    document.body.prepend(canvas);
    window.addEventListener('resize', resize);
    document.addEventListener('visibilitychange', motion);
    dark.addEventListener('change', recolor);
    reduced.addEventListener('change', motion);
    canvas.addEventListener('webglcontextlost', cleanup, { once: true });
    motion();
  } catch {
    cleanup();
  }
}
