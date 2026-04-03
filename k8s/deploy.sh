#!/bin/bash
set -e

NS="airflow-datalake"

echo "🚀 Deploying Airflow Data Lake Platform to Kubernetes..."

# Aplica todos os manifests via Kustomize
echo "📦 Applying manifests..."
kubectl apply -k .

# Aguarda Postgres e Redis ficarem prontos
echo "⏳ Waiting for Postgres..."
kubectl wait --for=condition=available deployment/postgres -n $NS --timeout=120s

echo "⏳ Waiting for Redis..."
kubectl wait --for=condition=available deployment/redis -n $NS --timeout=120s

# Executa o Job de init do Airflow
echo "⚙️ Running Airflow DB init..."
kubectl wait --for=condition=complete job/airflow-init -n $NS --timeout=300s 2>/dev/null || true

# Aguarda componentes principais
echo "⏳ Waiting for Airflow API Server..."
kubectl wait --for=condition=available deployment/airflow-apiserver -n $NS --timeout=300s

echo "⏳ Waiting for Pinot Controller..."
kubectl wait --for=condition=available deployment/pinot-controller -n $NS --timeout=300s

echo "⏳ Waiting for StarRocks FE..."
kubectl wait --for=condition=available deployment/starrocks-fe -n $NS --timeout=300s

echo ""
echo "✅ Deploy concluído!"
echo ""
echo "📋 Acessos (via NodePort):"
echo "   • Airflow:    http://localhost:30085 (airflow/airflow)"
echo "   • Pinot:      http://localhost:30010"
echo "   • StarRocks:  mysql -h localhost -P 30930 -u root"
echo "   • MinIO:      http://localhost:30901 (minioadmin/minioadmin)"
echo "   • Superset:   http://localhost:30088 (admin/admin)"
echo ""
echo "📋 Acessos (via port-forward):"
echo "   kubectl port-forward svc/airflow-apiserver 8085:8080 -n $NS"
echo "   kubectl port-forward svc/pinot-controller 9010:9000 -n $NS"
echo "   kubectl port-forward svc/starrocks-fe 9030:9030 -n $NS"
echo ""
echo "📋 Status:"
echo "   kubectl get pods -n $NS"
echo "   kubectl get svc -n $NS"
