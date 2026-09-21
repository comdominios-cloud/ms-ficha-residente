# Runbook de despliegue — una sola pasada

Guia pensada para desplegar **todo de una vez**, sin prueba y error, y gastando
lo minimo de credito de AWS Academy.

Leerla entera antes de empezar. Son unos 45 minutos si no hay que volver atras.

---

## Antes de arrancar: que consume el credito

| Recurso | Peso relativo | Nota |
|---------|---------------|------|
| **Application Load Balancer** | el mas caro por hora | Cobra este o no este en uso |
| **EC2 de base de datos** | medio | Necesita 2 GB de RAM para tres motores |
| **EC2 de produccion** x2 | bajo | `t3.micro` alcanza |
| EBS de las instancias | muy bajo | Se paga aunque esten apagadas |

Tres reglas para que rinda:

1. **Apagar las instancias al terminar.** Una EC2 detenida no cobra computo,
   solo el disco. Es la diferencia mas grande.
2. **No borrar el balanceador.** Si se recrea, cambia su DNS y hay que
   reconfigurar el API Gateway y el frontend. Sale mas caro en tiempo que lo
   que ahorra.
3. **Grabar la evidencia el dia que funcione.** Capturas y un video corto de la
   demo. Asi no hace falta tener todo prendido hasta la exposicion.

---

## Paso 0 — Que NO hay que crear

Para no gastar de mas:

- Nada de NAT Gateway: las instancias usan la subred publica de la VPC por defecto.
- Nada de Elastic IP: las IP publicas cambian al reiniciar, y no importa porque
  todo entra por el balanceador y el API Gateway.
- Nada de RDS ni DocumentDB: las bases van como contenedores, que es lo que
  pide el enunciado.
- Nada de CloudFront: el rol del laboratorio no tiene permisos.

---

## Paso 1 — Las instancias

Tres, todas desde la AMI `condominio-ubuntu22-docker-v1`:

| Nombre | Tipo | Para que |
|--------|------|----------|
| `condominio-prod-01` | `t3.micro` | microservicios |
| `condominio-prod-02` | `t3.micro` | microservicios (gemela) |
| `condominio-db-01` | `t3.small` | PostgreSQL + MySQL + MongoDB |

> La de base de datos necesita `t3.small`. Con `t3.micro` (1 GB) los tres
> motores juntos se quedan sin memoria y MongoDB es el primero en caer.

Las dos de produccion **lanzarlas desde la AMI personalizada**, no clonando
una existente: el enunciado pide dos maquinas gemelas desde esa imagen.

---

## Paso 2 — Security Groups

Cuatro, y el orden importa porque se referencian entre si.

**1. `sgc-alb`** — el unico publico

| Direccion | Puerto | Origen |
|-----------|--------|--------|
| Entrada | 80 | `0.0.0.0/0` |
| Salida | Todo | — |

**2. `sgc-produccion`**

| Direccion | Puerto | Origen |
|-----------|--------|--------|
| Entrada | 9000-12000 | **SG `sgc-alb`** |
| Entrada | 22 | tu IP |
| Salida | Todo | — |

**3. `sgc-database`**

| Direccion | Puerto | Origen |
|-----------|--------|--------|
| Entrada | 5432, 3306, 27017 | **SG `sgc-produccion`** |
| Entrada | 5432, 3306, 27017 | **SG `sgc-ingesta`** |
| Entrada | 22 | tu IP |
| Salida | Todo | — |

**4. `sgc-ingesta`** — para la VM de @carloscondor1610

| Direccion | Puerto | Origen |
|-----------|--------|--------|
| Entrada | 22 | tu IP |
| Salida | Todo | — |

> Ninguna regla con origen `0.0.0.0/0` salvo la del balanceador. El ACL insistio
> con eso.

---

## Paso 3 — La VM de base de datos

Entrar por SSH a `condominio-db-01` y pegar esto **completo**:

