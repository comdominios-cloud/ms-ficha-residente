# Diagrama de Arquitectura de Solucion

El archivo editable es [arquitectura.drawio](arquitectura.drawio). Se abre en
[app.diagrams.net](https://app.diagrams.net) con **File > Open From > Device**,
o directamente en VS Code con la extension *Draw.io Integration*.

Para el informe conviene exportarlo con **File > Export as > PNG**, marcando
*Transparent background* desactivado y un zoom de 200%.

## Que incluye

Los tres bloques que pide el enunciado:

### Backend

- **API Gateway** — unico punto publico, entrega HTTPS
- **Application Load Balancer** interno, con ruteo por ruta
- **2 EC2 de produccion** gemelas, lanzadas desde la misma AMI, con los
  6 microservicios en Docker Compose
- **1 EC2 de base de datos**, privada, con PostgreSQL, MySQL y MongoDB en
  contenedores y volumenes persistentes

### Frontend

- **AWS Amplify** sirviendo la SPA de React

### Data Science

- **1 EC2 de ingesta** con los 3 contenedores Python
- **Amazon S3** como data lake
- **AWS Glue** catalogando los archivos
- **Amazon Athena** ejecutando las consultas y vistas

## Por que el balanceador es interno

El enunciado lo pide explicito: *"balanceador de carga (privado, no publico)"*
y *"deben exponerse las Apis publicamente con https con el servicio AWS Api
Gateway"*.

O sea que el unico recurso alcanzable desde internet es el API Gateway. El
balanceador y las maquinas de produccion viven dentro de la VPC, y las bases de
datos no aceptan conexiones que no vengan de los grupos de seguridad de
produccion o de ingesta.

## Los dos caminos del dato

El diagrama muestra dos recorridos distintos, y conviene explicarlos asi en la
exposicion:

**En linea.** El usuario pide algo en la web, la peticion entra por el API
Gateway, el balanceador la manda al microservicio correspondiente y este
consulta su base. Milisegundos.

**Analitico.** Los contenedores de ingesta leen las tres bases, vuelcan todo a
S3, Glue lo cataloga y Athena permite consultarlo junto. Es la unica forma de
cruzar informacion entre las tres bases, porque cada microservicio solo ve la
suya.
