from LOGS.Auxiliary.Decorators import Endpoint
from LOGS.Entities.DataSourceStatusHistory import DataSourceStatusHistory
from LOGS.Entities.DataSourceStatusHistoryRequestParameter import (
    DataSourceStatusHistoryRequestParameter,
)
from LOGS.Entity.EntityIterator import EntityIterator


@Endpoint("data_sources_status")
class DataSourceStatusHistoryIterator(
    EntityIterator[DataSourceStatusHistory, DataSourceStatusHistoryRequestParameter]
):
    """LOGS connected class DataSource iterator"""

    _generatorType = DataSourceStatusHistory
    _parameterType = DataSourceStatusHistoryRequestParameter
