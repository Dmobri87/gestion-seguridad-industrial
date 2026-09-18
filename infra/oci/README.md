# OCI Infra (Terraform)

Provisiona infraestructura base en Oracle Cloud para este proyecto:

- VCN + subnet pública
- Internet Gateway + route table
- Security list (22/80/443)
- Compute VM (Ampere A1 por defecto)
- Volumen adicional opcional

## Requisitos

1. Terraform `>= 1.5`
2. Credenciales OCI (API key) configuradas
3. Archivo `terraform.tfvars` basado en `terraform.tfvars.example`

## Uso rápido

```bash
cd infra/oci
cp terraform.tfvars.example terraform.tfvars
# editar terraform.tfvars con tus OCIDs y valores reales

terraform init
terraform plan
terraform apply
```

## Después del apply

1. Toma el output `public_ip`
2. Espera cloud-init:
```bash
ssh ubuntu@<public_ip>
sudo cloud-init status --wait
```
3. Despliega app:
```bash
cd /opt/gestion_proyectos
bash scripts/oci/deploy.sh
```

## Seguridad recomendada

- Cambiar `allowed_ssh_cidr` a tu IP pública `/32`
- No exponer `5432` ni `6379`
- Configurar DNS + HTTPS antes de producción pública

