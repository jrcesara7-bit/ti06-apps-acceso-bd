<?php
// HolaMundo02 en PHP con interfaz web. Pide usuario y contraseña de MySQL en un formulario.
// Si la base acepta la conexión, muestra las asignaciones de CPremier con un buscador por trabajador.
// Uso:  php -S localhost:8080 holamundo02.php   y abrir http://localhost:8080
declare(strict_types=1);
require __DIR__ . '/config.php';

session_start(['cookie_httponly' => true, 'cookie_samesite' => 'Lax']);

// Escapa el texto antes de ponerlo en el HTML, para que un dato no se ejecute como código (XSS).
function e(mixed $v): string
{
    return htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');
}

$error = '';
$accion = $_POST['accion'] ?? '';

if ($accion === 'salir') {
    session_destroy();
    header('Location: /');
    exit;
}

if ($accion === 'entrar') {
    try {
        conectar($_POST['usuario'] ?? '', $_POST['clave'] ?? '');   // solo para validar el acceso
        session_regenerate_id(true);                                // sesión nueva al entrar
        $_SESSION['usuario'] = $_POST['usuario'];
        $_SESSION['clave'] = $_POST['clave'];                       // queda en el servidor, no en el navegador
        header('Location: /');
        exit;
    } catch (PDOException $ex) {
        http_response_code(401);   // credenciales no válidas
        $error = $ex->getCode() === 1045 ? 'Usuario o contraseña incorrectos.'
                                         : 'No se pudo conectar con el servidor de base de datos.';
    }
}

$filas = [];
$buscar = trim($_GET['buscar'] ?? '');
if (isset($_SESSION['usuario'])) {
    try {
        $pdo = conectar($_SESSION['usuario'], $_SESSION['clave']);
        // Consulta parametrizada. Lo que se escribe en el buscador nunca se concatena al SQL.
        $consulta = $pdo->prepare(
            "SELECT t.nombre AS trabajador, t.oficio, e.dir_edificio AS edificio, a.fecha_inicio AS inicio,
                    a.num_dias, a.num_dias * 8 * t.tarifa_hr AS monto
             FROM asignacion a
             JOIN trabajador t ON t.id_trabajador = a.id_trabajador
             JOIN edificio e ON e.id_edificio = a.id_edificio
             WHERE t.nombre LIKE :buscar
             ORDER BY a.fecha_inicio, t.nombre");
        $consulta->execute(['buscar' => "%$buscar%"]);
        $filas = $consulta->fetchAll();
    } catch (PDOException $ex) {
        http_response_code(500);
        $error = 'Error al consultar la base.';
    }
}
$total = array_sum(array_column($filas, 'monto'));
?>
<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>HolaMundo02 · PHP</title><style>
  body{font-family:system-ui,sans-serif;background:#f4f4f4;color:#1c1c1c;margin:0}
  main{max-width:860px;margin:40px auto;background:#fff;border:1px solid #d0d0d0;border-radius:8px;padding:28px 32px}
  h1{font-size:1.3rem;margin:0 0 4px} p.sub{color:#5c5c5c;margin:0 0 20px}
  label{display:block;font-weight:600;margin:12px 0 4px} input{padding:8px 10px;border:1px solid #b5b5b5;border-radius:5px;font:inherit}
  button{padding:8px 16px;border:0;border-radius:5px;background:#1c1c1c;color:#fff;font:inherit;cursor:pointer}
  table{border-collapse:collapse;width:100%;margin-top:16px} th,td{padding:7px 10px;text-align:left;border-bottom:1px solid #e2e2e2}
  th{border-bottom:2px solid #1c1c1c} td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
  .error{background:#ececec;border-left:4px solid #1c1c1c;padding:10px 12px;margin:12px 0}
  .barra{display:flex;gap:8px;align-items:center;flex-wrap:wrap} .barra form{display:flex;gap:8px;margin:0} .sep{flex:1}
</style></head><body><main>
<?php if (!isset($_SESSION['usuario'])): ?>
  <h1>HolaMundo02 · CPremier</h1>
  <p class="sub">PHP + PDO (pdo_mysql). Entra con tu usuario de MySQL.</p>
  <?php if ($error): ?><div class="error"><?= e($error) ?></div><?php endif; ?>
  <form method="post">
    <input type="hidden" name="accion" value="entrar">
    <label for="usuario">Usuario</label><input id="usuario" name="usuario" value="<?= e($_POST['usuario'] ?? '') ?>" required autofocus>
    <label for="clave">Contraseña</label><input id="clave" name="clave" type="password" required>
    <p><button type="submit">Entrar</button></p>
  </form>
<?php else: ?>
  <h1>Asignaciones de CPremier</h1>
  <p class="sub">Sesión de <b><?= e($_SESSION['usuario']) ?></b> en <?= e(cfg('DB_NAME', 'cpremier')) ?>.
     <?= count($filas) ?> registro(s), monto total <?= number_format((float) $total, 2, '.', '') ?>.</p>
  <?php if ($error): ?><div class="error"><?= e($error) ?></div><?php endif; ?>
  <div class="barra">
    <form method="get"><input name="buscar" value="<?= e($buscar) ?>" placeholder="Buscar trabajador"><button>Buscar</button></form>
    <span class="sep"></span>
    <form method="post"><input type="hidden" name="accion" value="salir"><button>Salir</button></form>
  </div>
  <table><thead><tr><th>Trabajador</th><th>Oficio</th><th>Edificio</th><th>Inicio</th><th class="num">Días</th><th class="num">Monto</th></tr></thead>
  <tbody>
  <?php foreach ($filas as $f): ?>
    <tr><td><?= e($f['trabajador']) ?></td><td><?= e($f['oficio']) ?></td><td><?= e($f['edificio']) ?></td>
        <td><?= e($f['inicio']) ?></td><td class="num"><?= e($f['num_dias']) ?></td>
        <td class="num"><?= number_format((float) $f['monto'], 2, '.', '') ?></td></tr>
  <?php endforeach; ?>
  </tbody></table>
<?php endif; ?>
</main></body></html>
