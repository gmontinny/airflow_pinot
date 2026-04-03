# Airflow Data Lake — Spark Connect, Apache Pinot, StarRocks & mais

Plataforma de dados moderna orquestrada por **Apache Airflow 3.x** com processamento distribuído via **Spark Connect**, OLAP em tempo real com **Apache Pinot**, analytics com **StarRocks** e um ecossistema completo de streaming, object storage e visualização.

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ORQUESTRAÇÃO                                   │
│                     Apache Airflow 3.1.8                                │
│          (API Server · Scheduler · Worker · Triggerer)                  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
┌──────────────────┐ ┌─────────────────┐ ┌──────────────────┐
│  Fontes de Dados │ │  Processamento  │ │   Armazenamento  │
│                  │ │                 │ │                  │
│ • APIs (IBGE)    │ │ Spark Connect   │ │ • MinIO (S3)     │
│ • Kafka          │ │ (gRPC :15002)   │ │ • Spark Warehouse│
│ • Arquivos CSV   │ │                 │ │                  │
└──────────────────┘ └────────┬────────┘ └──────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
┌────────────────┐  ┌─────────────────┐  ┌───────────────┐
│  Apache Pinot  │  │   StarRocks     │  │ Elasticsearch │
│  (OLAP Real-   │  │   (Analytics    │  │ (Full-text    │
│   time :9010)  │  │    OLAP :9030)  │  │  Search)      │
└───────┬────────┘  └────────┬────────┘  └───────┬───────┘
        │                    │                   │
        └────────────┬───────┘                   │
                     ▼                           ▼
            ┌─────────────────┐         ┌───────────────┐
            │    Superset     │         │   Logstash    │
            │  (BI :8088)     │         │   (Pipeline)  │
            └─────────────────┘         └───────────────┘

┌──────────────────┐  ┌──────────────────┐
│     Neo4j        │  │     Kafka        │
│  (Graph :7474)   │  │  (Stream :9092)  │
└──────────────────┘  └──────────────────┘
```

---

## Serviços e Portas

| Serviço | Porta | Descrição |
|---|---|---|
| Airflow UI / API | [localhost:8085](http://localhost:8085) | Interface web e API REST do Airflow |
| Apache Pinot UI | [localhost:9010](http://localhost:9010) | Console do Pinot (query SQL, schemas, tabelas) |
| Pinot Broker | localhost:8099 | Endpoint de queries SQL do Pinot |
| Pinot Server | localhost:8098 | Processamento e armazenamento de segmentos |
| StarRocks FE | [localhost:8030](http://localhost:8030) | Frontend do StarRocks |
| StarRocks MySQL | localhost:9030 | Protocolo MySQL do StarRocks |
| Superset | [localhost:8088](http://localhost:8088) | Dashboards e visualização |
| Spark Connect | localhost:15002 | gRPC do Spark Connect |
| Spark UI | [localhost:4040](http://localhost:4040) | Interface de monitoramento do Spark |
| MinIO Console | [localhost:9001](http://localhost:9001) | Object storage (compatível S3) |
| MinIO API | localhost:9000 | API S3 do MinIO |
| Kafka | localhost:9092 | Broker de mensagens |
| Schema Registry | localhost:8081 | Registry de schemas Avro/JSON |
| Elasticsearch | localhost:9200 | Motor de busca e analytics |
| Logstash | localhost:5000 / 9600 | Pipeline de ingestão de logs |
| Neo4j Browser | [localhost:7474](http://localhost:7474) | Banco de dados de grafos |
| Neo4j Bolt | localhost:7687 | Protocolo Bolt do Neo4j |
| ZooKeeper (Kafka) | localhost:2181 | Coordenação do Kafka |
| ZooKeeper (Pinot) | localhost:2182 | Coordenação do Pinot |

---

## Pré-requisitos

- **Docker** ≥ 24.0 e **Docker Compose** ≥ 2.20
- Mínimo **8 GB de RAM** alocados para o Docker (recomendado 12 GB+)
- Mínimo **2 CPUs**
- Mínimo **10 GB de disco** livre
- (Opcional) **VS Code** com extensão Dev Containers para desenvolvimento

---

## Estrutura do Projeto

```
airflow_pinot/
├── .devcontainer/
│   ├── devcontainer.json      # Configuração do Dev Container (VS Code)
│   └── Dockerfile             # Imagem de desenvolvimento com uv + deps
├── config/
│   └── airflow.cfg            # Configuração customizada do Airflow
├── dags/
│   └── ibge_pinot_starrocks.py  # DAG: IBGE → Spark → Pinot + StarRocks
├── data/                      # Dados de entrada (CSV, etc.)
├── docs/                      # Documentação adicional
├── logs/                      # Logs do Airflow (gerado automaticamente)
├── minio_data/                # Dados persistidos do MinIO
├── plugins/                   # Plugins customizados do Airflow
├── spark-connect/
│   ├── conf/
│   │   ├── core-site.xml      # Configuração Hadoop/S3
│   │   └── spark-defaults.conf # Configuração padrão do Spark
│   └── Dockerfile             # Imagem Spark Connect 4.0.1
├── k8s/                       # Manifests Kubernetes (Kustomize)
│   ├── kustomization.yaml
│   ├── deploy.sh
│   └── base/                  # Airflow, Pinot, StarRocks, Kafka, Storage, Observability
├── .env                       # Variáveis de ambiente
├── docker-compose-airflow.yml # Composição de todos os serviços
├── Makefile                   # Atalhos de comandos
├── pyproject.toml             # Dependências Python (uv/hatch)
├── requirements.txt           # Dependências Python (pip)
├── setup-airflow.sh           # Script de setup inicial
└── README.md                  # Este arquivo
```

---

## Início Rápido

### 1. Clonar e configurar

```bash
git clone <repo-url>
cd airflow_pinot
```

O arquivo `.env` já vem configurado com valores padrão:

```env
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
KAFKA_BROKERS=kafka:9093
KAFKA_SCHEMA_REGISTRY=http://schema-registry:8081
ELASTICSEARCH_HOST=http://elasticsearch:9200
SPARK_CONNECT_URL=sc://spark-connect:15002
PINOT_CONTROLLER_URL=http://pinot-controller:9000
AIRFLOW_UID=50000
AIRFLOW_PROJ_DIR=.
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow
```

### 2. Setup automático

```bash
chmod +x setup-airflow.sh
./setup-airflow.sh
```

Esse script cria os diretórios, ajusta permissões, inicializa o banco do Airflow e sobe todos os serviços.

### 3. Setup manual (alternativa)

```bash
# Criar diretórios
mkdir -p dags logs plugins config

