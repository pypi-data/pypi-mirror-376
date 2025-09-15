import json
import logging
import math
import os
from json import JSONDecodeError

import click
from tabulate import tabulate
import yaml

from edos.cache import cache
from edos.cli.common import create_completion_from_names, get_new_secret_name
from edos.exceptions import SecretDoesNotExists
from edos.services.docker_service import DockerService
from edos.services.swarmpit_service import SwarmpitService
from edos.settings import conf

LOG = logging.getLogger(__name__)


@click.group()
def docker():
    """Managing our docker swarm cluster"""


def service_completion(ctx, args, incomplete):
    @cache.memoize(expire=10)
    def get_names():
        return [s.name for s in DockerService().get_services()]

    return create_completion_from_names(get_names(), incomplete)


def secrets_completion(ctx, args, incomplete):
    @cache.memoize(expire=10)
    def get_names():
        return [s.name for s in DockerService().get_secrets()]

    return create_completion_from_names(get_names(), incomplete)


@docker.command()
@click.argument("service_name", shell_complete=service_completion)
@click.option(
    "--command",
    help="Specify which command will be used [bash, sh etc.]",
    type=str,
)
def exec(service_name, command):
    """\"docker exec\" into a service container"""
    if not command:
        command = "bash"
    d_service = DockerService()
    click.secho("Retrieving hostname...", fg="blue")
    host_name = d_service.get_node_name_for_service(service_name)
    click.secho("Retrieving container...", fg="blue")
    container_name = d_service.get_container(host_name, service_name)
    click.secho("Connecting to server...", fg="blue")
    os.system(f"docker --host ssh://{host_name} exec -it {container_name} {command}")

@docker.command()
@click.argument("service_name", shell_complete=service_completion)
@click.option("--format", type=click.Choice(["json", "yaml"]), default="json")
def inspect(service_name, format):
    """Inspect a service"""
    d_service = DockerService()
    service = d_service.get_service_by_service_name(service_name)
    if format == "json":
        click.echo(json.dumps(service.attrs, indent=2))
    else:
        click.echo(yaml.dump(service.attrs))

@docker.group()
def secrets():
    """Managing docker secrets"""


@secrets.command()
def ls():
    """List secrets"""
    items = DockerService().get_secrets()
    for secret in items:
        click.echo(secret.name)


@secrets.command()
@click.option("--name", type=str, help="Name of the secret", required=False)
@click.option("--from-file", type=click.Path(exists=True), help="File to read secret from", required=False)
@click.option("--no-confirm", is_flag=True, help="Do not ask for confirmation")
def create(name, from_file, no_confirm = False):
    """Create a secret interactively"""
    if not name:
        name = click.prompt("Name")
    if not no_confirm:
        click.confirm(
            "An editor will be opened to input the secret's value. " "Exit without saving to abort.",
            default=True,
            show_default=False,
            prompt_suffix="",
        )
    if from_file:
        with open(from_file, "rb") as f:
            value = f.read()
    else:
        value = click.edit()
    if name and value:
        result = DockerService().create_secret(name, value)
        click.echo(click.style("Created secret with ID: ", fg="green") + result.id)
    else:
        click.secho(f"Creation of secret '{name}' cancelled", fg="red")


@secrets.command()
@click.argument("secret_name", type=str, shell_complete=secrets_completion)
@click.option("--no-pager", is_flag=True, help="Do not use pager")
def ps(secret_name: str, no_pager: bool = False):
    """Read one secret"""
    d_service = DockerService()
    click.secho("Getting secret", fg="blue")
    d_secret = d_service.get_secret_by_name(secret_name)
    click.secho("Creating container with mounted secret", fg="blue")
    _service = d_service.create_service_with_secret(d_secret)
    try:
        container_name = d_service.get_container_name_by_service(_service)

        command = f"docker --host {conf.DOCKER_SSH_BASE_URL} exec -t {container_name} " f"cat /run/secrets/{d_secret.name}"

        old_secret = os.popen(command).read()
        if no_pager:
            click.echo("=" * 34)
            click.echo(old_secret)
            click.echo("=" * 34)
        else:
            click.echo_via_pager(old_secret)
    finally:
        _service.remove()


