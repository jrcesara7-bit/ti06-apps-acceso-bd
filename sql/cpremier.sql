-- CPremier para hosting mysql. Esquema y datos de prueba.

DROP TABLE IF EXISTS asignacion;
DROP TABLE IF EXISTS trabajador;
DROP TABLE IF EXISTS edificio;

CREATE TABLE edificio (
  id_edificio INT NOT NULL,
  dir_edificio VARCHAR(70) NOT NULL,
  tipo VARCHAR(30),
  nivel_calidad INT,
  categoria INT,
  PRIMARY KEY (id_edificio)
) ENGINE=InnoDB;

CREATE TABLE trabajador (
  id_trabajador INT NOT NULL,
  nombre VARCHAR(50) NOT NULL,
  tarifa_hr DECIMAL(5,2),
  oficio VARCHAR(20),
  id_supv INT,
  PRIMARY KEY (id_trabajador)
) ENGINE=InnoDB;

CREATE TABLE asignacion (
  id_trabajador INT NOT NULL,
  id_edificio INT NOT NULL,
  fecha_inicio DATE NOT NULL,
  num_dias INT,
  PRIMARY KEY (id_trabajador, id_edificio, fecha_inicio)
) ENGINE=InnoDB;

INSERT INTO edificio VALUES
(111,'1213 Aspen','Oficina',4,1),
(210,'1011 Birch','Oficina',3,1),
(312,'123 Elm','Oficina',2,2),
(435,'456 Maple','Comercio',1,1),
(460,'1415 Beech','Almacen',3,3),
(515,'789 Oak','Residencia',3,1);

INSERT INTO trabajador VALUES
(1235,'M Faraday',12.50,'Electricista',1311),
(1311,'C Coulomb',15.50,'Electricista',1311),
(1412,'C Nemo',13.75,'Fontanero',1520),
(1520,'H Rickover',11.75,'Fontanero',1520),
(2920,'R Garret',10.00,'Albañil',2920),
(3001,'J Barrister',8.20,'Carpintero',3231),
(3231,'P Mason',17.40,'Carpintero',3231);

INSERT INTO asignacion VALUES
(1235,312,'2024-10-10',5),
(1235,515,'2024-10-17',22),
(1311,435,'2024-10-08',12),
(1311,460,'2024-10-23',24),
(1412,111,'2024-12-01',4),
(1412,210,'2024-11-15',12),
(1412,312,'2024-10-01',10),
(1412,435,'2024-10-15',15),
(1412,460,'2024-12-08',18),
(1412,515,'2024-11-05',8),
(1520,312,'2024-10-30',17),
(1520,515,'2024-10-09',14),
(2920,210,'2024-11-10',15),
(2920,435,'2024-10-28',10),
(2920,460,'2024-10-05',18),
(3001,111,'2024-10-08',14),
(3001,210,'2024-10-27',14),
(3231,111,'2024-10-10',8),
(3231,312,'2024-10-24',20);

ALTER TABLE trabajador ADD CONSTRAINT trabajador_supv_fk FOREIGN KEY (id_supv) REFERENCES trabajador (id_trabajador);
ALTER TABLE asignacion ADD CONSTRAINT asignacion_trabajador_fk FOREIGN KEY (id_trabajador) REFERENCES trabajador (id_trabajador);
ALTER TABLE asignacion ADD CONSTRAINT asignacion_edificio_fk FOREIGN KEY (id_edificio) REFERENCES edificio (id_edificio);
