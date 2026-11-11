// HolaMundo03 en Node.js. API REST de asignaciones de CPremier con Express y mysql2.
// Expone los mismos endpoints y el mismo JSON que las versiones de Python y PHP,
// para que un solo cliente web pueda usar cualquiera de las tres.
// Uso:  npm run hola3   y abrir http://localhost:3001
const path = require('path');
const express = require('express');
const mysql = require('mysql2/promise');

const PUERTO = Number(process.env.API_PORT || 3001);
const app = express();
// Un pool reutiliza conexiones en lugar de abrir una por petición. dateStrings deja las fechas como texto.
const pool = mysql.createPool({
  host: process.env.DB_HOST || '127.0.0.1',
  port: Number(process.env.DB_PORT || 3306),
  database: process.env.DB_NAME || 'cpremier',
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  dateStrings: true,
  connectionLimit: 5,
});

app.use(express.json());
// CORS. Permite que la página servida por otro back-end (otro puerto) llame a esta API.
app.use((req, res, next) => {
  res.set({
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  });
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});
// El cliente web es el mismo archivo para los tres lenguajes.
app.get('/', (_req, res) => res.sendFile(path.join(__dirname, '..', 'cliente', 'index.html')));

const LISTA = `
  SELECT a.id_trabajador, a.id_edificio, CAST(a.fecha_inicio AS CHAR) AS fecha_inicio, a.num_dias,
         t.nombre AS trabajador, t.oficio, e.dir_edificio AS edificio,
         a.num_dias * 8 * t.tarifa_hr AS monto
  FROM asignacion a
  JOIN trabajador t ON t.id_trabajador = a.id_trabajador
  JOIN edificio e ON e.id_edificio = a.id_edificio
  WHERE t.nombre LIKE ?
  ORDER BY a.fecha_inicio, t.nombre`;

// Revisa los datos antes de tocar la base. Devuelve un mensaje si algo está mal, o null si todo bien.
function validar({ id_trabajador, id_edificio, fecha_inicio, num_dias }, soloDias = false) {
  if (!Number.isInteger(num_dias) || num_dias < 1 || num_dias > 365) return 'num_dias debe ser un entero entre 1 y 365';
  if (soloDias) return null;
  if (!Number.isInteger(id_trabajador) || !Number.isInteger(id_edificio)) return 'id_trabajador e id_edificio deben ser enteros';
  if (!/^\d{4}-\d{2}-\d{2}$/.test(fecha_inicio || '')) return 'fecha_inicio debe tener el formato AAAA-MM-DD';
  return null;
}

// Envuelve cada ruta para que un error de la base se convierta en una respuesta HTTP con sentido.
const ruta = (fn) => async (req, res) => {
  try {
    await fn(req, res);
  } catch (error) {
    if (error.code === 'ER_DUP_ENTRY') return res.status(409).json({ error: 'Esa asignación ya existe' });
    if (error.code === 'ER_NO_REFERENCED_ROW_2') return res.status(400).json({ error: 'El trabajador o el edificio no existe' });
    if (error.code === 'ER_TRUNCATED_WRONG_VALUE') return res.status(400).json({ error: 'La fecha no es válida' });
    console.error(error.message);
    res.status(500).json({ error: 'Error interno al consultar la base' });
  }
};

app.get('/api/info', (_req, res) => res.json({ lenguaje: 'JavaScript', entorno: `Node.js ${process.versions.node}`, driver: 'mysql2', framework: 'Express' }));

app.get('/api/trabajadores', ruta(async (_req, res) => {
  const [filas] = await pool.execute('SELECT id_trabajador, nombre, oficio FROM trabajador ORDER BY nombre');
  res.json(filas);
}));

app.get('/api/edificios', ruta(async (_req, res) => {
  const [filas] = await pool.execute('SELECT id_edificio, dir_edificio FROM edificio ORDER BY dir_edificio');
  res.json(filas);
}));

// Esquema de la base, leído del catálogo information_schema. Con esto el cliente dibuja el diagrama ER.
const SQL_COLUMNAS = `
  SELECT TABLE_NAME AS tabla, COLUMN_NAME AS columna, COLUMN_TYPE AS tipo, COLUMN_KEY AS llave
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
  ORDER BY TABLE_NAME, ORDINAL_POSITION`;
