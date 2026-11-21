#!/usr/bin/env bash
# Publica la disponibilidad real del microservicio (incluye Oracle) en CloudWatch.
# 1 = /actuator/health responde UP, 0 = DOWN o sin respuesta.
if curl -fsS -m 20 http://localhost:8081/actuator/health | grep -q '"status":"UP"'; then
  VALUE=1
else
  VALUE=0
fi
aws cloudwatch put-metric-data --region us-east-1 \
  --namespace Bdget --metric-name HealthUp --value "$VALUE" --unit Count