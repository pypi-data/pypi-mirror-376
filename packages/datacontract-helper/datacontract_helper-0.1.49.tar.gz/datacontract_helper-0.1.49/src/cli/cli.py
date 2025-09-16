import logging
import sys
from pathlib import Path

import click

from helpers import ModuleBuilder, WheelBuilder


# Добавляем текущую директорию в путь импорта
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(object=current_dir))

# https://datacontract.com/examples/orders-latest/datacontract.yaml
# название schema из schema-registry брать из контракта .yml, не передавать ее как атрибут
# добавлять в .yml название сервиса овнера

# попросить у девопсов создать тестовый топик на девовской аналитической кафке:
# done



# name of schema из schema registry должно браться из датаконтракта и храниться в пакете в nexus
# done
# name of topic должно браться из датаконтракта и храниться в пакете в nexus
# done



log: logging.Logger = logging.getLogger(name=__name__)
log.setLevel(level=logging.DEBUG)


# топики
# http://localhost:8082/topics
# http://localhost:8082/topics/et_admin_datacontract



# # Получить список всех subjects
# curl -X GET http://localhost:8081/subjects
# nshokurov@MB-YLV2KQ4C ~
# % curl -X GET http://localhost:8081/subjects                                                    [2025-09-03 15:56:37]
# ["persons-topic-value","your_topic-value"]%

# # Получить все версии схемы для subject
# curl -X GET http://localhost:8081/subjects/et_admin_datacontract/versions

# # Получить конкретную версию схемы
# curl -X GET http://localhost:8081/subjects/vertica_datacontract/versions/1
# echo $(curl -X GET http://localhost:8081/subjects/vertica_datacontract/versions/1)


@click.group()
@click.pass_context
def cli(
    ctx,
):
    ctx.ensure_object(dict)
    print("is cli")


@cli.command()
@click.option("--filename")
@click.option("--subject-name")
def publish_schema_registry(
    filename: str,
    subject_name: str,
):
    """
    uv run --env-file .env python -m src publish-schema-registry --filename "vertica_datacontract" --subject-name vertica_datacontract

    uv run datacontract-helper publish-schema-registry --filename et_admin_datacontract --subject-name et_admin_datacontract
    et_admin_datacontract
    """
    ModuleBuilder().publish_schema_registry(
        filename=filename, subject_name=subject_name
    )


@cli.command()
@click.option("--filename", default="vertica_datacontract")
@click.option(
    "--subject-name",
    default="vertica_datacontract",
)
@click.option("--version", default="latest")
@click.option("--compatibility-type", default="FULL")
def validate_schema_registry(
    filename: str = "vertica_datacontract",
    subject_name: str = "vertica_datacontract",
    version: str = "latest",
    compatibility_type: str = "FULL",
):
    """

    uv run --env-file .env python -m src validate-schema-registry --filename "vertica_datacontract" --subject-name vertica_datacontract --compatibility-type FULL
    
    uv run datacontract-helper validate-schema-registry --filename "et_admin_datacontract" --subject-name et_admin_datacontract --compatibility-type FULL
    """
    ModuleBuilder().validate_custom(filename=filename)

    ModuleBuilder().validate_schema_registry(
        subject_name=subject_name,
        version=version,
        filename=filename,
        compatibility_type=compatibility_type,
    )        


@cli.command()
@click.option("--filename", required=False, type=str, help="Название файла")
def validate_custom(filename: str):
    """
    uv run --env-file .env python -m src validate-custom --filename vertica_datacontract

    uv run datacontract-helper validate-custom --filename vertica_datacontract

    """

    ModuleBuilder().validate_custom(filename=filename)


@cli.command()
@click.option("--filename", required=True, type=str, help="Название файла")
def create_yaml_from_sql(filename: str):
    """
    нужен ddl.sql

    uv run --env-file .env python -m src create-yaml-from-sql --filename vertica_datacontract

    uv run datacontract-helper create-yaml-from-sql --filename vertica_datacontract
    """
    ModuleBuilder().create_yaml_from_sql(filename=filename)


# не уверен, что эта команда нужна
@cli.command()
@click.option("--filename", required=True, type=str, help="Название файла")
def create_proto_from_yaml(filename: str):
    """
    нужен your-datacontract.yaml

    uv run --env-file .env python -m src create-proto-from-yaml --filename vertica_datacontract

    uv run datacontract-helper create-proto-from-yaml --filename et_admin_datacontract

    """
    ModuleBuilder().create_proto_from_yaml(filename=filename)


@cli.command()
@click.option("--filename", required=True, type=str, help="Название файла")
def generate_python_code_from_proto(filename: str):
    """
    uv run --env-file .env python -m src generate-python-code-from-proto --filename vertica_datacontract

    uv run datacontract-helper generate-python-code-from-proto --filename et_admin_datacontract

    """
    ModuleBuilder().generate_python_code_from_proto(filename=filename)


@cli.command()
@click.option("--wheel-version", required=True)
@click.option("--proto-file-name", default="vertica_datacontract_pb2")
@click.option("--filename", default="vertica_datacontract")
def create_wheel(
    wheel_version: str,
    proto_file_name: str = "vertica_datacontract_pb2",
    filename: str = "vertica_datacontract",
):
    """
    uv run --env-file .env python -m src create-wheel --proto-file-name vertica_datacontract_pb2 --wheel-version 0.1.9 --filename vertica_datacontract

    uv run datacontract-helper create-wheel --proto-file-name et_admin_datacontract_pb2 --wheel-version 0.1.5 --filename et_admin_datacontract

    """

    WheelBuilder().build_wheel(
        proto_file_name=proto_file_name,
        filename=filename,
        version=wheel_version,
    )


@cli.command()
@click.option("--filepath", required=True, type=str)
@click.option("--nexusurl", required=True, type=str)
@click.option("--username", required=True, type=str)
@click.option("--password", required=True, type=str)
def publish_package(
    filepath: str, nexusurl: str, username: str, password: str
):
    """

    uv run python -m src publish-package --filepath "vertica_datacontract-0.1.9-py3-none-any.whl" --nexusurl "https://nexus.k8s-analytics.ostrovok.in/repository/datacontract_pypi/" --username n.shokurov --password test_pass

    uv run datacontract-helper create-wheel --proto-file-name et_admin_datacontract_pb2 --wheel-version 0.1.4 --filename et_admin_datacontract


    """
    ModuleBuilder().publish_package(
        nexus_pass=password,
        nexus_repo=nexusurl,
        nexus_user=username,
        wheel_file=filepath
    )
