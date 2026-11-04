// Cambia la imagen de cada .escena[data-modelo] por su modelo 3D cuando entra en pantalla.
// Con «reducir movimiento» o sin WebGL se queda la imagen, que ya es el modelo renderizado.
const quieto = matchMedia("(prefers-reduced-motion: reduce)").matches;
const conWebGL = (() => {
  try {
    return Boolean(document.createElement("canvas").getContext("webgl2"));
  } catch {
    return false;
  }
})();
const raton = matchMedia("(pointer: fine)").matches;
const escenas = [...document.querySelectorAll(".escena[data-modelo]")];
const visores = [];
let visor;

// Mismo ángulo que la imagen renderizada, más el desplazamiento del cursor.
function orbita(escena, giro = 0, altura = 0) {
  const [base, inclinacion] = escena.dataset.orbita.split(" ").map(Number);
  return `${base + giro}deg ${inclinacion + altura}deg auto`;
}

function montar(escena) {
  const imagen = escena.querySelector("img");
  const modelo = document.createElement("model-viewer");
  const atributos = {
    src: escena.dataset.modelo, alt: imagen.alt, "environment-image": "neutral", exposure: "1.2",
    "camera-orbit": orbita(escena), "auto-rotate-delay": "0",
    "interaction-prompt": "none", "disable-zoom": "", "disable-pan": "", "interpolation-decay": "120",
  };
  // Con ratón el modelo sigue al cursor (como el Hero3D original); en pantallas táctiles gira solo.
  Object.assign(atributos, raton ? {} : { "auto-rotate": "", "camera-controls": "", "touch-action": "pan-y" });
  for (const [nombre, valor] of Object.entries(atributos)) modelo.setAttribute(nombre, valor);
  modelo.setAttribute("aria-hidden", "true");
  modelo.addEventListener("load", () => escena.classList.add("listo"), { once: true });
  escena.append(modelo);
  visores.push(modelo);
}

if (escenas.length && conWebGL && !quieto) {
  const observador = new IntersectionObserver((entradas) => {
    for (const { isIntersecting, target } of entradas) {
      if (!isIntersecting) continue;
      observador.unobserve(target);
      visor ??= import("/vendor/model-viewer/model-viewer.min.js");
      visor.then(() => montar(target));
    }
  }, { rootMargin: "200px" });
  escenas.forEach((escena) => observador.observe(escena));

  if (raton) {
    let pendiente = false;
    addEventListener("pointermove", ({ clientX, clientY }) => {
      if (pendiente) return;
      pendiente = true;
      requestAnimationFrame(() => {
        pendiente = false;
        const giro = (clientX / innerWidth - 0.5) * 50;
        const altura = (clientY / innerHeight - 0.5) * 20;
        for (const modelo of visores) modelo.cameraOrbit = orbita(modelo.parentElement, giro, altura);
      });
    }, { passive: true });
  }
}
