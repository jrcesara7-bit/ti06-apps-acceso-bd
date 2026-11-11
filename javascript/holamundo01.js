// HolaMundo01 en Node.js. Se conecta a MySQL, ejecuta un SELECT y muestra los registros en consola.
// Uso:  npm run hola1            lista a todos los trabajadores
//       npm run hola1 -- Fontanero   filtra por oficio (el valor viaja como parámetro, no pegado al SQL)
const mysql = require('mysql2/promise');

// Los datos de conexión salen de variables de entorno (archivo .env), nunca del código.
const config = {
  host: process.env.DB_HOST || '127.0.0.1',
  port: Number(process.env.DB_PORT || 3306),
  database: process.env.DB_NAME || 'cpremier',
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
};

const SQL = `
  SELECT t.id_trabajador, t.nombre, t.oficio, t.tarifa_hr, s.nombre AS supervisor
  FROM trabajador t
  LEFT JOIN trabajador s ON s.id_trabajador = t.id_supv
  WHERE t.oficio LIKE ?
  ORDER BY t.nombre`;

async function main() {
  if (!config.user) {
    console.error('Falta DB_USER. Copia .env.example como .env y llena tus datos.');
    process.exit(1);
  }
  const oficio = process.argv[2] || '%';
  let conexion;
  try {
    conexion = await mysql.createConnection(config);
    console.log(`Conectado a ${config.database} en ${config.host}:${config.port} como ${config.user}`);
    // execute() usa una sentencia preparada. El "?" lo sustituye el servidor, así se evita la inyección de SQL.
    const [filas] = await conexion.execute(SQL, [oficio]);
    console.table(filas);
    console.log(`${filas.length} registro(s)`);
  } catch (error) {
    console.error('No se pudo consultar la base:', error.message);
    process.exitCode = 1;
  } finally {
    if (conexion) await conexion.end();   // siempre se cierra la conexión
  }
}

main();
