# ms-ficha-residente

Microservicio **consumidor de APIs**, sin base de datos propia. Devuelve la
**ficha consolidada de un residente** del condominio.

> CS2032 Cloud Computing - UTEC | Proyecto: Sistema de Administracion de Condominios

## Responsable

[@Brisseth-raton](https://github.com/Brisseth-raton) — Backend / Infraestructura. Ver [INTEGRANTE.md](INTEGRANTE.md).

Es el unico repositorio que integra a los demas: las 3 APIs con base de datos se
desarrollan por separado y aqui se juntan por HTTP.

La infraestructura del proyecto (VPC, Security Groups, VM de produccion gemelas,
VM de base de datos, VM de ingesta y el mapa de puertos) se documenta en
[docs/infra.md](docs/infra.md).

## Dominio

No persiste nada. Recibe el id de un residente y, en paralelo, consulta:

| Microservicio | Que le pide |
|---------------|-------------|
| `ms-residentes` | datos personales del residente y su unidad/edificio |
| `ms-pagos` | estado de cuenta: cuotas pendientes, deuda total, ultimos pagos |
| `ms-incidencias` | incidencias abiertas y proximas reservas de areas comunes |

Con esas tres respuestas arma un solo JSON. Cumple dos requisitos del curso a la
vez: **microservicio sin base de datos** y **microservicio que consume a otros
microservicios**.

```
                          ┌──> ms-residentes  :9001
web ──> balanceador ──> ms-ficha-residente :9004 ─┼──> ms-pagos       :9002
                          └──> ms-incidencias :9003
```

Si alguno de los tres servicios no responde, la ficha se devuelve igual con esa
seccion marcada como no disponible (degradacion controlada), para que el avance
de un integrante no bloquee al resto.

## Stack

| Elemento    | Tecnologia                |
|-------------|---------------------------|
| Lenguaje    | Python 3.12               |
| Framework   | FastAPI                   |
| Base de datos | **Ninguna** (por diseno) |
| Cliente HTTP | httpx (asincrono, en paralelo) |
| Documentacion | Swagger-UI en `/docs`   |
| Contenedor  | Docker                    |

## Puerto asignado

**9004** publicado · **8004** dentro del contenedor.

El curso asigno el rango **9000-12000** para los microservicios; ese es el puerto
que se habilita en el Security Group.

| Microservicio | Publicado | Interno |
|---------------|-----------|---------|
| ms-residentes | 9001      | 8000    |
| ms-pagos      | 9002      | 8080    |
| ms-incidencias| 9003      | 3003    |
| ms-ficha-residente | **9004** | 8004 |
| ms-analitico  | 9005      | 8005    |
| web-condominio (dev) | 5173 | —     |

Las bases de datos **no** entran en ese rango: PostgreSQL 5432, MySQL 3306,
MongoDB 27017, alcanzables solo desde los Security Groups de la VM de produccion
y la VM de ingesta.

## Endpoints REST

| # | Metodo | Ruta | Descripcion | Consumido por |
|---|--------|------|-------------|---------------|
| 1 | `GET` | `/ficha/{residente_id}` | Ficha completa: datos, estado de cuenta, cuotas, pagos, incidencias y reservas | **frontend** |
| 2 | `GET` | `/ficha/unidad/{unidad_id}` | Ficha de una unidad y todos sus residentes | **frontend** |
| 3 | `GET` | `/ficha/{residente_id}/resumen` | Version reducida: nombre, unidad, edificio, deuda, incidencias abiertas | frontend |
| 4 | `GET` | `/dependencias/estado` | Estado de los tres microservicios que consume | infra |
| 5 | `GET` | `/health` | Health check | infra |

Documentacion interactiva: `http://<ip>:9004/docs` (Swagger-UI).

## Como resuelve la agregacion

Las llamadas a los tres microservicios salen **en paralelo** con
`asyncio.gather`. Si se hicieran una detras de otra, la ficha tardaria la suma
de las tres; asi tarda lo que tarde la mas lenta.

### Degradacion controlada

Cada bloque de la respuesta lleva su propio `disponible` y `error`:

```json
{
  "residente_id": 1,
  "unidad_id": 1,
  "completa": false,
  "residente":     { "disponible": true,  "datos": { "nombres": "Lucia", "...": "..." } },
  "estado_cuenta": { "disponible": false, "error": "no se pudo contactar a ms-pagos" },
  "incidencias":   { "disponible": false, "error": "no se pudo contactar a ms-incidencias" }
}
```

Si un microservicio se cae, la ficha **se devuelve igual** con esa seccion
marcada, en vez de fallar entera. El campo `completa` dice si los tres
respondieron. Asi la caida de un servicio no arrastra a los otros dos.

### Reintentos

Un timeout o un 5xx se reintentan, con una espera creciente entre intentos: son
fallas que pueden ser pasajeras. Un 404 o un 400 **no** se reintentan, porque
volver a preguntar da el mismo resultado.

### Rutas que usa para sondear

`/dependencias/estado` consulta `/edificios`, `/cuotas` e `/incidencias` en vez
de `/health`. Es a proposito: el balanceador solo enruta las rutas que tienen
regla, y `/health` no la tiene.

## Variables de entorno

Copiar [.env.example](.env.example) a `.env` y completar. **Nunca** commitear `.env`.

| Variable | Descripcion | Ejemplo |
|----------|-------------|---------|
| `APP_NAME` | Nombre del servicio | `ms-ficha-residente` |
| `APP_PORT` | Puerto dentro del contenedor | `8004` |
| `PUBLISHED_PORT` | Puerto publicado en la VM | `9004` |
| `APP_ENV` | Entorno de ejecucion | `development` / `production` |
| `LOG_LEVEL` | Nivel de logging | `info` |
| `MS_RESIDENTES_URL` | URL base de ms-residentes | `http://<ip-vm-produccion>:9001` |
| `MS_PAGOS_URL` | URL base de ms-pagos | `http://<ip-vm-produccion>:9002` |
| `MS_INCIDENCIAS_URL` | URL base de ms-incidencias | `http://<ip-vm-produccion>:9003` |
| `HTTP_TIMEOUT_SECONDS` | Timeout de las llamadas salientes | `5` |
| `HTTP_MAX_RETRIES` | Reintentos ante fallo | `2` |

## Como levantar con Docker

### Solo el microservicio

```bash
cp .env.example .env
docker build -t ms-ficha-residente .
docker run --rm -p 9004:8004 --env-file .env ms-ficha-residente
```

Luego abrir `http://localhost:9004/docs`.

### En la VM de produccion

```yaml
services:
  ms-ficha-residente:
    image: <usuario>/ms-ficha-residente:0.1.0
    ports: ["9004:8004"]
    env_file: .env
```

```bash
docker compose up -d
```

Los cinco microservicios corren en la misma VM de produccion, asi que las
variables `MS_*_URL` pueden apuntar a la **IP privada** de esa maquina con el
puerto publicado de cada uno (9001, 9002, 9003). Como hay **dos VM de produccion
gemelas**, el mismo `.env` funciona en las dos.

## Estructura

```
app/
├── main.py          # instancia FastAPI y CORS
├── config.py        # URLs de los tres microservicios
├── routers/
│   ├── ficha.py     # los 3 endpoints de ficha
│   └── salud.py     # health y estado de dependencias
├── clients/
│   ├── base.py      # reintentos y manejo de fallas
│   ├── residentes.py
│   ├── pagos.py
│   └── incidencias.py
└── schemas/
    └── ficha.py     # contratos de salida
postman/
tests/
docs/
└── infra.md      # VPC, Security Groups, VMs y mapa de puertos
```

## Coleccion de Postman

[postman/ms-ficha-residente.postman_collection.json](postman/ms-ficha-residente.postman_collection.json),
8 requests verificados. Empezar por **`0. Estado / Estado de las dependencias`**
para ver que microservicios estan arriba antes de pedir una ficha.

## Estado

**Implementado y probado.** Los 5 endpoints funcionando, con llamadas en
paralelo y degradacion controlada. Imagen publicada como
`osomar/ms-ficha-residente:0.1.0`.

Verificado contra `ms-residentes` real, con `ms-pagos` e `ms-incidencias`
caidos a proposito: la ficha se devuelve con las secciones disponibles y las
demas marcadas con su motivo.
