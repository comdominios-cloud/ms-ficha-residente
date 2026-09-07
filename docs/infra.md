# Infraestructura del proyecto

> Responsable: [@Brisseth-raton](https://github.com/Brisseth-raton) (backend / infraestructura).
> PLACEHOLDER: completar las IPs, ids y nombres reales a medida que se creen los
> recursos. **Nunca** pegar aqui credenciales ni llaves de acceso.

## Maquinas virtuales

| VM | Cantidad | AMI | Que corre adentro |
|----|----------|-----|-------------------|
| **Produccion** | **2, gemelas** (misma AMI, distinta IP) | Ubuntu 22.04 | Los 5 microservicios como contenedores |
| **Base de datos** | 1 | Ubuntu 22.04 | **3 contenedores**: PostgreSQL, MySQL, MongoDB |
| **Ingesta** | 1 | Ubuntu 22.04 | Los 3 contenedores Python de `ingesta-datos` |

Las dos VM de produccion son **identicas**: se crea una, se genera una **AMI** a
partir de ella y la segunda se lanza desde esa AMI. Ambas hacen `pull` de las
mismas imagenes de Docker Hub, por lo que corren exactamente la misma version.

El balanceador reparte el trafico entre las dos.

```
Clientes ──80/443──> Amplify (frontend)
                        │
                   Balanceador ──> VM produccion 1  ┐
                        └────────> VM produccion 2  ┘ (gemelas)
                                        │
                                        ▼ IP privada
                              VM base de datos (3 contenedores)
                                        ▲
                                        │ IP privada
                                  VM de ingesta ──> Bucket S3 ──> Glue ──> Athena
```

## Mapa de puertos

El curso asigno el rango **9000-12000** para los microservicios.

### Microservicios (VM de produccion)

| Microservicio | Publicado | Interno | Lenguaje |
|---------------|-----------|---------|----------|
| ms-residentes | 9001 | 8000 | Python / FastAPI |
| ms-pagos | 9002 | 8080 | Java / Spring Boot |
| ms-incidencias | 9003 | 3003 | por definir |
| ms-ficha-residente | 9004 | 8004 | Python / FastAPI |
| ms-analitico | 9005 | 8005 | Python / FastAPI |

### Bases de datos (VM de base de datos)

| Motor | Puerto | Microservicio que la usa |
|-------|--------|--------------------------|
| PostgreSQL | 5432 | ms-residentes |
| MySQL | 3306 | ms-pagos |
| MongoDB | 27017 | ms-incidencias |

## Security Groups

Regla de oro que dio el ACL: **el origen nunca puede ser `0.0.0.0/0`** salvo en
el balanceador. Cada regla apunta al *Security Group* de quien necesita entrar,
no a una IP suelta ni a internet entero.

### SG del balanceador

| Direccion | Puerto | Origen / Destino |
|-----------|--------|------------------|
| Entrada | 80, 443 | `0.0.0.0/0` (unico caso permitido: es el punto publico) |
| Salida | 9001-9005 | SG de produccion |

### SG de la VM de produccion

| Direccion | Puerto | Origen / Destino |
|-----------|--------|------------------|
| Entrada | 9001-9005 | SG del balanceador |
| Entrada | 22 (SSH) | IP fija del equipo, nunca abierta |
| Salida | 5432, 3306, 27017 | SG de la VM de base de datos |
| Salida | 443 | `0.0.0.0/0` (pull de imagenes desde Docker Hub) |

### SG de la VM de base de datos

| Direccion | Puerto | Origen / Destino |
|-----------|--------|------------------|
| Entrada | 5432, 3306, 27017 | SG de produccion **y** SG de ingesta |
| Entrada | 22 (SSH) | IP fija del equipo |
| Salida | 443 | `0.0.0.0/0` (pull de imagenes) |

### SG de la VM de ingesta

| Direccion | Puerto | Origen / Destino |
|-----------|--------|------------------|
| Entrada | 22 (SSH) | IP fija del equipo |
| Salida | 5432, 3306, 27017 | SG de la VM de base de datos |
| Salida | Todo el trafico (443) | S3 y Docker Hub |

## VPC

La cuenta tiene una VPC por defecto. Decidir si alcanza o si conviene una VPC
propia con subred publica (balanceador) y subred privada (produccion, base de
datos e ingesta). Registrar aqui la decision.

- VPC utilizada: `TODO`
- Subredes: `TODO`

## Docker Hub

Todas las imagenes se publican en la cuenta/organizacion del equipo, para que las
dos VM de produccion hagan `pull` de la misma version.

| Imagen | Tag | Quien la publica |
|--------|-----|------------------|
| `<org>/ms-residentes` | `0.1.0` | @Osomar1705 |
| `<org>/ms-pagos` | `0.1.0` | @sebastianperez72 |
| `<org>/ms-incidencias` | `0.1.0` | @fabianbot1331 |
| `<org>/ms-ficha-residente` | `0.1.0` | @Brisseth-raton |
| `<org>/ms-analitico` | `0.1.0` | @carloscondor1610 |
| `<org>/ingesta01..03` | `0.1.0` | @carloscondor1610 |

- Cuenta / organizacion de Docker Hub: `TODO`

## Inventario de recursos

Completar a medida que se creen:

| Recurso | Identificador | Notas |
|---------|---------------|-------|
| AMI base | `TODO` | Ubuntu 22.04 con Docker preinstalado |
| VM produccion 1 | `TODO` | IP publica / privada |
| VM produccion 2 | `TODO` | IP publica / privada |
| VM base de datos | `TODO` | IP privada |
| VM ingesta | `TODO` | IP privada |
| Bucket S3 | `TODO` | una carpeta por contenedor de ingesta |
| Base de Glue | `condominio_db` | catalogo sobre el bucket |

## Pendientes de confirmar con el ACL

1. Si la ingesta lee las bases **directamente** o a traves de las APIs. El
   diagrama muestra conexion directa a las BDs, que es lo coherente con "pull del
   100% de los registros".
2. Que significa exactamente que "el contenedor de ingesta almacena en el
   contenedor de base de datos" antes de subir a S3.