# Ajustar permissões (Linux)
sudo chown -R 50000:0 dags/ logs/ plugins/ config/

# Inicializar Airflow (migra banco + cria usuário admin)
make init

# Subir todos os serviços
make up
```

### 4. Verificar se tudo subiu

```bash
# Ver status dos containers
docker compose -f docker-compose-airflow.yml ps

# Acompanhar logs
make logs
```

Aguarde ~2-3 minutos para todos os serviços ficarem healthy. O StarRocks BE demora um pouco mais para registrar no FE (~30-60s após o FE ficar healthy).

---

## Usando o Dev Container (VS Code)

O projeto inclui configuração completa para desenvolvimento dentro de um container.

### Abrir no Dev Container

1. Abra o projeto no VS Code
2. Instale a extensão **Dev Containers** (`ms-vscode-remote.remote-containers`)
3. Pressione `F1` → **Dev Containers: Reopen in Container**
4. O VS Code vai buildar a imagem e subir todos os serviços automaticamente

O Dev Container:
- Usa o serviço `airflow-worker` como container principal
- Sobe todos os serviços definidos em `runServices` (incluindo Pinot)
- Instala extensões Python, Ruff, Jupyter, Docker
- Executa `uv sync --locked && uv run pre-commit install` no `postCreateCommand`
- Workspace fica em `/opt/airflow/dags`

### Serviços incluídos no Dev Container

Postgres, Redis, Airflow (apiserver, scheduler, dag-processor, worker, triggerer), ZooKeeper, Kafka, Schema Registry, MinIO, StarRocks (FE + BE), Superset, Spark Connect, Elasticsearch, Logstash, Neo4j, **Pinot** (zookeeper, controller, broker, server).

---

## DAG de Exemplo: IBGE → Spark → Pinot + StarRocks

A DAG `ibge_pinot_starrocks` demonstra um pipeline completo de ingestão, transformação e carga em dois motores OLAP.

### Fonte de Dados

API pública do IBGE — [Aglomerações Urbanas](https://servicodados.ibge.gov.br/api/v1/localidades/aglomeracoes-urbanas)

Retorna milhares de registros com estrutura aninhada:

```json
{
  "id": "00301",
  "nome": "Aglomeração Urbana de Franca",
  "municipios": [
    {
      "id": 3503000,
      "nome": "Aramina",
      "UF": {
        "id": 35,
        "sigla": "SP",
        "nome": "São Paulo",
        "regiao": { "id": 3, "sigla": "SE", "nome": "Sudeste" }
      }
    }
  ]
}
```

### Fluxo da DAG

```
extract_ibge ──→ transform_spark ──┬──→ setup_pinot_table ──→ load_pinot
                                   │
                                   └──→ setup_starrocks ──→ load_starrocks
