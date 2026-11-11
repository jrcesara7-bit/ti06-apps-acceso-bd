// HolaMundo02 en Node.js con interfaz web (Express).
// Pide usuario y contraseña de MySQL en un formulario. Si la base acepta la conexión,
// muestra las asignaciones de CPremier con un buscador por trabajador.
// Uso:  npm run hola2   y abrir http://localhost:3000
const crypto = require('crypto');
const express = require('express');
const session = require('express-session');
const mysql = require('mysql2/promise');

const app = express();
const PUERTO = Number(process.env.PORT || 3000);
// El servidor y la base se configuran por entorno. El usuario y la contraseña los escribe la persona.
const SERVIDOR = {
  host: process.env.DB_HOST || '127.0.0.1',
  port: Number(process.env.DB_PORT || 3306),
  database: process.env.DB_NAME || 'cpremier',
};

app.use(express.urlencoded({ extended: false }));
app.use(session({
  // La sesión vive en la memoria del servidor. Al navegador solo llega una cookie con su identificador.
  secret: process.env.SESSION_SECRET || crypto.randomBytes(32).toString('hex'),
  resave: false,
  saveUninitialized: false,
  cookie: { httpOnly: true, sameSite: 'lax', maxAge: 15 * 60 * 1000 },
}));

// Escapa el texto antes de ponerlo en el HTML, para que un dato de la base no se ejecute como código (XSS).
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const pagina = (titulo, cuerpo) => `<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(titulo)}</title><style>
  body{font-family:system-ui,sans-serif;background:#f4f4f4;color:#1c1c1c;margin:0}
  main{max-width:860px;margin:40px auto;background:#fff;border:1px solid #d0d0d0;border-radius:8px;padding:28px 32px}
  h1{font-size:1.3rem;margin:0 0 4px} p.sub{color:#5c5c5c;margin:0 0 20px}
  label{display:block;font-weight:600;margin:12px 0 4px} input{padding:8px 10px;border:1px solid #b5b5b5;border-radius:5px;font:inherit}
  button{padding:8px 16px;border:0;border-radius:5px;background:#1c1c1c;color:#fff;font:inherit;cursor:pointer}
  table{border-collapse:collapse;width:100%;margin-top:16px} th,td{padding:7px 10px;text-align:left;border-bottom:1px solid #e2e2e2}
  th{border-bottom:2px solid #1c1c1c} td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
  .error{background:#ececec;border-left:4px solid #1c1c1c;padding:10px 12px;margin:12px 0}
  .barra{display:flex;gap:8px;align-items:center;flex-wrap:wrap} .barra form{display:flex;gap:8px;margin:0} .sep{flex:1}
</style></head><body><main>${cuerpo}</main></body></html>`;

const formularioLogin = (error = '', usuario = '') => pagina('HolaMundo02 · Acceso', `
  <h1>HolaMundo02 · CPremier</h1>
  <p class="sub">Node.js + Express + mysql2. Entra con tu usuario de MySQL.</p>
  ${error ? `<div class="error">${esc(error)}</div>` : ''}
  <form method="post" action="/login">
    <label for="usuario">Usuario</label><input id="usuario" name="usuario" value="${esc(usuario)}" required autofocus>
    <label for="clave">Contraseña</label><input id="clave" name="clave" type="password" required>
    <p><button type="submit">Entrar</button></p>
  </form>`);

// Abre una conexión con las credenciales que escribió la persona. Si MySQL las rechaza, lanza un error.
const conectar = (usuario, clave) => mysql.createConnection({ ...SERVIDOR, user: usuario, password: clave });

app.get('/', (req, res) => (req.session.usuario ? res.redirect('/asignaciones') : res.send(formularioLogin())));

app.post('/login', async (req, res) => {
  const { usuario = '', clave = '' } = req.body;
  try {
    const conexion = await conectar(usuario, clave);
    await conexion.end();
    // Se renueva la sesión al entrar y las credenciales quedan solo del lado del servidor.
    req.session.regenerate(() => {
      req.session.usuario = usuario;
      req.session.clave = clave;
      res.redirect('/asignaciones');
    });
  } catch (error) {
    // 401 es el código HTTP para credenciales no válidas. No se muestra el detalle interno del error.
    const motivo = error.code === 'ER_ACCESS_DENIED_ERROR'
      ? 'Usuario o contraseña incorrectos.' : 'No se pudo conectar con el servidor de base de datos.';
    res.status(401).send(formularioLogin(motivo, usuario));
  }
});

app.get('/asignaciones', async (req, res) => {
  if (!req.session.usuario) return res.redirect('/');
  const buscar = String(req.query.buscar || '').trim();
  let conexion;
  try {
    conexion = await conectar(req.session.usuario, req.session.clave);
    // Consulta parametrizada. Lo que se escribe en el buscador nunca se concatena al SQL.
    const [filas] = await conexion.execute(`
      SELECT t.nombre AS trabajador, t.oficio, e.dir_edificio AS edificio,
             DATE_FORMAT(a.fecha_inicio, '%Y-%m-%d') AS inicio, a.num_dias,
             a.num_dias * 8 * t.tarifa_hr AS monto
      FROM asignacion a
      JOIN trabajador t ON t.id_trabajador = a.id_trabajador
      JOIN edificio e ON e.id_edificio = a.id_edificio
      WHERE t.nombre LIKE ?
      ORDER BY a.fecha_inicio, t.nombre`, [`%${buscar}%`]);
    const total = filas.reduce((suma, f) => suma + Number(f.monto), 0);
    res.send(pagina('HolaMundo02 · Asignaciones', `
      <h1>Asignaciones de CPremier</h1>
      <p class="sub">Sesión de <b>${esc(req.session.usuario)}</b> en ${esc(SERVIDOR.database)}. ${filas.length} registro(s), monto total ${total.toFixed(2)}.</p>
      <div class="barra">
        <form method="get" action="/asignaciones"><input name="buscar" value="${esc(buscar)}" placeholder="Buscar trabajador"><button>Buscar</button></form>
        <span class="sep"></span>
        <form method="post" action="/logout"><button>Salir</button></form>
      </div>
      <table><thead><tr><th>Trabajador</th><th>Oficio</th><th>Edificio</th><th>Inicio</th><th class="num">Días</th><th class="num">Monto</th></tr></thead>
      <tbody>${filas.map((f) => `<tr><td>${esc(f.trabajador)}</td><td>${esc(f.oficio)}</td><td>${esc(f.edificio)}</td>
        <td>${esc(f.inicio)}</td><td class="num">${esc(f.num_dias)}</td><td class="num">${Number(f.monto).toFixed(2)}</td></tr>`).join('')}
      </tbody></table>`));
  } catch (error) {
    console.error(error.message);
    res.status(500).send(pagina('Error', '<h1>Error al consultar la base</h1><p><a href="/">Volver</a></p>'));
  } finally {
    if (conexion) await conexion.end();
  }
});

app.post('/logout', (req, res) => req.session.destroy(() => res.redirect('/')));

app.listen(PUERTO, () => console.log(`HolaMundo02 escuchando en http://localhost:${PUERTO}`));
