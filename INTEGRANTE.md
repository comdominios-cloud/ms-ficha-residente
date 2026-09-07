# Integrante responsable

| | |
|---|---|
| **Repositorio** | `ms-ficha-residente` |
| **Integrante** | [@Brisseth-raton](https://github.com/Brisseth-raton) |
| **Rol** | Backend / Infraestructura |
| **Puerto** | 9004 publicado, 8004 interno |

## Alcance

`ms-ficha-residente` (el consumidor de las 3 APIs) **y toda la infraestructura del proyecto**: VPC, Security Groups, las VM y el mapa de puertos. Ver [docs/infra.md](docs/infra.md).

> ### La infra es lo tuyo, el microservicio va despues
>
> `ms-ficha-residente` recien tiene sentido cuando existan 2 de las 3 APIs. Para
> el avance del 50% lo que se evalua de tu lado son las **maquinas virtuales y
> los Security Groups**, no este microservicio.
>
> El ACL marco la definicion de puertos como *"tarea complicada"*, y fue
> explicito en que el origen de las reglas **nunca puede ser `0.0.0.0/0`**
> salvo en el balanceador.

## Avance del 50% — entrega del 6 al 12 de septiembre

### Infraestructura (lo prioritario)

- [ ] **AMI Ubuntu 22.04** con Docker preinstalado
- [ ] **2 VM de produccion gemelas** desde esa AMI: identicas, distinta IP
- [ ] **1 VM de base de datos** con los **3 contenedores** (PostgreSQL, MySQL, MongoDB) y sus volumenes
- [ ] **Security Groups** segun [docs/infra.md](docs/infra.md): entrada 9000-12000 a produccion; 5432/3306/27017 solo desde los SG de produccion e ingesta; SSH solo desde la IP del equipo; salida todo el trafico
- [ ] Definir la **VPC** (usar la existente o crear una) y anotarlo en el inventario
- [ ] Cuenta/organizacion de **Docker Hub** del equipo, y compartirla con todos
- [ ] Completar el inventario de recursos de [docs/infra.md](docs/infra.md) con IPs e ids reales
- [ ] Balanceador repartiendo entre las 2 VM de produccion

### Microservicio (despues del avance)

- [ ] Clientes httpx hacia `:9001`, `:9002` y `:9003`
- [ ] Endpoints de ficha consolidada, publicados en el **9004**

---

## Como trabajamos

Cada repositorio pertenece a un integrante y se desarrolla de forma
**independiente**: las APIs con base de datos no se llaman entre si. La unica
integracion entre microservicios vive en `ms-ficha-residente`, y la del lado del
usuario en `web-condominio`.

Los cambios a este repositorio los define su responsable. Si otro integrante
necesita algo de esta API, se pide via issue en vez de tocar el codigo.

## Equipo

| Repositorio | Integrante | Rol | Puerto |
|---|---|---|---|
| [ms-residentes](https://github.com/comdominios-cloud/ms-residentes) | @Osomar1705 | API con BD - Python / PostgreSQL | 9001 |
| [ms-pagos](https://github.com/comdominios-cloud/ms-pagos) | @sebastianperez72 | API con BD - Java / MySQL | 9002 |
| [ms-incidencias](https://github.com/comdominios-cloud/ms-incidencias) | @fabianbot1331 | API con BD - lenguaje por definir / MongoDB | 9003 |
| [ms-ficha-residente](https://github.com/comdominios-cloud/ms-ficha-residente) | @Brisseth-raton | Backend / Infraestructura | 9004 |
| [web-condominio](https://github.com/comdominios-cloud/web-condominio) | @alxgr-08 | Frontend / Amplify | 5173 (dev) |
| [ms-analitico](https://github.com/comdominios-cloud/ms-analitico) | @carloscondor1610 | Data Science | 9005 |
| [ingesta-datos](https://github.com/comdominios-cloud/ingesta-datos) | @carloscondor1610 | Data Science | — |

> CS2032 Cloud Computing - UTEC | Sistema de Administracion de Condominios