```

| Task | Descrição |
|---|---|
| `extract_ibge` | Consome a API REST do IBGE e retorna o JSON bruto |
| `transform_spark` | Conecta ao Spark via gRPC (Spark Connect), faz explode do array de municípios e flatten de toda a hierarquia (UF, região) em colunas planas |
| `setup_pinot_table` | Cria schema e tabela OFFLINE no Apache Pinot via REST API do Controller |
| `load_pinot` | Ingere os dados no Pinot via endpoint `/ingestFromFile` (multipart file upload em NDJSON) |
| `setup_starrocks` | Cria database `demo_ibge` e tabela no StarRocks via protocolo MySQL (`pymysql`). Aguarda o BE estar alive com retry automático |
| `load_starrocks` | Carrega os dados transformados no StarRocks via Spark JDBC |

### Detalhes técnicos da DAG

- **Pinot**: a ingestão usa multipart file upload (`files=`) no endpoint `/ingestFromFile` do Controller, com dados em formato NDJSON
- **StarRocks**: o DDL é executado via `pymysql` (protocolo MySQL na porta 9030), pois a API HTTP do StarRocks não suporta DDL de forma confiável. A task `setup_starrocks` verifica se há backends alive (`SHOW BACKENDS`) antes de criar a tabela, com `retries=10` e `retry_delay=20s` para aguardar o BE registrar no FE
- **StarRocks tabela**: usa `BUCKETS 1` e `replication_num=1` pois o ambiente Docker tem apenas 1 backend

### Schema resultante (flatten)

| Coluna | Tipo | Origem |
|---|---|---|
| `aglomeracao_id` | STRING | `id` da aglomeração |
| `aglomeracao_nome` | STRING | `nome` da aglomeração |
| `municipio_id` | INT | `municipios[].id` |
| `municipio_nome` | STRING | `municipios[].nome` |
| `uf_id` | INT | `municipios[].UF.id` |
| `uf_sigla` | STRING | `municipios[].UF.sigla` |
| `uf_nome` | STRING | `municipios[].UF.nome` |
| `regiao_id` | INT | `municipios[].UF.regiao.id` |
| `regiao_sigla` | STRING | `municipios[].UF.regiao.sigla` |
| `regiao_nome` | STRING | `municipios[].UF.regiao.nome` |

### Executar a DAG

1. Acesse o Airflow em [localhost:8085](http://localhost:8085) (usuário: `airflow`, senha: `airflow`)
2. Ative a DAG `ibge_pinot_starrocks`
3. Clique em **Trigger DAG** para executar manualmente
4. Aguarde todas as 6 tasks ficarem verdes (~1-2 min)

---

## Consultar Dados no Pinot

Acesse o Pinot Query Console em [localhost:9010](http://localhost:9010) e execute:

```sql
-- Todos os registros
SELECT * FROM ibge_aglomeracoes LIMIT 10

-- Total de municípios por região
SELECT regiao_nome, COUNT(*) AS total
FROM ibge_aglomeracoes
GROUP BY regiao_nome
LIMIT 10

-- Municípios de São Paulo
SELECT municipio_nome, aglomeracao_nome
FROM ibge_aglomeracoes
WHERE uf_sigla = 'SP'
LIMIT 20

