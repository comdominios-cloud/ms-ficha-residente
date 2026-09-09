# Infraestructura del proyecto

> Responsable: [@Brisseth-raton](https://github.com/Brisseth-raton) (backend / infraestructura).
>
> No se almacenan credenciales, contraseñas, llaves privadas ni tokens de acceso
> dentro de este documento.

## Maquinas virtuales

| VM | Cantidad | AMI | Que corre adentro |
|----|----------|-----|-------------------|
| **Produccion** | **2** | Ubuntu 22.04 + Docker | Microservicios del proyecto como contenedores |
| **Base de datos** | 1 | Ubuntu 22.04 + Docker | PostgreSQL, MySQL y MongoDB |
| **Ingesta** | Pendiente / otro integrante | Ubuntu 22.04 | Contenedores Python de `ingesta-datos` |

Se creo una AMI personalizada denominada:

`condominio-ubuntu22-docker-v1`

con identificador:

`ami-08c6a4d8c4b64e1ce`

La AMI contiene Ubuntu 22.04, Docker Engine y Docker Compose
preinstalados, permitiendo desplegar maquinas con una configuracion
consistente.

Las maquinas de produccion utilizadas son:

- `condominio-prod-01`
- `condominio-prod-02`

Ambas utilizan Ubuntu 22.04, Docker y la misma configuracion del entorno.
Las dos poseen direcciones IP diferentes y estan registradas como destinos
del Application Load Balancer.

La arquitectura implementada es:

```text
                          Internet
                             |
                             | HTTP 80
                             v
                    +------------------+
                    |  alb-condominio  |
                    +---------+--------+
                              |
                         Target Group
                         tg-produccion
                         HTTP : 9000
                              |
                 +------------+------------+
                 |                         |
                 v                         v
        +-----------------+       +-----------------+
        | Produccion 01   |       | Produccion 02   |
        | 172.31.29.4     |       | 172.31.20.248   |
        +--------+--------+       +--------+--------+
                 |                         |
                 +------------+------------+
                              |
                  Red privada de la VPC
                              |
                              v
                     +----------------+
                     | condominio-db  |
                     | 172.31.30.16   |
                     +-------+--------+
                             |
               +-------------+-------------+
               |             |             |
               v             v             v
          PostgreSQL       MySQL        MongoDB
            5432           3306          27017
```

---

## AMI base

Se creo una AMI personalizada para estandarizar el despliegue de las
maquinas virtuales.

| Propiedad | Valor |
|-----------|-------|
| Nombre | `condominio-ubuntu22-docker-v1` |
| AMI ID | `ami-08c6a4d8c4b64e1ce` |
| Sistema operativo | Ubuntu 22.04 LTS |
| Arquitectura | `x86_64` |
| Virtualizacion | `hvm` |
| Dispositivo raiz | EBS |
| Estado | Disponible |
| AMI de origen | `ami-01112e374e42e3f3c` |
| Region | `us-east-1` |

La imagen contiene Docker Engine y Docker Compose previamente instalados.

---

## Maquinas de produccion

### Produccion 1

| Propiedad | Valor |
|-----------|-------|
| Nombre | `condominio-prod-01` |
| Instance ID | `i-0938c1a9322fb928b` |
| Tipo | `t3.micro` |
| IPv4 publica | `3.80.227.46` |
| IPv4 privada | `172.31.29.4` |
| Subnet | `subnet-0ce7fa50be9b1eced` |
| VPC | `vpc-09ade36730213dc98` |
| Key pair | `vockey` |
| Sistema operativo | Ubuntu 22.04 |
| Docker | Instalado y operativo |

### Produccion 2

| Propiedad | Valor |
|-----------|-------|
| Nombre | `condominio-prod-02` |
| Instance ID | `i-0dda04d81590cbc5e` |
| Tipo | `t3.micro` |
| IPv4 publica | `18.232.169.2` |
| IPv4 privada | `172.31.20.248` |
| Subnet | `subnet-0ce7fa50be9b1eced` |
| VPC | `vpc-09ade36730213dc98` |
| AMI | `ami-08c6a4d8c4b64e1ce` |
| Key pair | `vockey` |
| Sistema operativo | Ubuntu 22.04 |
| Docker | Instalado desde la AMI |

---

## Mapa de puertos

El curso asigno el rango **9000-12000** para los microservicios.

### Microservicios

| Microservicio | Publicado | Interno | Lenguaje |
|---------------|-----------|---------|----------|
| ms-residentes | 9001 | 8000 | Python / FastAPI |
| ms-pagos | 9002 | 8080 | Java / Spring Boot |
| ms-incidencias | 9003 | 3003 | Por definir |
| ms-ficha-residente | 9004 | 8004 | Python / FastAPI |
| ms-analitico | 9005 | 8005 | Python / FastAPI |
| ms-usuarios | 9006 | 8000 | Python / FastAPI |

Actualmente se utiliza adicionalmente el puerto `9000` para la prueba
del balanceador de carga entre las dos maquinas de produccion.

---

## VM de base de datos

Se creo una instancia dedicada para los motores de bases de datos.

| Propiedad | Valor |
|-----------|-------|
| Nombre | `condominio-db-01` |
| Instance ID | `i-06c5937b94c257cc6` |
| Tipo | `t2.small` |
| IPv4 publica | `18.215.148.226` |
| IPv4 privada | `172.31.30.16` |
| Subnet | `subnet-0ce7fa50be9b1eced` |
| VPC | `vpc-09ade36730213dc98` |
| AMI | `ami-08c6a4d8c4b64e1ce` |
| Sistema operativo | Ubuntu 22.04 |
| Docker | Instalado y operativo |

Dentro de la VM se ejecutan tres motores de base de datos mediante
contenedores Docker.

| Motor | Imagen | Puerto | Contenedor |
|-------|--------|--------|------------|
| PostgreSQL | `postgres:16` | 5432 | `condominio-postgres` |
| MySQL | `mysql:8.4` | 3306 | `condominio-mysql` |
| MongoDB | `mongo:8` | 27017 | `condominio-mongodb` |

Los tres contenedores fueron comprobados en ejecucion mediante:

```bash
docker ps
```

---

## Volumenes persistentes

Para evitar que la informacion desaparezca al eliminar o recrear los
contenedores, cada motor utiliza un volumen Docker persistente.

| Motor | Volumen |
|-------|---------|
| PostgreSQL | `databases_postgres_data` |
| MySQL | `databases_mysql_data` |
| MongoDB | `databases_mongo_data` |

Los volumenes pueden comprobarse mediante:

```bash
docker volume ls
```

La arquitectura de almacenamiento es:

```text
condominio-db-01
       |
     Docker
       |
 +-----+------+------+
 |            |      |
 v            v      v
PostgreSQL   MySQL  MongoDB
 |            |      |
 v            v      v
postgres     mysql   mongo
_data        _data   _data
```

---

## Bases de datos

| Motor | Puerto | Microservicio que la utiliza |
|-------|--------|-------------------------------|
| PostgreSQL | 5432 | ms-residentes y ms-usuarios |
| MySQL | 3306 | ms-pagos |
| MongoDB | 27017 | ms-incidencias |

PostgreSQL almacena las bases correspondientes a residentes y usuarios
dentro del mismo motor.

---

# Security Groups

Se implementaron cuatro Security Groups independientes.

La regla general de seguridad es evitar exponer directamente las bases de
datos o las maquinas de produccion a Internet.

## Security Groups creados

| Security Group | ID | Funcion |
|----------------|----|---------|
| `sgc-alb` | `sg-0e05ef40c5f5c9352` | Application Load Balancer |
| `sgc-produccion` | `sg-077c86f2a02bd0143` | VM de produccion |
| `sgc-database` | `sg-06f95c6cdd7e6157c` | VM de bases de datos |
| `sgc-ingesta` | `sg-0ddc4d537d6cbdfbb` | Servicios de ingesta |

---

## SG del balanceador

Security Group:

`sgc-alb`

ID:

`sg-0e05ef40c5f5c9352`

El balanceador constituye el punto publico de entrada a la arquitectura.

Las reglas permiten el trafico necesario para acceder al Application
Load Balancer y reenviarlo hacia las maquinas de produccion.

---

## SG de produccion

Security Group:

`sgc-produccion`

ID:

`sg-077c86f2a02bd0143`

Reglas principales:

| Direccion | Puerto | Origen / Destino |
|-----------|--------|------------------|
| Entrada | 9000-12000 | SG del balanceador |
| Entrada | 22 | Acceso SSH autorizado |
| Salida | Todo el trafico | Permitido |

Las dos maquinas de produccion utilizan este Security Group.

---

## SG de base de datos

Security Group:

`sgc-database`

ID:

`sg-06f95c6cdd7e6157c`

Las bases de datos no se encuentran abiertas directamente a Internet.

| Direccion | Puerto | Origen |
|-----------|--------|--------|
| Entrada | 5432 | SG de produccion |
| Entrada | 5432 | SG de ingesta |
| Entrada | 3306 | SG de produccion |
| Entrada | 3306 | SG de ingesta |
| Entrada | 27017 | SG de produccion |
| Entrada | 27017 | SG de ingesta |
| Entrada | 22 | Acceso administrativo autorizado |

Salida:

```text
Todo el trafico
```

Esto permite que la maquina descargue imagenes y actualizaciones cuando
sea necesario.

---

## SG de ingesta

Security Group:

`sgc-ingesta`

ID:

`sg-0ddc4d537d6cbdfbb`

Actualmente se encuentra preparado para la futura VM de ingesta.

Su acceso administrativo se restringe mediante SSH y posteriormente
permitira las conexiones hacia las bases de datos.

---

# VPC

Para esta etapa se decidio utilizar la VPC existente de AWS.

| Propiedad | Valor |
|-----------|-------|
| VPC | `vpc-09ade36730213dc98` |
| CIDR | `172.31.0.0/16` |
| Region | `us-east-1` |

La decision de utilizar la VPC existente permite completar el avance sin
crear infraestructura de red adicional, manteniendo las maquinas dentro
de una misma red privada.

## Subredes utilizadas

| Subnet | Zona | Uso |
|--------|------|-----|
| `subnet-0ce7fa50be9b1eced` | `us-east-1c` | Produccion, base de datos y ALB |
| `subnet-054156b9a67e00e02` | `us-east-1b` | Segunda zona del ALB |

El Application Load Balancer se encuentra desplegado en dos zonas de
disponibilidad.

---

# Application Load Balancer

Se implemento un Application Load Balancer para distribuir las peticiones
entre las dos maquinas virtuales de produccion.

## Balanceador

| Propiedad | Valor |
|-----------|-------|
| Nombre | `alb-condominio` |
| Tipo | Application Load Balancer |
| Esquema | Internet-facing |
| Estado | Activo |
| IP | IPv4 |
| VPC | `vpc-09ade36730213dc98` |
| Security Group | `sg-0e05ef40c5f5c9352` |
| DNS | `alb-condominio-678852222.us-east-1.elb.amazonaws.com` |
| ARN | `arn:aws:elasticloadbalancing:us-east-1:688967828215:loadbalancer/app/alb-condominio/df7165ad3f716c93` |

## Zonas de disponibilidad

El balanceador utiliza dos subredes:

```text
us-east-1c
subnet-0ce7fa50be9b1eced

us-east-1b
subnet-054156b9a67e00e02
```

---

# Target Group

El balanceador utiliza el Target Group:

`tg-produccion`

| Propiedad | Valor |
|-----------|-------|
| Nombre | `tg-produccion` |
| Tipo de destino | Instancia |
| Protocolo | HTTP |
| Puerto | 9000 |
| Version | HTTP/1 |
| VPC | `vpc-09ade36730213dc98` |
| ARN | `arn:aws:elasticloadbalancing:us-east-1:688967828215:targetgroup/tg-produccion/bf9892af5e3da429` |

## Destinos registrados

| Instancia | Nombre | IP privada | Puerto | Estado |
|-----------|--------|------------|--------|--------|
| `i-0938c1a9322fb928b` | `condominio-prod-01` | `172.31.29.4` | 9000 | **Healthy** |
| `i-0dda04d81590cbc5e` | `condominio-prod-02` | `172.31.20.248` | 9000 | **Healthy** |

Resultados actuales:

```text
Destinos totales: 2
Healthy: 2
Unhealthy: 0
```

Por lo tanto, el Application Load Balancer puede distribuir correctamente
las peticiones entre las dos VM de produccion.

---

# Docker Hub

Las imagenes de los microservicios se publicaran en la cuenta u
organizacion Docker Hub definida por el equipo.

| Imagen | Tag | Quien la publica |
|--------|-----|------------------|
| `<org>/ms-residentes` | `0.1.0` | @Osomar1705 |
| `<org>/ms-pagos` | `0.1.0` | @sebastianperez72 |
| `<org>/ms-incidencias` | `0.1.0` | @fabianbot1331 |
| `<org>/ms-ficha-residente` | `0.1.0` | @Brisseth-raton |
| `<org>/ms-analitico` | `0.1.0` | @carloscondor1610 |
| `<org>/ms-usuarios` | `0.1.0` | @Osomar1705 |
| `<org>/ingesta01..03` | `0.1.0` | @carloscondor1610 |

- Cuenta / organizacion Docker Hub: **PENDIENTE DE DEFINIR POR EL EQUIPO**

---

# Inventario de recursos

| Recurso | Identificador | Notas |
|---------|---------------|-------|
| AMI base | `ami-08c6a4d8c4b64e1ce` | Ubuntu 22.04 con Docker y Docker Compose |
| VM produccion 1 | `i-0938c1a9322fb928b` | Publica `3.80.227.46` / Privada `172.31.29.4` |
| VM produccion 2 | `i-0dda04d81590cbc5e` | Publica `18.232.169.2` / Privada `172.31.20.248` |
| VM base de datos | `i-06c5937b94c257cc6` | Publica `18.215.148.226` / Privada `172.31.30.16` |
| VPC | `vpc-09ade36730213dc98` | VPC existente |
| Subnet principal | `subnet-0ce7fa50be9b1eced` | `us-east-1c` |
| Subnet ALB secundaria | `subnet-054156b9a67e00e02` | `us-east-1b` |
| SG ALB | `sg-0e05ef40c5f5c9352` | `sgc-alb` |
| SG Produccion | `sg-077c86f2a02bd0143` | `sgc-produccion` |
| SG Database | `sg-06f95c6cdd7e6157c` | `sgc-database` |
| SG Ingesta | `sg-0ddc4d537d6cbdfbb` | `sgc-ingesta` |
| Load Balancer | `alb-condominio` | Estado activo |
| DNS del ALB | `alb-condominio-678852222.us-east-1.elb.amazonaws.com` | Punto de entrada publico |
| Target Group | `tg-produccion` | 2 destinos Healthy |
| VM ingesta | `PENDIENTE` | Responsable del modulo de ingesta |
| Bucket S3 | `PENDIENTE` | Una carpeta por contenedor de ingesta |
| Base de Glue | `condominio_db` | Catalogo sobre el bucket |

---

# Estado del avance de infraestructura

| Requisito | Estado |
|-----------|--------|
| AMI Ubuntu 22.04 con Docker preinstalado | COMPLETADO |
| 2 VM de produccion | COMPLETADO |
| VM de base de datos | COMPLETADO |
| PostgreSQL | COMPLETADO |
| MySQL | COMPLETADO |
| MongoDB | COMPLETADO |
| Volumen PostgreSQL | COMPLETADO |
| Volumen MySQL | COMPLETADO |
| Volumen MongoDB | COMPLETADO |
| Security Groups | COMPLETADO |
| VPC definida | COMPLETADO |
| Application Load Balancer | COMPLETADO |
| 2 targets Healthy | COMPLETADO |
| Docker Hub del equipo | PENDIENTE |
| VM de ingesta | PENDIENTE / otro integrante |
| S3 / Glue | PENDIENTE / otro integrante |

---

## Confirmado por el ACL

1. La ingesta se conecta directamente a las bases de datos, no a los
   endpoints de los microservicios.
2. Los puertos de las bases quedan reservados:
   - PostgreSQL: `5432`
   - MySQL: `3306`
   - MongoDB: `27017`
3. Usuarios es un microservicio independiente en el puerto `9006`.
4. La base `condominio_usuarios` se ejecutara sobre PostgreSQL.
5. El rango asignado a los microservicios es `9000-12000`.

---

# Recomendaciones antes de la entrega final

## 1. Reemplazar `condominio-prod-01` por una instancia lanzada desde la AMI personalizada

Actualmente `condominio-prod-01` es la instancia original usada para crear
la AMI, por lo que AWS muestra como AMI de origen:

`ami-01112e374e42e3f3c`

mientras que `condominio-prod-02` utiliza:

`ami-08c6a4d8c4b64e1ce`

Funcionalmente ambas tienen la misma configuracion, pero el requisito indica
de forma literal que se deben tener **2 VM de produccion gemelas desde esa AMI**.

Por ello, antes de la revision final se recomienda:

1. Crear una nueva instancia `condominio-prod-01-new`.
2. Lanzarla desde `ami-08c6a4d8c4b64e1ce`.
3. Usar tipo `t3.micro`.
4. Asociarla a `vpc-09ade36730213dc98`.
5. Asociarla a `sgc-produccion`.
6. Levantar el mismo servicio de prueba en el puerto `9000`.
7. Registrar la nueva instancia en `tg-produccion`.
8. Esperar hasta que aparezca como `Healthy`.
9. Retirar del Target Group la instancia antigua `i-0938c1a9322fb928b`.
10. Actualizar este inventario con el nuevo Instance ID e IP.

De esta manera las dos VM de produccion mostraran exactamente la misma
AMI personalizada como origen.

## 2. Revisar la tercera regla de entrada de `sgc-alb`

Actualmente `sgc-alb` presenta tres reglas de entrada.

Antes de entregar se recomienda verificar que solo existan las reglas
realmente necesarias para el balanceador, por ejemplo HTTP y HTTPS.

Si la tercera regla corresponde a SSH o a un puerto que no sea necesario,
debe eliminarse para evitar exponer servicios innecesariamente.
