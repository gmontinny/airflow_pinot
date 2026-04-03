"""
DAG: IBGE Aglomerações Urbanas → Spark Connect → Apache Pinot + StarRocks

Demonstra o pipeline completo:
1. Extrai dados da API do IBGE (aglomerações urbanas)
2. Transforma com Spark Connect (flatten JSON aninhado)
3. Cria tabela/schema no Apache Pinot
4. Carrega dados no Pinot via REST API
5. Carrega dados no StarRocks via Spark JDBC
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta

import requests
from airflow.decorators import dag, task

logger = logging.getLogger(__name__)

IBGE_API_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/aglomeracoes-urbanas"
PINOT_CONTROLLER = os.getenv("PINOT_CONTROLLER_URL", "http://pinot-controller:9000")
SPARK_CONNECT_URL = os.getenv("SPARK_CONNECT_URL", "sc://spark-connect:15002")
STARROCKS_FE = os.getenv("STARROCKS_FE_HOST", "starrocks-fe-0")
STARROCKS_JDBC = f"jdbc:mysql://{STARROCKS_FE}:9030/demo_ibge"

PINOT_TABLE = "ibge_aglomeracoes"


@dag(
    dag_id="ibge_pinot_starrocks",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ibge", "pinot", "starrocks", "spark"],
    doc_md=__doc__,
)
def ibge_pinot_starrocks():

    @task()
    def extract_ibge() -> list[dict]:
        resp = requests.get(IBGE_API_URL, timeout=60)
        resp.raise_for_status()
        raw = resp.json()
        logger.info("Extraídos %d aglomerações urbanas do IBGE", len(raw))
        return raw

    @task()
    def transform_spark(raw: list[dict]) -> list[dict]:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F
        from pyspark.sql.types import (
            ArrayType,
            IntegerType,
            StringType,
            StructField,
            StructType,
        )

        spark = SparkSession.builder.remote(SPARK_CONNECT_URL).getOrCreate()

        schema = StructType([
            StructField("id", StringType()),
            StructField("nome", StringType()),
            StructField("municipios", ArrayType(StructType([
                StructField("id", IntegerType()),
                StructField("nome", StringType()),
                StructField("UF", StructType([
                    StructField("id", IntegerType()),
                    StructField("sigla", StringType()),
                    StructField("nome", StringType()),
                    StructField("regiao", StructType([
                        StructField("id", IntegerType()),
                        StructField("sigla", StringType()),
                        StructField("nome", StringType()),
                    ])),
                ])),
            ]))),
        ])

        df = spark.createDataFrame(raw, schema=schema)

        flat = (
            df.select("id", "nome", F.explode("municipios").alias("m"))
            .select(
                F.col("id").alias("aglomeracao_id"),
                F.col("nome").alias("aglomeracao_nome"),
                F.col("m.id").alias("municipio_id"),
                F.col("m.nome").alias("municipio_nome"),
                F.col("m.UF.id").alias("uf_id"),
                F.col("m.UF.sigla").alias("uf_sigla"),
                F.col("m.UF.nome").alias("uf_nome"),
                F.col("m.UF.regiao.id").alias("regiao_id"),
                F.col("m.UF.regiao.sigla").alias("regiao_sigla"),
                F.col("m.UF.regiao.nome").alias("regiao_nome"),
            )
        )

        rows = [row.asDict() for row in flat.collect()]
        logger.info("Spark transformou %d registros (municípios flatten)", len(rows))
        spark.stop()
        return rows

    @task()
    def setup_pinot_table():
        schema_payload = {
            "schemaName": PINOT_TABLE,
            "dimensionFieldSpecs": [
                {"name": "aglomeracao_id", "dataType": "STRING"},
                {"name": "aglomeracao_nome", "dataType": "STRING"},
                {"name": "municipio_id", "dataType": "INT"},
                {"name": "municipio_nome", "dataType": "STRING"},
                {"name": "uf_id", "dataType": "INT"},
                {"name": "uf_sigla", "dataType": "STRING"},
                {"name": "uf_nome", "dataType": "STRING"},
                {"name": "regiao_id", "dataType": "INT"},
                {"name": "regiao_sigla", "dataType": "STRING"},
                {"name": "regiao_nome", "dataType": "STRING"},
            ],
        }

        table_payload = {
            "tableName": PINOT_TABLE,
            "tableType": "OFFLINE",
            "segmentsConfig": {
                "replication": "1",
                "schemaName": PINOT_TABLE,
            },
            "tenants": {"broker": "DefaultTenant", "server": "DefaultTenant"},
            "tableIndexConfig": {"loadMode": "MMAP"},
            "ingestionConfig": {"batchIngestionConfig": {"segmentIngestionType": "APPEND"}},
            "metadata": {},
        }

        # Cria schema (ignora se já existe)
        r = requests.post(
            f"{PINOT_CONTROLLER}/schemas",
            json=schema_payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        logger.info("Pinot schema: %s %s", r.status_code, r.text)

        # Cria tabela (ignora se já existe)
        r = requests.post(
            f"{PINOT_CONTROLLER}/tables",
            json=table_payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        logger.info("Pinot table: %s %s", r.status_code, r.text)

    @task()
    def load_pinot(rows: list[dict]):
        if not rows:
            logger.warning("Nenhum registro para carregar no Pinot")
            return

        ndjson = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)

        batch_config = json.dumps({
            "inputFormat": "json",
            "recordReader.className": "org.apache.pinot.plugin.inputformat.json.JSONRecordReader",
        })

        r = requests.post(
            f"{PINOT_CONTROLLER}/ingestFromFile",
            params={
                "tableNameWithType": f"{PINOT_TABLE}_OFFLINE",
                "batchConfigMapStr": batch_config,
            },
            files={"file": ("data.json", ndjson.encode("utf-8"), "application/json")},
            timeout=120,
        )
        r.raise_for_status()
        logger.info("Pinot ingest: %s %s", r.status_code, r.text[:500])

    @task(retries=10, retry_delay=timedelta(seconds=20))
    def setup_starrocks():
        """Cria database e tabela no StarRocks via protocolo MySQL (pymysql)."""
        import pymysql

        conn = pymysql.connect(host=STARROCKS_FE, port=9030, user="root", password="",
                               cursorclass=pymysql.cursors.DictCursor)
        try:
            with conn.cursor() as cur:
                cur.execute("SHOW BACKENDS")
                backends = cur.fetchall()
                alive = [b for b in backends if str(b.get("Alive", "")).lower() == "true"]
                logger.info("StarRocks backends: %s", [(b.get("IP"), b.get("Alive")) for b in backends])
                if not alive:
                    raise RuntimeError(f"Nenhum BE alive no StarRocks. Backends: {backends}")

                cur.execute("CREATE DATABASE IF NOT EXISTS demo_ibge")
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS demo_ibge.{PINOT_TABLE} (
                        aglomeracao_id VARCHAR(10),
                        aglomeracao_nome VARCHAR(200),
                        municipio_id INT,
                        municipio_nome VARCHAR(200),
                        uf_id INT,
                        uf_sigla VARCHAR(2),
                        uf_nome VARCHAR(100),
                        regiao_id INT,
                        regiao_sigla VARCHAR(5),
                        regiao_nome VARCHAR(100)
                    )
                    DUPLICATE KEY(aglomeracao_id)
                    DISTRIBUTED BY HASH(aglomeracao_id) BUCKETS 1
                    PROPERTIES("replication_num" = "1")
                """)
            conn.commit()
            logger.info("StarRocks: database e tabela criados com sucesso")
        finally:
            conn.close()

    @task()
    def load_starrocks(rows: list[dict]):
        from pyspark.sql import SparkSession

        if not rows:
            logger.warning("Nenhum registro para carregar no StarRocks")
            return

        spark = SparkSession.builder.remote(SPARK_CONNECT_URL).getOrCreate()
        df = spark.createDataFrame(rows)

        (
            df.write
            .format("jdbc")
            .option("driver", "com.mysql.cj.jdbc.Driver")
            .option("url", f"jdbc:mysql://{STARROCKS_FE}:9030/demo_ibge")
            .option("dbtable", PINOT_TABLE)
            .option("user", "root")
            .option("password", "")
            .mode("append")
            .save()
        )

        logger.info("StarRocks: registros carregados com sucesso")
        spark.stop()

    # Orquestração
    raw = extract_ibge()
    rows = transform_spark(raw)
    pinot_setup = setup_pinot_table()

    pinot_setup >> load_pinot(rows)

    sr_setup = setup_starrocks()
    sr_setup >> load_starrocks(rows)


ibge_pinot_starrocks()
