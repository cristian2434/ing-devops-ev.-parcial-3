#!/usr/bin/env bash
# Se ejecuta EN la EC2 (por SSH desde el pipeline). Usa el rol de la instancia
# (LabInstanceProfile), por eso no hacen falta credenciales de AWS en GitHub.
# Uso: publish-observability.sh <segundos_de_despliegue> <cobertura_porcentaje>
set -euo pipefail

DURATION="${1:?falta el tiempo de despliegue}"
COVERAGE="${2:?falta la cobertura}"
REGION="us-east-1"
DASHBOARD="Bdget-Observabilidad"

TOKEN=$(curl -sS -X PUT http://169.254.169.254/latest/api/token \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
INSTANCE_ID=$(curl -sS -H "X-aws-ec2-metadata-token: ${TOKEN}" \
  http://169.254.169.254/latest/meta-data/instance-id)

echo "Instancia: ${INSTANCE_ID} | despliegue: ${DURATION}s | cobertura: ${COVERAGE}%"

# 1) Metricas del pipeline
aws cloudwatch put-metric-data --region "${REGION}" --namespace Bdget/Pipeline \
  --metric-data \
    "MetricName=DeployDurationSeconds,Value=${DURATION},Unit=Seconds" \
    "MetricName=CoveragePercent,Value=${COVERAGE},Unit=Percent"

# 2) Dashboard versionado en el repo (monitoring/dashboard.json)
sed "s/__INSTANCE_ID__/${INSTANCE_ID}/g" /tmp/dashboard.json > /tmp/dashboard.rendered.json
aws cloudwatch put-dashboard --region "${REGION}" \
  --dashboard-name "${DASHBOARD}" \
  --dashboard-body file:///tmp/dashboard.rendered.json

# 3) Disponibilidad: un temporizador de systemd envia HealthUp cada minuto
sudo install -D -m 755 /tmp/health-metric.sh /opt/bdget/health-metric.sh
sudo tee /etc/systemd/system/bdget-health.service > /dev/null <<'UNIT'
[Unit]
Description=Publica la disponibilidad de bdget en CloudWatch

[Service]
Type=oneshot
ExecStart=/opt/bdget/health-metric.sh
UNIT
sudo tee /etc/systemd/system/bdget-health.timer > /dev/null <<'UNIT'
[Unit]
Description=Disponibilidad de bdget cada minuto

[Timer]
OnBootSec=60s
OnUnitActiveSec=60s

[Install]
WantedBy=timers.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now bdget-health.timer

rm -f /tmp/dashboard.json /tmp/dashboard.rendered.json /tmp/health-metric.sh
echo "Metricas y dashboard ${DASHBOARD} publicados."