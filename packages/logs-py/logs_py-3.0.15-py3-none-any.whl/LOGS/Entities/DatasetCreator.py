from typing import TYPE_CHECKING, List, Optional

from LOGS.Auxiliary.Decorators import Endpoint
from LOGS.Auxiliary.Exceptions import EntityCreatingException, LOGSException
from LOGS.Auxiliary.Tools import Tools
from LOGS.Entities.Dataset import Dataset
from LOGS.Entities.FileEntry import FileEntry
from LOGS.Entity.EntityConnector import EntityConnector
from LOGS.LOGSConnection import LOGSConnection, MultipartEntry

if TYPE_CHECKING:
    pass


class DatasetUploadRequest(Dataset):
    _typeMapper = {"files": FileEntry}

    def __init__(self, ref=None):
        super().__init__(ref)
        if ref and isinstance(ref, Dataset):
            self._files = ref._files

    _files: Optional[List[FileEntry]]
    _filePathsAreAbsolute: Optional[bool] = True

    @property
    def files(self) -> Optional[List[FileEntry]]:
        return self._files

    @files.setter
    def files(self, value):
        self._files = self.checkListAndConvertNullable(value, FileEntry, "files")

    @property
    def filePathsAreAbsolute(self) -> Optional[bool]:
        return self._filePathsAreAbsolute

    @filePathsAreAbsolute.setter
    def filePathsAreAbsolute(self, value):
        self._filePathsAreAbsolute = self.checkAndConvertNullable(
            value, bool, "filePathsAreAbsolute"
        )


@Endpoint("datasets")
class DatasetCreator(EntityConnector):
    _request: DatasetUploadRequest = DatasetUploadRequest()
    _formatId: str
    _files: List[FileEntry]

    def __init__(self, connection: LOGSConnection, dataset: Dataset):
        self._connection = connection

        if not dataset:
            raise LOGSException("Cannot not create empty dataset")
        if not dataset._files:
            raise LOGSException("Cannot not create dataset without files")
        if not dataset.format or not dataset.format.id:
            raise LOGSException("Cannot not create dataset without a format field")

        self._formatId = dataset.format.id
        self._files = dataset._files
        self._request = self._getDatasetUploadRequest(dataset=dataset)

    def create(self):
        connection, endpoint = self._getConnectionData()

        multipart = [
            MultipartEntry(
                name="Dataset", fileName=None, content=self._request.toDict()
            )
        ]
        multipart.extend(
            [
                MultipartEntry(name="files", fileName=file.id, content=file)
                for file in self._files
            ]
        )

        data, responseError = connection.postMultipartEndpoint(
            endpoint=endpoint + ["create"], data=multipart
        )
        if responseError:
            raise EntityCreatingException(responseError=responseError)

        return Tools.checkAndConvert(data, dict, "dataset creation result")

    def _getDatasetUploadRequest(self, dataset: Dataset):
        # print("\n".join([f.fullPath for f in fileList]))
        if not self._files:
            raise LOGSException("Cannot not create dataset without files")
        if not self._formatId:
            raise LOGSException("Cannot not create dataset without a formatId")

        for file in self._files:
            file.addMtime()

        request = DatasetUploadRequest(dataset)

        return request
