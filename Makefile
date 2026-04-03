# Airflow Data Lake Project
COMPOSE_FILE = docker-compose-airflow.yml

# Activate environment
activate:
	source .venv/bin/activate

# Airflow services
up:
	docker-compose -f $(COMPOSE_FILE) up -d

down:
	docker-compose -f $(COMPOSE_FILE) down

init:
	docker-compose -f $(COMPOSE_FILE) up airflow-init

logs:
	docker-compose -f $(COMPOSE_FILE) logs -f

restart:
	make down && make up

rebuild:
	make down && make up

# Open Airflow UI
browse:
	open http://localhost:8080

unit-tests:
	@echo "Running unit tests..."

# ---- Kubernetes ----
K8S_NS = airflow-datalake

k8s-deploy:
	cd k8s && bash deploy.sh

k8s-apply:
	kubectl apply -k k8s/

k8s-delete:
	kubectl delete namespace $(K8S_NS)

k8s-status:
	kubectl get pods -n $(K8S_NS)

k8s-logs:
	kubectl logs -f -l app=airflow-apiserver -n $(K8S_NS)

k8s-forward:
	@echo "Airflow UI: http://localhost:8085"
	kubectl port-forward svc/airflow-apiserver 8085:8080 -n $(K8S_NS)
