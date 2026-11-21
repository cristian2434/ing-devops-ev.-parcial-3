#!/usr/bin/env python3
"""Auditoria automatizada de politicas sobre los manifiestos de Kubernetes.

Falla (exit 1) si un Deployment incumple alguna politica. Se ejecuta en el
pipeline ANTES de construir y desplegar, y se puede probar en local:
    python3 scripts/audit-k8s.py k8s

Politicas (cada una con su codigo):
  P01 La imagen debe tener etiqueta fija (no :latest ni sin etiqueta)
  P02 requests de cpu y memoria definidos
  P03 limits de cpu y memoria definidos
  P04 livenessProbe definida
  P05 readinessProbe definida
  P06 securityContext.runAsNonRoot = true
  P07 allowPrivilegeEscalation = false
  P08 capabilities.drop incluye ALL
  P09 No se permite privileged ni hostNetwork
"""
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("Falta PyYAML: pip install pyyaml")

PLACEHOLDER = "__APP_IMAGE__"  # el pipeline lo reemplaza por ghcr.io/...:<SHA>


def load_docs(folder):
    for name in sorted(os.listdir(folder)):
        if name.endswith((".yaml", ".yml")):
            path = os.path.join(folder, name)
            with open(path, encoding="utf-8") as fh:
                for doc in yaml.safe_load_all(fh):
                    if isinstance(doc, dict):
                        yield path, doc


def image_ok(image):
    if not image:
        return False
    if image == PLACEHOLDER:
        return True
    ref = image.split("@")[0]
    if "@sha256:" in image:
        return True
    last = ref.rsplit("/", 1)[-1]
    return ":" in last and not last.endswith(":latest")


def audit_container(c, pod_spec):
    sc = c.get("securityContext") or {}
    pod_sc = pod_spec.get("securityContext") or {}
    res = c.get("resources") or {}
    req, lim = res.get("requests") or {}, res.get("limits") or {}
    drop = [str(x).upper() for x in (sc.get("capabilities") or {}).get("drop", [])]
    run_non_root = sc.get("runAsNonRoot", pod_sc.get("runAsNonRoot"))
    return [
        ("P01", "Imagen con etiqueta fija (sin :latest)", image_ok(c.get("image"))),
        ("P02", "requests de cpu y memoria", bool(req.get("cpu")) and bool(req.get("memory"))),
        ("P03", "limits de cpu y memoria", bool(lim.get("cpu")) and bool(lim.get("memory"))),
        ("P04", "livenessProbe", "livenessProbe" in c),
        ("P05", "readinessProbe", "readinessProbe" in c),
        ("P06", "runAsNonRoot = true", run_non_root is True),
        ("P07", "allowPrivilegeEscalation = false", sc.get("allowPrivilegeEscalation") is False),
        ("P08", "capabilities.drop incluye ALL", "ALL" in drop),
        ("P09", "Sin privileged ni hostNetwork",
         not sc.get("privileged") and not pod_spec.get("hostNetwork")),
    ]


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "k8s"
    failures, total_workloads = 0, 0
    lines = ["| Recurso | Politica | Resultado |", "|---|---|---|"]

    for path, doc in load_docs(folder):
        kind = doc.get("kind")
        if kind not in ("Deployment", "StatefulSet", "DaemonSet"):
            continue
        total_workloads += 1
        name = (doc.get("metadata") or {}).get("name", "?")
        pod_spec = doc["spec"]["template"]["spec"]
        for c in pod_spec.get("containers", []):
            for code, desc, ok in audit_container(c, pod_spec):
                status = "OK" if ok else "FALLA"
                if not ok:
                    failures += 1
                    print(f"::error file={path}::{kind}/{name} contenedor '{c.get('name')}' incumple {code}: {desc}")
                print(f"[{status:5}] {os.path.basename(path)} {kind}/{name}/{c.get('name')} {code} {desc}")
                lines.append(f"| {kind}/{name} ({c.get('name')}) | {code} {desc} | {'OK' if ok else 'FALLA'} |")

    if total_workloads == 0:
        print("::error::No se encontro ningun Deployment para auditar")
        return 1

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("### Auditoria de politicas de Kubernetes\n\n" + "\n".join(lines) + "\n")

    print(f"\nResultado: {failures} incumplimiento(s) en {total_workloads} workload(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())