from pydantic import BaseModel
from typing import Optional, Any,Dict,List

class TType(BaseModel):
    numberOfBytes: int
    t_type: str  # type with t prefix
    label: str   # variable type

class MapType(TType):
    key: TType
    value: TType




class Storage(BaseModel):
    slot: int
    offset: int
    type: TType
    label: str  #variable name
    showtype: int
    
    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))



class StructType(TType):
    members: list[Storage]


class DiffInfo(BaseModel):
    key: str
    fromValue: str
    toValue: str

class BaseResult(TType):
    actual_value: Any

class MapResult(MapType):
    actual_key: Any
    actual_value: Any

class StorageResult(Storage):
    actual_value: Any

class StructResult(StructType):
    members: List[StorageResult]

# class StateDiffResultOne(BaseModel):
#     dirty: Optional[str|Dict]
#     original: Optional[str|Dict]
#     soltype: Optional[Dict]

class StateDiffResult(BaseModel):
    dirty: Optional[str|Dict]
    original: Optional[str|Dict]
    raw: List[Dict]
    soltype: Optional[Dict]
    contract: Optional[Dict]
    showtype: int = 0

class DestructItem(BaseModel):
    key: str
    slot: int