-- Aglomerações com mais municípios
SELECT aglomeracao_nome, COUNT(*) AS qtd_municipios
FROM ibge_aglomeracoes
GROUP BY aglomeracao_nome
ORDER BY qtd_municipios DESC
LIMIT 10
```

> **Nota**: O Pinot tem algumas diferenças em relação ao SQL padrão. `ORDER BY` em queries com `GROUP BY` funciona a partir de versões recentes. Se uma query com `ORDER BY` não funcionar, remova-o e use apenas `LIMIT`.

---

## Consultar Dados no StarRocks

### Via linha de comando

```bash
mysql -h 127.0.0.1 -P 9030 -u root

USE demo_ibge;
SELECT regiao_nome, COUNT(*) AS total FROM ibge_aglomeracoes GROUP BY regiao_nome ORDER BY total DESC;
```

### Via Docker (sem MySQL client local)

```bash
docker compose -f docker-compose-airflow.yml exec starrocks-fe-0 \
  mysql -h 127.0.0.1 -P 9030 -u root -e \
  "SELECT regiao_nome, COUNT(*) AS total FROM demo_ibge.ibge_aglomeracoes GROUP BY regiao_nome ORDER BY total DESC"
```

---

## Conectar ao StarRocks via IDEs

O StarRocks é compatível com o **protocolo MySQL**. Qualquer IDE ou ferramenta que conecte em MySQL funciona com o StarRocks.

### Parâmetros de conexão

| Parâmetro | Valor |
|---|---|
| **Host** | `localhost` (ou `127.0.0.1`) |
| **Porta** | `9030` |
| **Usuário** | `root` |
| **Senha** | *(vazio — deixe em branco)* |
| **Database** | `demo_ibge` |
| **Driver** | MySQL (Connector/J) |
| **JDBC URL** | `jdbc:mysql://localhost:9030/demo_ibge` |

### DataGrip (JetBrains)

1. **+** → **Data Source** → **MySQL**
2. Preencha:
   - Host: `localhost`
   - Port: `9030`
   - User: `root`
   - Password: *(vazio)*
   - Database: `demo_ibge`
3. Aba **Driver**: use o MySQL Connector/J (já incluso no DataGrip)
4. **Test Connection** → **OK**

### DBeaver

1. **Nova Conexão** → **MySQL**
2. Preencha:
   - Server Host: `localhost`
   - Port: `9030`
   - Username: `root`
   - Password: *(vazio)*
   - Database: `demo_ibge`
3. Aba **Driver properties**: se necessário, defina `allowPublicKeyRetrieval=true`
4. **Test Connection** → **Finish**

### VS Code (extensão MySQL)

1. Instale a extensão **MySQL** (`cweijan.vscode-mysql-client2`) ou **Database Client**
2. **+** → **MySQL**
3. Preencha:
   - Host: `localhost`
   - Port: `9030`
   - Username: `root`
   - Password: *(vazio)*
   - Database: `demo_ibge`
4. **Connect**

### IntelliJ IDEA / PyCharm

1. **View** → **Tool Windows** → **Database**
2. **+** → **Data Source** → **MySQL**
3. Preencha:
   - Host: `localhost`
   - Port: `9030`
   - User: `root`
   - Password: *(vazio)*
   - Database: `demo_ibge`
4. **Download Driver** (se solicitado) → **Test Connection** → **OK**

### Python (pymysql)

```python
import pymysql

conn = pymysql.connect(host="localhost", port=9030, user="root", password="")
with conn.cursor() as cur:
    cur.execute("SELECT regiao_nome, COUNT(*) AS total FROM demo_ibge.ibge_aglomeracoes GROUP BY regiao_nome")
    for row in cur.fetchall():
        print(row)
conn.close()
```

### Python (SQLAlchemy)

```python
from sqlalchemy import create_engine, text

engine = create_engine("mysql+pymysql://root:@localhost:9030/demo_ibge")
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM ibge_aglomeracoes LIMIT 10"))
    for row in result:
        print(row)
```

### Superset