```bash
mkdir -p ~/bases && cd ~/bases

cat > .env <<'ENV'
POSTGRES_USER=condominio
POSTGRES_PASSWORD=CAMBIAR_ESTA_CLAVE
MYSQL_USER=condominio
MYSQL_PASSWORD=CAMBIAR_ESTA_CLAVE
MYSQL_ROOT_PASSWORD=CAMBIAR_ESTA_CLAVE
ENV
chmod 600 .env

cat > docker-compose.yml <<'YML'
services:
  postgres:
    image: postgres:16
    container_name: condominio-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: condominio_residentes
    ports: ["5432:5432"]
    volumes: [pg_data:/var/lib/postgresql/data]
    restart: unless-stopped

  mysql:
    image: mysql:8
    container_name: condominio-mysql
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: condominio_pagos
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    ports: ["3306:3306"]
    volumes: [mysql_data:/var/lib/mysql]
    restart: unless-stopped

  mongo:
    image: mongo:7
    container_name: condominio-mongodb
    ports: ["27017:27017"]
    volumes: [mongo_data:/data/db]
    restart: unless-stopped

volumes:
  pg_data:
  mysql_data:
  mongo_data:
YML

docker compose up -d
sleep 30
docker ps
```

> **`mongo:7`, no `mongo:8`.** La version 8 no arranca en kernels 6.19 o
> superiores: es una incompatibilidad conocida y el contenedor muere al
> instante.

Despues crear la segunda base de PostgreSQL, la de usuarios:

```bash
docker exec condominio-postgres psql -U condominio -d postgres \
  -c "CREATE DATABASE condominio_usuarios;"
```

### Cargar los esquemas

```bash
cd ~/bases
for r in ms-residentes ms-usuarios ms-pagos; do
  curl -sO "https://raw.githubusercontent.com/comdominios-cloud/$r/main/docs/schema.sql"
  mv schema.sql "$r-schema.sql"
done

docker exec -i condominio-postgres psql -U condominio -d condominio_residentes < ms-residentes-schema.sql
docker exec -i condominio-postgres psql -U condominio -d condominio_usuarios   < ms-usuarios-schema.sql
docker exec -i condominio-mysql mysql -ucondominio -p"$MYSQL_PASSWORD" condominio_pagos < ms-pagos-schema.sql
```

Comprobar:

```bash
docker exec condominio-postgres psql -U condominio -d condominio_residentes -c "\dt"
docker exec condominio-postgres psql -U condominio -d condominio_usuarios   -c "\dt"
docker exec condominio-mysql mysql -ucondominio -p"$MYSQL_PASSWORD" condominio_pagos -e "SHOW TABLES;"
```

---

## Paso 4 — Las VM de produccion

**Lo mismo en las dos maquinas.** Reemplazar `IP_PRIVADA_DB` por la IP privada
de `condominio-db-01` y generar el secreto **una sola vez** para las dos.

```bash
# Generar el JWT_SECRET UNA VEZ y usar el mismo valor en las dos maquinas
openssl rand -hex 32
```

```bash
mkdir -p ~/condominio && cd ~/condominio

cat > comun.env <<'ENV'
POSTGRES_HOST=IP_PRIVADA_DB
POSTGRES_PORT=5432
POSTGRES_USER=condominio
POSTGRES_PASSWORD=LA_MISMA_DEL_PASO_3
JWT_SECRET=EL_VALOR_GENERADO_ARRIBA
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
APP_PORT=8000
ENV

cat > residentes.env <<'ENV'
POSTGRES_DB=condominio_residentes
ENV

cat > usuarios.env <<'ENV'
POSTGRES_DB=condominio_usuarios
ENV

cat > pagos.env <<'ENV'
APP_PORT=8080
MYSQL_HOST=IP_PRIVADA_DB
MYSQL_PORT=3306
MYSQL_DATABASE=condominio_pagos
MYSQL_USER=condominio
MYSQL_PASSWORD=LA_MISMA_DEL_PASO_3
ENV

cat > incidencias.env <<'ENV'
PORT=3003
MONGO_URI=mongodb://IP_PRIVADA_DB:27017/condominio_incidencias
MONGO_DB=condominio_incidencias
ENV

cat > ficha.env <<'ENV'
APP_PORT=8004
MS_RESIDENTES_URL=http://localhost:9001
MS_PAGOS_URL=http://localhost:9002
MS_INCIDENCIAS_URL=http://localhost:9003
HTTP_TIMEOUT_SECONDS=5
ENV

chmod 600 *.env

cat > docker-compose.yml <<'YML'
services:
  ms-residentes:
    image: osomar/ms-residentes:0.2.0
    container_name: ms-residentes
    ports: ["9001:8000"]
    env_file: [comun.env, residentes.env]
    restart: unless-stopped

  ms-usuarios:
    image: osomar/ms-usuarios:0.1.0
    container_name: ms-usuarios
    ports: ["9006:8000"]
    env_file: [comun.env, usuarios.env]
    restart: unless-stopped

  ms-pagos:
    image: sebpecar75/ms-pagos:latest
    container_name: ms-pagos
    ports: ["9002:8080"]
    env_file: [pagos.env]
    restart: unless-stopped

  ms-ficha-residente:
    image: osomar/ms-ficha-residente:0.1.0
    container_name: ms-ficha-residente
    ports: ["9004:8004"]
    env_file: [ficha.env]
    restart: unless-stopped
YML

docker compose pull
docker compose up -d
sleep 20
docker ps
```

