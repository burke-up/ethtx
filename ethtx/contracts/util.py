from .models.contract_model import *

def get_num_by_offset_and_len(num: int, offset: int, numberOfBytes: int):
    return hex((num >> (offset*8)) & ((1<<(numberOfBytes*8))-1))

def recursiveGenStateDiffResult(itemtype:TType, diffList: List[DestructItem], pos: int, offset: int, dirty_input:str, original_input:str):  
    print("pos=",pos)
    print("diffList:=", diffList)      

    if isinstance(itemtype,MapType):
        diff = diffList[pos]
        key = diff.key
        # transfer diff.slot , if next is struct, then the slot will be used
        dirty_value,original_value = recursiveGenStateDiffResult(itemtype.value,diffList, pos+1,diff.slot,dirty_input,original_input)
        dirty = {key: dirty_value }
        original = {key: original_value }
        return tuple([dirty, original])

    if isinstance(itemtype, StructType):
        print("itemtypestruct:", itemtype)
        slot = offset
        dirty = {}
        original = {}
        for member in itemtype.members:

            print("heresolot:",slot, member.slot)
            if member.slot == slot:
                struct_offset = member.offset
                dirty_value,original_value = recursiveGenStateDiffResult(member.type,diffList,pos+1,struct_offset,dirty_input,original_input)
                dirty[member.label] = dirty_value
                original[member.label] =  original_value
                print("here:", dirty)
        return tuple([dirty, original])

    dirty_num = get_num_by_offset_and_len(int(dirty_input,16), offset, itemtype.numberOfBytes)
    original_num = get_num_by_offset_and_len(int(original_input,16), offset, itemtype.numberOfBytes)
    return tuple([dirty_num, original_num])

def genStateDiffResult(raw: List, diffInfo:Dict[str,str], diffList:List[DestructItem],storageDict: Dict[int,Dict[int,Storage]])->Dict[str,StateDiffResult]:
    slot = diffList[0].slot
    items: Dict[int,Storage] = storageDict[slot]

    retdata = {}
    for offset, item in items.items():
        soltype = {"name":item.label, "type": item.type.label}
        print("diff:", diffList)


        dirty,original = recursiveGenStateDiffResult(item.type, diffList,1, offset, diffInfo.dirty, diffInfo.original)
        # print("soltype:",soltype)
        # print("dirty=", dirty)
        # print("original=", original)
        # needHandle = True
        # if type(dirty) == str:
        #     if original == dirty:
        #         needHandle = False

        # if not needHandle:
        #     continue
        stateDiffResultOne = StateDiffResult(dirty=dirty, original=original, soltype=soltype, raw=raw)
        if dirty == original:
            continue
        retdata["%s_%s"%(slot, offset)] = stateDiffResultOne
    return retdata 

def handleKey(key):
    return "0x"+key[2:].zfill(64)
