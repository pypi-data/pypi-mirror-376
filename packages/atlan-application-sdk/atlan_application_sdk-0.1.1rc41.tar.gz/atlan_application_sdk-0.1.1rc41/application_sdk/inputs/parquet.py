import glob
import os
from typing import TYPE_CHECKING, AsyncIterator, Iterator, List, Optional, Union

from application_sdk.activities.common.utils import get_object_store_prefix
from application_sdk.inputs import Input
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.services.objectstore import ObjectStore

logger = get_logger(__name__)

if TYPE_CHECKING:
    import daft  # type: ignore
    import pandas as pd


class ParquetInput(Input):
    """
    Parquet Input class to read data from Parquet files using daft and pandas.
    Supports reading both single files and directories containing multiple parquet files.
    """

    def __init__(
        self,
        path: Optional[str] = None,
        chunk_size: Optional[int] = 100000,
        input_prefix: Optional[str] = None,
        file_names: Optional[List[str]] = None,
    ):
        """Initialize the Parquet input class.

        Args:
            path (str): Path to parquet file or directory containing parquet files.
            chunk_size (Optional[int], optional): Number of rows per batch.
                Defaults to 100000.
            input_prefix (Optional[str], optional): Prefix for files when reading from object store.
                If provided, files will be read from object store. Defaults to None.
            file_names (Optional[List[str]], optional): List of file names to read.
                Defaults to None.
        """
        self.path = path
        self.chunk_size = chunk_size
        self.input_prefix = input_prefix
        self.file_names = file_names

    async def download_files(self, local_path: str) -> Optional[str]:
        """Read a file from the object store.

        Args:
            local_path (str): Path to the local data in the temp directory.

        Returns:
            Optional[str]: Path to the downloaded local file.
        """
        # if the path is a directory, then check if the directory has any parquet files
        parquet_files = []
        if os.path.isdir(local_path):
            parquet_files = glob.glob(os.path.join(local_path, "*.parquet"))
        else:
            parquet_files = glob.glob(local_path)
        if not parquet_files:
            if self.input_prefix:
                logger.info(
                    f"Reading file from object store: {local_path} from {self.input_prefix}"
                )
                if os.path.isdir(local_path):
                    await ObjectStore.download_prefix(
                        source=get_object_store_prefix(local_path),
                        destination=local_path,
                    )
                else:
                    await ObjectStore.download_file(
                        source=get_object_store_prefix(local_path),
                        destination=local_path,
                    )
            else:
                raise ValueError(
                    f"No parquet files found in {local_path} and no input prefix provided"
                )

    async def get_dataframe(self) -> "pd.DataFrame":
        """
        Method to read the data from the parquet file(s)
        and return as a single combined pandas dataframe.

        Returns:
            "pd.DataFrame": Combined dataframe from all parquet files.
        """
        try:
            import pandas as pd

            path = self.path
            if self.input_prefix and self.path:
                path = await self.download_files(self.path)
            # Use pandas native read_parquet which can handle both single files and directories
            return pd.read_parquet(path)
        except Exception as e:
            logger.error(f"Error reading data from parquet file(s): {str(e)}")
            # Re-raise to match IcebergInput behavior
            raise

    async def get_batched_dataframe(
        self,
    ) -> Union[AsyncIterator["pd.DataFrame"], Iterator["pd.DataFrame"]]:
        """
        Method to read the data from the parquet file(s) in batches
        and return as an async iterator of pandas dataframes.

        Returns:
            AsyncIterator["pd.DataFrame"]: Async iterator of pandas dataframes.
        """
        try:
            import pandas as pd

            path = self.path
            if self.input_prefix and self.path:
                path = await self.download_files(self.path)
            df = pd.read_parquet(path)
            if self.chunk_size:
                for i in range(0, len(df), self.chunk_size):
                    yield df.iloc[i : i + self.chunk_size]
            else:
                yield df
        except Exception as e:
            logger.error(
                f"Error reading data from parquet file(s) in batches: {str(e)}"
            )
            raise

    async def get_daft_dataframe(self) -> "daft.DataFrame":  # noqa: F821
        """
        Method to read the data from the parquet file(s)
        and return as a single combined daft dataframe.

        Returns:
            daft.DataFrame: Combined daft dataframe from all parquet files.
        """
        try:
            import daft  # type: ignore

            if self.file_names:
                path = f"{self.path}/{self.file_names[0].split('/')[0]}"
            else:
                path = self.path
            if self.input_prefix and path:
                await self.download_files(path)
            return daft.read_parquet(f"{path}/*.parquet")
        except Exception as e:
            logger.error(
                f"Error reading data from parquet file(s) using daft: {str(e)}"
            )
            # Re-raise to match IcebergInput behavior
            raise

    async def get_batched_daft_dataframe(self) -> AsyncIterator["daft.DataFrame"]:  # type: ignore
        """
        Get batched daft dataframe from parquet file(s)

        Returns:
            AsyncIterator[daft.DataFrame]: An async iterator of daft DataFrames, each containing
            a batch of data from the parquet file(s).
        """
        try:
            import daft  # type: ignore

            if self.file_names:
                for file_name in self.file_names:
                    path = f"{self.path}/{file_name}"
                    if self.input_prefix and path:
                        await self.download_files(path)
                        yield daft.read_parquet(path)
            else:
                if self.path and self.input_prefix:
                    await self.download_files(self.path)
                    yield daft.read_parquet(f"{self.path}/*.parquet")

        except Exception as error:
            logger.error(
                f"Error reading data from parquet file(s) in batches using daft: {error}"
            )
            raise