1. Acesse [localhost:8088](http://localhost:8088) (admin/admin)
2. **Settings** → **Database Connections** → **+ Database**
3. Selecione **MySQL** (ou **Other**)
4. SQLAlchemy URI: `mysql+pymysql://root:@starrocks-fe-0:9030/demo_ibge`
   - Use `starrocks-fe-0` (hostname interno) se o Superset roda dentro do Docker
   - Use `localhost` se acessando de fora do Docker
5. **Test Connection** → **Connect**

### Query de teste (funciona em qualquer IDE)

```sql
-- Total de municípios por região
SELECT regiao_nome, COUNT(*) AS total
FROM ibge_aglomeracoes
GROUP BY regiao_nome
ORDER BY total DESC;

-- Municípios de São Paulo
SELECT municipio_nome, aglomeracao_nome
FROM ibge_aglomeracoes
WHERE uf_sigla = 'SP'
LIMIT 20;

-- Aglomerações com mais municípios
SELECT aglomeracao_nome, COUNT(*) AS qtd_municipios
FROM ibge_aglomeracoes
GROUP BY aglomeracao_nome
ORDER BY qtd_municipios DESC
LIMIT 10;
```

---

## Apache Pinot — Arquitetura

O Pinot é composto por 4 componentes, cada um rodando em seu próprio container:

```
                    ┌──────────────────┐
                    │  ZooKeeper       │
                    │  (pinot-zk:2182) │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌──────────────┐ ┌───────────┐ ┌────────────┐
     │  Controller  │ │  Broker   │ │   Server   │
     │  (:9010)     │ │  (:8099)  │ │  (:8098)   │
     │              │ │           │ │            │
     │ • Schemas    │ │ • Routing │ │ • Segments │
     │ • Tables     │ │ • Queries │ │ • Storage  │
     │ • Segments   │ │ • Scatter │ │ • Index    │
     │   metadata   │ │   Gather  │ │            │
     └──────────────┘ └───────────┘ └────────────┘
```

- **ZooKeeper** — Coordenação e service discovery (porta 2182, separado do ZK do Kafka)
- **Controller** — Gerencia schemas, tabelas e metadados de segmentos. Expõe a UI web na porta 9010
- **Broker** — Recebe queries SQL, roteia para os servers e agrega resultados (porta 8099)
- **Server** — Armazena os segmentos de dados e executa o processamento local (porta 8098)

---

## StarRocks — Arquitetura

O StarRocks roda com 2 componentes principais + um container auxiliar de registro:

```
     ┌──────────────────┐
     │  Frontend (FE)   │
     │  (:8030 / :9030) │
     │                  │
     │ • Query parsing  │
     │ • Metadata       │
     │ • MySQL protocol │
     └────────┬─────────┘
              │
     ┌────────▼─────────┐
     │  Backend (BE)    │
     │  (:8040)         │
     │                  │
     │ • Data storage   │
     │ • Query exec     │
     │ • Tablets        │
     └──────────────────┘
```

- **FE (Frontend)** — Recebe queries via protocolo MySQL (porta 9030), gerencia metadados, UI web (porta 8030)
- **BE (Backend)** — Armazena dados e executa queries. Registra-se automaticamente no FE via `be_entrypoint.sh`
- **starrocks-add-be** — Container auxiliar que garante o registro do BE no FE via `ALTER SYSTEM ADD BACKEND`

> **Nota**: O BE demora ~30-60s para ficar `Alive` após o FE estar healthy. A DAG lida com isso via retries automáticos na task `setup_starrocks`.

---

## Deploy no Kubernetes

O projeto inclui manifests Kubernetes completos com Kustomize em `k8s/`.

```bash
# Deploy automatizado
cd k8s && bash deploy.sh

# Ou via Makefile
make k8s-deploy

# Ou manualmente
kubectl apply -k k8s/
```

### Acessos via NodePort

| Serviço | NodePort |
|---|---|
| Airflow UI | [localhost:30085](http://localhost:30085) |
| Pinot UI | [localhost:30010](http://localhost:30010) |
| StarRocks MySQL | `mysql -h localhost -P 30930 -u root` |
| MinIO Console | [localhost:30901](http://localhost:30901) |
| Superset | [localhost:30088](http://localhost:30088) |

```bash
# Status dos pods
make k8s-status

# Logs do Airflow
make k8s-logs

# Remover tudo
make k8s-delete
```

---

## Comandos Úteis

```bash
# Subir todos os serviços
make up

# Parar todos os serviços
make down

# Reiniciar
make restart

# Ver logs em tempo real
make logs

# Inicializar Airflow (primeira vez)
make init

# Logs de um serviço específico
docker compose -f docker-compose-airflow.yml logs -f pinot-controller
docker compose -f docker-compose-airflow.yml logs -f spark-connect
docker compose -f docker-compose-airflow.yml logs -f starrocks-be-0

# Verificar saúde do Pinot
curl http://localhost:9010/health
curl http://localhost:8099/health

# Listar tabelas do Pinot
curl http://localhost:9010/tables

# Query no Pinot via API
curl -X POST http://localhost:8099/query/sql \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT COUNT(*) FROM ibge_aglomeracoes"}'

# Verificar backends do StarRocks
docker compose -f docker-compose-airflow.yml exec starrocks-fe-0 \
  mysql -h 127.0.0.1 -P 9030 -u root -e "SHOW BACKENDS\G"

# Query no StarRocks via Docker
docker compose -f docker-compose-airflow.yml exec starrocks-fe-0 \
  mysql -h 127.0.0.1 -P 9030 -u root -e \
  "SELECT COUNT(*) FROM demo_ibge.ibge_aglomeracoes"

# Limpar volumes do StarRocks (reset completo)
make down
docker volume rm airflow_pinot_singleton_fe0_data airflow_pinot_singleton_be0_data
make up
```

---

## Credenciais Padrão

| Serviço | Usuário | Senha |
|---|---|---|
| Airflow | `airflow` | `airflow` |
| MinIO | `minioadmin` | `minioadmin` |
| Neo4j | `neo4j` | `password` |
| Superset | `admin` | `admin` |
| StarRocks | `root` | *(vazio)* |

---

## Tecnologias

| Componente | Versão | Papel |
|---|---|---|
| Apache Airflow | 3.1.8 | Orquestração de pipelines |
| Apache Spark | 4.0.1 | Processamento distribuído (via Spark Connect) |
| Apache Pinot | latest | OLAP em tempo real (sub-segundo) |
| StarRocks | latest | Analytics OLAP |
| Apache Kafka | 7.4.0 (Confluent) | Streaming de eventos |
| Schema Registry | 7.4.0 (Confluent) | Governança de schemas |
| MinIO | latest | Object storage (S3-compatible) |
| Elasticsearch | 8.11.0 | Busca full-text e analytics |
| Logstash | 8.11.0 | Pipeline de ingestão |
| Neo4j | 5.15.0 | Banco de dados de grafos |
| Apache Superset | latest | BI e visualização |
| PostgreSQL | 16 | Metastore do Airflow |
| Redis | 7.2 | Broker do Celery (Airflow) |

---

## Troubleshooting

**Pinot Controller não sobe:**
```bash
docker compose -f docker-compose-airflow.yml logs pinot-zookeeper
docker compose -f docker-compose-airflow.yml logs pinot-controller
```

**Pinot tabela sem dados (No Records found):**
Verifique o log da task `load_pinot`. A ingestão deve retornar `Successfully ingested file into table`. Se não, reexecute a task.

**StarRocks BE não registra (Current alive backend is []):**
O BE demora para registrar no FE. Verifique:
```bash
# Ver se o BE está rodando
docker compose -f docker-compose-airflow.yml logs starrocks-be-0 --tail 10

# Ver se o BE registrou no FE
docker compose -f docker-compose-airflow.yml exec starrocks-fe-0 \
  mysql -h 127.0.0.1 -P 9030 -u root -e "SHOW BACKENDS\G"
```
Se `Alive: false`, aguarde mais ~30s. Se o BE não aparece, reinicie:
```bash
docker compose -f docker-compose-airflow.yml restart starrocks-be-0
```

**Spark Connect não conecta:**
```bash
docker compose -f docker-compose-airflow.yml logs spark-connect | tail -20
```

**Erro de memória no Docker:**
O projeto roda ~20+ containers. Aumente a memória do Docker para pelo menos 12 GB em Docker Desktop → Settings → Resources.

**DAG não aparece no Airflow:**
Aguarde 1-2 minutos para o dag-processor detectar o arquivo. Verifique erros de parse:
```bash
docker compose -f docker-compose-airflow.yml logs airflow-dag-processor | grep -i error
```

**Permissão negada nos logs/dags (Linux):**
```bash
sudo chown -R 50000:0 dags/ logs/ plugins/ config/
```
