(() => {
  "use strict";

  const API = "/api/registro";
  const $ = (id) => document.getElementById(id);
  const form = $("form-registro");
  const avisos = $("avisos");
  const btn = $("btn-enviar");
  let temporizador = null;

  // ───────── Credencial en vivo ─────────
  const esUco = () => form.elements.tipo.value === "uco";

  function actualizarCredencial() {
    const nombre = `${$("nombre").value} ${$("apellidos").value}`.trim();
    $("cred-nombre").textContent = nombre || "Tu nombre aparecerá aquí";
    $("cred-email").textContent = $("email").value.trim() || "—";
    $("cred-acred").textContent = esUco() ? ($("acreditacion").value.trim().toUpperCase() || "—") : "No aplica";
    const sello = $("cred-sello");
    sello.textContent = esUco() ? "Prioridad UCO" : "Investigador externo";
    sello.classList.toggle("uco", esUco());
    $("cred-nota").textContent = esUco()
      ? "Tu acreditación se comprueba con el padrón de la UCO al enviar."
      : "Los investigadores externos se atienden después de los de la UCO.";
    $("campo-acreditacion").hidden = !esUco();
    $("campo-institucion").hidden = esUco();
  }
  form.addEventListener("input", actualizarCredencial);
  form.addEventListener("change", actualizarCredencial);
  actualizarCredencial();

  // ───────── Avisos y errores ─────────
  function limpiarAvisos() {
    clearInterval(temporizador);
    avisos.replaceChildren();
  }

  function mostrarAviso({ tipo, titulo, mensaje }, extra) {
    const caja = document.createElement("div");
    caja.className = `aviso ${tipo}`;
    const h = document.createElement("h2");
    h.textContent = titulo;
    const p = document.createElement("p");
    p.textContent = mensaje;
    caja.append(h, p);
    if (extra) caja.append(extra);
    avisos.append(caja);
    caja.scrollIntoView({ behavior: "smooth", block: "nearest" });
    return caja;
  }

  function limpiarErrores() {
    form.querySelectorAll("[data-error-for]").forEach((e) => (e.textContent = ""));
    form.querySelectorAll("[aria-invalid]").forEach((e) => e.removeAttribute("aria-invalid"));
  }

  function marcarError(campo, texto) {
    const destino = form.querySelector(`[data-error-for="${campo}"]`);
    if (destino) destino.textContent = texto;
    const input = form.elements[campo === "acepta_tratamiento" ? "acepta" : campo];
    if (input) input.setAttribute("aria-invalid", "true");
  }

  // ───────── Redirección con cuenta atrás ─────────
  function redirigirConAviso(notificacion, redirect) {
    let restante = Math.ceil(redirect.espera_ms / 1000);
    const acciones = document.createElement("div");
    acciones.className = "acciones";
    const ir = document.createElement("a");
    ir.href = redirect.url;
    ir.className = "boton";
    ir.style.cssText = "width:auto;text-decoration:none;display:inline-block";
    ir.textContent = "Ir a iniciar sesión";
    const quedarme = document.createElement("button");
    quedarme.type = "button";
    quedarme.className = "boton secundario";
    quedarme.textContent = "Quedarme aquí";
    const cuenta = document.createElement("span");
    cuenta.className = "ayuda";
    acciones.append(ir, quedarme, cuenta);

    mostrarAviso(notificacion, acciones);
    const pintar = () => (cuenta.textContent = `Te redirigimos en ${restante} s.`);
    pintar();

    temporizador = setInterval(() => {
      restante -= 1;
      if (restante <= 0) {
        clearInterval(temporizador);
        window.location.assign(redirect.url);
      } else pintar();
    }, 1000);
    quedarme.addEventListener("click", () => {
      clearInterval(temporizador);
      cuenta.remove();
      quedarme.remove();
    });
  }

  // ───────── Envío ─────────
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    limpiarAvisos();
    limpiarErrores();

    if ($("password").value !== $("password2").value) {
      marcarError("password2", "Las contraseñas no coinciden.");
      $("password2").focus();
      return;
    }

    const payload = {
      nombre: $("nombre").value,
      apellidos: $("apellidos").value,
      email: $("email").value,
      password: $("password").value,
      es_uco: esUco(),
      acreditacion: esUco() ? $("acreditacion").value : "",
      institucion: esUco() ? "" : $("institucion").value,
      acepta_tratamiento: $("acepta").checked,
    };

    btn.disabled = true;
    btn.textContent = "Enviando…";
    try {
      const resp = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const datos = await resp.json().catch(() => ({}));

      if (resp.status === 422 && datos.error?.detalles) {
        Object.entries(datos.error.detalles).forEach(([c, t]) => marcarError(c, t));
        mostrarAviso(datos.notificacion);
        const primero = form.querySelector("[aria-invalid=true]");
        if (primero) primero.focus();
        return;
      }

      if (datos.resultado === "ya_registrado" && datos.redirect) {
        redirigirConAviso(datos.notificacion, datos.redirect);   // aviso informativo + login
        return;
      }

      if (datos.notificacion) mostrarAviso(datos.notificacion);
      if (datos.resultado === "solicitud_creada") {
        form.reset();
        actualizarCredencial();
        form.hidden = true;
      }
    } catch (e) {
      mostrarAviso({ tipo: "error", titulo: "Sin conexión",
        mensaje: "No pudimos contactar con el servidor. Revisa tu conexión e inténtalo de nuevo." });
    } finally {
      btn.disabled = false;
      btn.textContent = "Solicitar acceso";
    }
  });
})();