const SQL_RELACIONES = `
  SELECT TABLE_NAME AS tabla, COLUMN_NAME AS columna,
         REFERENCED_TABLE_NAME AS ref_tabla, REFERENCED_COLUMN_NAME AS ref_columna
  FROM information_schema.KEY_COLUMN_USAGE
  WHERE TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL
  ORDER BY TABLE_NAME, COLUMN_NAME`;

app.get('/api/esquema', ruta(async (_req, res) => {
  const [columnas] = await pool.query(SQL_COLUMNAS);
  const [relaciones] = await pool.query(SQL_RELACIONES);
  res.json({ columnas, relaciones });
}));

// READ
app.get('/api/asignaciones', ruta(async (req, res) => {
  const [filas] = await pool.execute(LISTA, [`%${req.query.buscar || ''}%`]);
  res.json(filas.map((f) => ({ ...f, monto: Number(f.monto) })));   // DECIMAL llega como texto
}));

// CREATE
app.post('/api/asignaciones', ruta(async (req, res) => {
  const error = validar(req.body);
  if (error) return res.status(400).json({ error });
  const { id_trabajador, id_edificio, fecha_inicio, num_dias } = req.body;
  await pool.execute('INSERT INTO asignacion (id_trabajador, id_edificio, fecha_inicio, num_dias) VALUES (?, ?, ?, ?)',
    [id_trabajador, id_edificio, fecha_inicio, num_dias]);
  res.status(201).json({ id_trabajador, id_edificio, fecha_inicio, num_dias });
}));

// UPDATE. La llave de la asignación va en la URL y el dato nuevo en el cuerpo.
app.put('/api/asignaciones/:t/:e/:f', ruta(async (req, res) => {
  const error = validar(req.body, true);
  if (error) return res.status(400).json({ error });
  const [r] = await pool.execute(
    'UPDATE asignacion SET num_dias = ? WHERE id_trabajador = ? AND id_edificio = ? AND fecha_inicio = ?',
    [req.body.num_dias, req.params.t, req.params.e, req.params.f]);
  // affectedRows cuenta las filas encontradas. Si es 0, esa asignación no existe.
  if (r.affectedRows === 0) return res.status(404).json({ error: 'No existe esa asignación' });
  res.json({ num_dias: req.body.num_dias });
}));

// DELETE
app.delete('/api/asignaciones/:t/:e/:f', ruta(async (req, res) => {
  const [r] = await pool.execute('DELETE FROM asignacion WHERE id_trabajador = ? AND id_edificio = ? AND fecha_inicio = ?',
    [req.params.t, req.params.e, req.params.f]);
  if (r.affectedRows === 0) return res.status(404).json({ error: 'No existe esa asignación' });
  res.sendStatus(204);
}));

// Demostración de inyección de SQL. El modo "concatenada" es vulnerable A PROPÓSITO y solo hace un SELECT.
// Nunca se debe escribir así una consulta real.
app.get('/api/demo/inyeccion', ruta(async (req, res) => {
  const oficio = String(req.query.oficio || '');
  const base = 'SELECT nombre, oficio, tarifa_hr FROM trabajador WHERE oficio = ';
  if (req.query.modo === 'concatenada') {
    const sql = `${base}'${oficio}'`;                       // el texto del usuario se vuelve parte del SQL
    const [filas] = await pool.query(sql).catch((e) => [[{ error_sql: e.sqlMessage }]]);
    return res.json({ modo: 'concatenada', sql, filas });
  }
  const [filas] = await pool.execute(`${base}?`, [oficio]);   // el valor viaja aparte
  res.json({ modo: 'parametrizada', sql: `${base}?   ← parámetro: ${JSON.stringify(oficio)}`, filas });
}));

app.use('/api', (_req, res) => res.status(404).json({ error: 'Ruta no encontrada' }));

app.listen(PUERTO, '127.0.0.1', () => console.log(`API de Node.js en http://localhost:${PUERTO}`));