@secrets.command()
@click.argument("secret_name", type=str, shell_complete=secrets_completion)
def rm(secret_name: str):
    """Remove a secret"""
    DockerService().remove_secret(secret_name)
    click.secho("Secret has been removed", fg="green")


@secrets.command()
@click.argument("secret_name", type=str, shell_complete=secrets_completion)
def edit(secret_name: str):
    """
    1. check if secret exists
    2. create container and mount secret to it
    3. open and edit secret
    4. create new secret and return secret name
    :param secret_name:
    :return:
    """
    d_service = DockerService()
    click.secho("Getting secret", fg="blue")
    d_secret = d_service.get_secret_by_name(secret_name)
    click.secho("Creating container with mounted secret", fg="blue")
    _service = d_service.create_service_with_secret(d_secret)
    try:
        container_name = d_service.get_container_name_by_service(_service)

        command = f"docker --host {conf.DOCKER_SSH_BASE_URL} exec -t {container_name} " f"cat /run/secrets/{d_secret.name}"
        click.secho("Getting secret content", fg="blue")
        old_secret = os.popen(command).read()

        while True:
            new_data = click.edit(old_secret, extension=".json")
            if new_data and old_secret.strip() != new_data.strip():
                break
            if not click.confirm("No change detected, do you want to edit again?"):
                return click.secho("Creation cancelled", fg="red")
            continue

        try:
            json.loads(new_data)
        except JSONDecodeError:
            if not click.confirm("Not valid JSON, do you want to continue?"):
                return click.secho("Creation cancelled", fg="red")

        new_name = get_new_secret_name(secret_name)

        while True:
            name = click.prompt(
                "New secret name: (keep empty if you want to use default)",
                default=new_name,
            )
            try:
                d_service.get_secret_by_name(name)
                click.secho("Secret already exists, choose another name", fg="yellow")
            except SecretDoesNotExists:
                break

        result = DockerService().create_secret(name, bytes(new_data.encode("utf-8")))
        click.echo(click.style("Created secret with name: ", fg="green") + result.name)
    finally:
        _service.remove()


@docker.group()
def service():
    """Managing swarm services"""


@service.command()
# flake8: noqa
def ls():  # flake8: noqa
    """List running services"""
    for item in DockerService().get_services():
        click.echo(item.name)


@service.command()
def reservation():
    """List of services without reservation"""
    services = DockerService().get_services_without_reservation()
    if not services:
        click.echo("Good job. All services has reservation limit")
    click.echo("These services have no resource limits:")
    for s in services:
        click.secho(s.name, fg="red")


def get_mem_res_text(res_memory, avg_memory, diff):
    if not res_memory:
        return click.style("No limit", fg="red")

    if res_memory < avg_memory:
        return click.style(res_memory, fg="red")

    if res_memory - diff < avg_memory:
        return click.style(res_memory, fg="yellow")

    return click.style(res_memory, fg="green")


sort_cols = ["name", "memory"]
sort_mapper = {val: i for i, val in enumerate(sort_cols)}


@service.command()
@click.option(
    "--diff",
    help="Specify how many extra MiB services can have (else warning)",
    type=int,
)
@click.option(
    "--sort",
    help="Specify sorting",
    type=click.Choice(sort_cols),
    default=sort_cols[1],
)
def memstats(diff, sort):
    """List of memory stats for all services"""
    memory_stats = SwarmpitService().get_service_memory_stats()
    if not diff:
        diff = 20

    text_to_tabulate = []
    for s in memory_stats:
        res_text = get_mem_res_text(s.memory_reservation, s.actual_memory_usage, diff)
        text_to_tabulate.append([s.service_name, s.actual_memory_usage, res_text])

    text_to_tabulate = sorted(text_to_tabulate, key=lambda x: x[sort_mapper[sort]], reverse=True)

    click.echo(tabulate(text_to_tabulate, headers=["Service", "Usage", "Reservation"]))


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


@service.command()
def reservationsum():
    sum_res = DockerService().get_sum_of_reservation()
    click.echo(f"Sum of reservation: {convert_size(sum_res)}")
