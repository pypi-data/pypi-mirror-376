from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

from LOGS.Entities.BridgeType import BridgeType
from LOGS.Entities.IRelatedEntityRequest import IRelatedEntityRequest
from LOGS.Entities.RunState import RunState
from LOGS.Entity.EntityRequestParameter import EntityRequestParameter
from LOGS.Interfaces.INamedEntity import INamedEntityRequest
from LOGS.Interfaces.IPermissionedEntity import IPermissionedEntityRequest


class DataSourceHistoryOrder(Enum):
    ID_ASC = "ID_ASC"
    ID_DESC = "ID_DESC"
    STARTED_ON_ASC = "STARTED_ON_ASC"
    STARTED_ON_DESC = "STARTED_ON_DESC"


@dataclass
class DataSourceStatusHistoryRequestParameter(
    EntityRequestParameter[DataSourceHistoryOrder],
    INamedEntityRequest,
    IRelatedEntityRequest,
    IPermissionedEntityRequest,
):
    dataSourceIds: Optional[List[int]] = None
    types: Optional[List[BridgeType]] = None
    runStates: Optional[List[RunState]] = None
    durationInSecondsMin: Optional[float] = None
    durationInSecondsMax: Optional[float] = None
    startedOnFrom: Optional[datetime] = None
    startedOnTo: Optional[datetime] = None