Comprobar **en la propia maquina**:

```bash
curl -s localhost:9001/health   # tiene que decir "database":"ok"
curl -s localhost:9006/health   # tiene que decir "database":"ok"
curl -s localhost:9002/cuotas | head -c 200
curl -s localhost:9004/dependencias/estado
```

> `restart: unless-stopped` hace que los contenedores vuelvan solos cuando se
> prende la maquina. Sin eso, cada vez que expira el laboratorio hay que
> levantarlos a mano.

`ms-incidencias` y `ms-analitico` se agregan cuando sus duenos publiquen las
imagenes.

---

## Paso 5 — Balanceador y reglas

Target groups, uno por puerto, todos **HTTP** y con health check en la ruta
que ya existe:

| Target group | Puerto | Health check |
|--------------|--------|--------------|
| `tg-residentes` | 9001 | `/health` |
| `tg-usuarios` | 9006 | `/health` |
| `tg-pagos` | 9002 | `/cuotas` |
| `tg-ficha` | 9004 | `/health` |

Registrar **las dos** instancias de produccion en cada uno.

El balanceador tiene que ser **interno**, no internet-facing: el enunciado pide
*"balanceador de carga (privado, no publico)"*.

Reglas del listener HTTP:80, por orden de prioridad:

| Prioridad | Ruta | Destino |
|-----------|------|---------|
| 10 | `/residentes*`, `/unidades*`, `/edificios*` | `tg-residentes` |
| 20 | `/usuarios*`, `/auth*` | `tg-usuarios` |
| 30 | `/cuotas*`, `/pagos*` | `tg-pagos` |
| 40 | `/ficha*`, `/dependencias*` | `tg-ficha` |
| — | por defecto | `tg-residentes` |

---

## Paso 6 — API Gateway

Ya existe (`api-condominio`, `5y33fncgsh`). Si el balanceador cambio de DNS,
hay que actualizar la integracion:

- **Integration**: HTTP URI → `http://<DNS-del-ALB>/{proxy}`
- **Route**: `ANY /{proxy+}`
- **Stage**: `$default` con auto-deploy

---

## Paso 7 — Verificar todo de una

Desde cualquier maquina con internet:

```bash
git clone https://github.com/comdominios-cloud/ms-residentes.git
cd ms-residentes
APIGW=https://5y33fncgsh.execute-api.us-east-1.amazonaws.com \
  ./scripts/verificar-despliegue.sh
```

Si da todo en verde, **sacar las capturas y grabar el video de la demo en ese
momento**. Es lo que permite apagar todo despues sin perder la evidencia.

---

## Paso 8 — Apagar para no gastar

Al terminar la sesion de trabajo:

```
EC2 > Instancias > seleccionar las 3 > Estado de la instancia > Detener
```

**Detener, no terminar.** Detenida conserva el disco y los contenedores; si se
termina, se pierde todo y hay que rehacer desde el paso 1.

Al volver a prenderlas:

1. Iniciar las instancias
2. Esperar a que digan **2/2** en las comprobaciones
3. Los contenedores arrancan solos por el `restart: unless-stopped`
4. Correr el script de verificacion

Las IP publicas cambian al reiniciar, pero no importa: las privadas se
mantienen y todo entra por el balanceador.
