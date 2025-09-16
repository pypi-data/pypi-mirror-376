import logging
import shlex
import tempfile

import httpx
from edos.api.digitalocean.databases.api import DatabaseApi
from edos.api.digitalocean.databases.models.cluster import DatabaseCluster
from edos.api.digitalocean.databases.models.database import Database
from edos.api.digitalocean.databases.models.database_user import DatabaseUser
from edos.exceptions import DatabaseCreationError, DatabaseEngineNotSupported
from edos.settings import conf
import subprocess

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.api = DatabaseApi()
        self.db_users_cache = {}

    def get_clusters(self) -> dict[str, str]:
        """
        :return: {cluster_id, cluster_name}
        """
        clusters = self.api.get_clusters()
        res = {}
        for cluster in clusters:
            res[cluster.id] = cluster.name
        return res

    def get_cluster(self, cluster_id: str) -> DatabaseCluster:
        if cluster_id == "psql":
            return self.api.get_one_cluster(conf.PSQL_CLUSTER_ID)
        if cluster_id == "psql-dev":
            return self.api.get_one_cluster(conf.PSQL_DEV_CLUSTER_ID)
        if cluster_id == "mysql":
            return self.api.get_one_cluster(conf.MYSQL_CLUSTER_ID)
        return self.api.get_one_cluster(cluster_id)

    def get_databases(self, cluster_id: str) -> list[str]:
        """
        :param cluster_id: cluster where is database stored
        :return: list of database names
        """
        databases = self.api.get_databases(cluster_id)
        return [db.name for db in databases]

    def get_database(self, cluster_id: str, database_name: str) -> Database:
        return self.api.get_database(cluster_id, database_name)
    
    def get_connection_string(self, cluster: DatabaseCluster, database: Database, user: DatabaseUser) -> str:
        if cluster.engine == "pg":
            prefix = "postgresql://"
        elif cluster.engine == "mysql":
            prefix = "mysql://"
        else:
            raise DatabaseEngineNotSupported("Bad cluster. Only PG and Mysql clusters are supported")
        
        private_connection = cluster.privateConnection
        return (
            f"{prefix}{user.name}:{user.password}@{private_connection.host}:"
            f"{private_connection.port}/{database.name}"
        )

    def create_database(self, cluster_id: str, project_name: str, from_dump_file: str | None = None, existing_user: str | None = None, upsert: bool = False) -> str:
        """
        this command creates a database and user

        so this command will be doing this:
            - creates a database
            - creates a database user
            - get cluster
            - create db_url from private connection from cluster
                and database user/password

        In case, that create user fail, you must delete database, for consistency

        :param cluster_id: cluster where database will be stored
        :param project_name: name of database and user
        :return: database url for secrets
        """
        is_database_fresh = True
        cluster = self.get_cluster(cluster_id)
        if from_dump_file and cluster.engine != "pg":
            raise DatabaseEngineNotSupported("Restoring from dump file is only supported for PG clusters")
        try:
            database = self.api.create_database(cluster.id, project_name)
        except httpx.HTTPStatusError as e:
            if upsert and e.response.status_code == 422:
                is_database_fresh = False
                database = self.api.get_database(cluster.id, project_name)
                existing_user = project_name  # assume user with the same name exists
            else:
                raise e
        if existing_user:
            user = self.get_database_user(cluster.id, existing_user)
            if not user:
                raise DatabaseCreationError(f"User {existing_user} does not exist in cluster {cluster.id}")
        else:
            try:
                user = self.api.create_database_user(cluster.id, project_name)
            except httpx.HTTPStatusError as e:
                logger.info(f"Database user creation failed: {e}, ignoring and proceeding")
        
        if cluster.engine == "pg":
            # Grant all privileges to the new user on the new database
            grant_db_cmd = f'GRANT ALL ON DATABASE "{database.name}" TO "{user.name}";'
            grant_schema_cmd = f'GRANT ALL ON SCHEMA public TO "{user.name}";'
            self.run_psql_shell(cluster, "defaultdb", "doadmin", input_string=grant_db_cmd)
            self.run_psql_shell(cluster, database.name, "doadmin", input_string=grant_schema_cmd)

            # import dump file if provided, but only if it's a newly created database
            if from_dump_file and is_database_fresh:
                self.run_psql_shell(cluster, database.name, user.name, input_filename=from_dump_file)

        return self.get_connection_string(cluster, database, user)

    def delete_database(self, cluster_id: str, db_name: str, db_user: str | None = None):
        """
        this command deletes a database and user

        :param cluster_id: cluster where is database stored
        :param db_name: name of database
        :param db_user: name of user, optional
        :return: None
        """
        cluster = self.get_cluster(cluster_id)
        try:
            self.api.delete_database(cluster.id, db_name)
            logger.info(f"Database {db_name} deleted successfully from cluster {cluster.id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Database {db_name} does not exist in cluster {cluster.id}, cannot delete")
            else:
                raise e
        if db_user:
            try:
                self.api.delete_database_user(cluster.id, db_user)
                logger.info(f"User {db_user} deleted successfully from cluster {cluster.id}")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning(f"User {db_user} does not exist in cluster {cluster.id}, cannot delete")
                else:
                    raise e

    def get_database_user(self, cluster_id, username) -> DatabaseUser:
        if (cluster_id, username) not in self.db_users_cache:
            self.db_users_cache[(cluster_id, username)] = self.api.get_database_user(cluster_id, username)
        return self.db_users_cache[(cluster_id, username)]

    def run_psql_shell(self, cluster: DatabaseCluster, database_name: str, username: str, input_filename: str | None = None, input_string: str | None = None):
        if input_filename and input_string:
            raise ValueError("You can use only one of input_filename or input_string")
        user = self.get_database_user(cluster.id, username)
        private_connection = cluster.privateConnection
        psql_cmd = (
            f'psql --host={private_connection.host} '
            f'--port={private_connection.port} --username={user.name} --dbname={database_name}'
        )
        ssh_cmd = [
            "ssh", conf.SSH_CONNECTION,
            f"PGPASSWORD='{user.password}' {psql_cmd}"
        ]

        logger.info(f"Running psql with flags: {psql_cmd}")

        if input_filename:
            # Use shell to handle input redirection
            ssh_cmd_shell = (
                f"ssh {conf.SSH_CONNECTION} PGPASSWORD='{user.password}' {psql_cmd} < \"{input_filename}\""
            )
            subprocess.run(ssh_cmd_shell, shell=True)
        elif input_string:
            # Pipe the input_string to psql via tempfile
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(input_string.encode())
                temp_file.close()
                ssh_cmd_shell = (
                    f"ssh {conf.SSH_CONNECTION} PGPASSWORD='{user.password}' {psql_cmd} < \"{temp_file.name}\""
                )
                subprocess.run(ssh_cmd_shell, shell=True)
        else:
            subprocess.run(ssh_cmd, shell=False)

    # def recreate_database(self, cluster_id: str, db_name: str):
    #     """
    #     this command just deletes database and create it again
    #     (when it needs to be deleted like uploading a dump)
    #     :param cluster_id: cluster where is database stored
    #     :param db_name: name of database
    #     :return: None - because db_url is the same
    #     """
    #     self.api.delete_database(cluster_id, db_name)
    #     self.api.create_database(cluster_id, db_name)
