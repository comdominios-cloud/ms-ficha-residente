# Infraestructura como codigo

`infra.yaml` es la plantilla de CloudFormation que recrea toda la
infraestructura del proyecto. Se escribio despues de haberla construido a mano
por la consola, que es como pidio el curso: primero entender que hace cada
recurso, despues automatizarlo.

## Que declara

41 recursos:

| Bloque | Recursos |
|--------|----------|
| Red | 5 grupos de seguridad encadenados: cada uno solo acepta al de arriba |
| Computo | 4 instancias EC2: dos de produccion, una de bases, una de ingesta |
| Balanceo | 1 balanceador interno, 6 grupos de destino, 7 reglas de ruteo por ruta |
| Entrada | 1 VPC Link y el API Gateway con su ruta comodin y su etapa |
| Analitica | Bucket del data lake, base del catalogo de Glue, crawler y grupo de trabajo de Athena |

## Como desplegarla

```bash
aws cloudformation deploy \
  --template-file infraestructura/infra.yaml \
  --stack-name condominios \
  --parameter-overrides \
      VpcId=vpc-xxxxxxxx \
      SubredPrincipal=subnet-xxxxxxxx \
      SubredSecundaria=subnet-yyyyyyyy \
      ParDeClaves=mi-par \
      NombreBucket=condominios-data-NUMERODECUENTA \
      IpAdministracion=TU.IP.PU.BLICA/32
```

Al terminar, `aws cloudformation describe-stacks --stack-name condominios` devuelve
la URL del API Gateway y las IP privadas de las cuatro maquinas, que son los
valores que hay que poner en el `.env` de cada microservicio y en la variable
`VITE_API_BASE_URL` de Amplify.

## Lo que la plantilla no hace, a proposito

**No crea la AMI.** `ami-08c6a4d8c4b64e1ce` se armo una vez a mano, con Ubuntu
22.04 y Docker ya instalado. CloudFormation la usa como parametro.

**No crea roles de IAM.** El laboratorio academico no lo permite, asi que el
crawler de Glue reutiliza `LabRole`, que es el unico disponible.

**No instala los contenedores.** La plantilla levanta las maquinas vacias; los
microservicios se despliegan despues con `docker compose`, siguiendo
[docs/runbook-despliegue.md](../docs/runbook-despliegue.md).

## Verificacion

La plantilla pasa `cfn-lint` sin errores:

```bash
pip install cfn-lint
cfn-lint infraestructura/infra.yaml
```
