import requests
import tempfile
import boto3
from urllib.parse import urlparse
from time import sleep
from .gql_client import RelyComplyGQLClient
from .exceptions import RelyComplyClientException

s3_client = boto3.client("s3")


class RelyComplyIntegrationClient:
    """
    A client that is useful for common integration tasks.

    This exposes higher level methods that compose the lower level GQL calls in common patterns
    """

    def __init__(self, gql_client: RelyComplyGQLClient):
        self.gql = gql_client

    def object_id(self, obj_or_id):
        """
        Useful helpers so we can pass json objects with and "id" field instead of
        just ids
        """
        if isinstance(obj_or_id, dict):
            return obj_or_id["id"]
        else:
            return obj_or_id

    def object_ids(self, objs_or_ids):
        if not objs_or_ids:
            return []
        return [self.object_id(obj) for obj in objs_or_ids]

    def sign_url(self, url):
        """
        If an s3 url is passed this will sign it, else if https just return
        """

        if url.startswith("https://"):
            return url

        if url.startswith("s3://"):
            # pull out the bucket and path
            o = urlparse(url)
            return s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": o.netloc,
                    "Key": o.path.lstrip("/"),
                },
                ExpiresIn=5 * 60,
            )

    def put_to_datafile(self, df, name):
        """
        Takes a dataframe converts it to parquet, creates a new datafile, and puts it at the putUrl
        """
        datafile = self.gql.createDataFile(name=name)

        with tempfile.NamedTemporaryFile() as fp:
            df.to_parquet(
                fp.name,
                allow_truncated_timestamps=True,
                use_deprecated_int96_timestamps=True,
            )
            try:
                requests.put(datafile["putUrl"], data=fp).raise_for_status()
            except Exception as e:
                raise RelyComplyClientException(
                    f"Error uploading to DataFile {datafile['id']}:{str(e)}"
                )

        return datafile

    def pull_to_datafile(self, source_url, name, wait_for_ready=False):
        signed_url = self.sign_url(source_url)
        datafile = self.gql.createDataFile(name=name, sourceUrl=signed_url)

        if wait_for_ready:
            while True:  # Should have timeout
                sleep(5)
                datafile = self.gql.dataFiles(id=self.object_id(datafile), _only=True)
                if datafile["status"] != "LOADING":
                    break
        if datafile["status"] == "ERROR":
            raise RelyComplyClientException(
                f"Error pulling datafile {datafile['id']}: {datafile['error']}"
            )
        return datafile

    def ingest_datasource(
        self, datasource, data_file, format="PARQUET", raw_data_files=None
    ):
        """
        Ingests a datasource
        """
        version = self.gql.ingestDataSource(
            id=self.object_id(datasource),
            dataFile=self.object_id(data_file),
            rawDataFiles=self.object_ids(raw_data_files),
            format=format,
        )
        status = version["status"]
        while status == "UPLOADING":
            sleep(2)
            version = self.gql.dataSourceVersions(id=version["id"], _only=True)
            status = version["status"]

        if status == "ERROR":
            raise RelyComplyClientException(
                f"Error ingesting DataSourceVersion {version['id']}: {version['error']}"
            )

        return version

    def ingest_parquet_lookup_table(
        self,
        lookup_table,
        data_file,
        version_tag=None,
        replace_tag=False,
    ):
        """
        Ingests a lookup table
        """
        version = self.gql.ingestParquetLookupTable(
            id=self.object_id(lookup_table),
            dataFile=self.object_id(data_file),
            versionTag=version_tag,
            replaceTag=replace_tag,
        )
        status = version["status"]
        while status == "UPLOADING":
            sleep(1)
            version = self.gql.lookupTableVersions(id=version["id"], _only=True)
            status = version["status"]

        if status == "ERROR":
            raise RelyComplyClientException(
                f"Error ingesting DataSourceVersion {version['id']}: {version['error']}"
            )

        return version

    def run_monitor(self, monitor_name, sources=None, source_versions=None):
        """
        Runs a monitor
        """
        sources = sources or []
        source_versions = source_versions or []
        return self.gql.runMonitor(
            id=monitor_name,
            sources=self.object_ids(sources),
            versions=self.object_ids(source_versions),
            engine="athena",
        )
