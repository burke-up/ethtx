from crytic_compile.crytic_compile import compile_all, get_platforms
from crytic_compile.cryticparser import DEFAULTS_FLAG_IN_CONFIG, cryticparser
from crytic_compile.platform import InvalidCompilation
from crytic_compile.utils.zip import ZIP_TYPES_ACCEPTED, save_to_zip
# from ethtx.models.decoded_model import DecodedTransaction,DecodedCall
import argparse
import json
import os
from .models.contract_model import *
from .util import *

class  Contract():
    globalAddressToStorage = {}
    def __init__(self, addr,etherscan_api_key="FC8R2Q3NYMBJSF9BE6C5RN64EA5GXZPEWA"):
        self.addr = addr
        self.etherscan_api_key = etherscan_api_key
        Contract.globalAddressToStorage = {} 
    def compile(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--etherscan_api_key')
        parser.add_argument('--export-format')
        parser.add_argument('--export-dir')
        parser.add_argument('target')

        argslist = ["--etherscan_api_key",self.etherscan_api_key]
        argslist += ["--export-format","solc"]
        argslist += ["--export-dir","bytecodes/%s"%(self.addr)]
        argslist += [self.addr]
        args = parser.parse_args(args=argslist)

        try:
            # Compile all specified (possibly glob patterned) targets.
            compilations = compile_all(**vars(args))

            # Perform relevant tasks for each compilation
            # print(compilations[0].compilation_units)
            for compilation in compilations:
                if args.export_format:
                    compilation.export(**vars(args))
            return True
        except Exception as e:
            print("compile fail addr=%s,e=%s"%(self.addr,e))
        return False

    def load_storage(self):
        #"bytecodes\\0x0c90c8b4aa8549656851964d5fb787f0e4f54082\\etherscan-contracts\\0x0c90c8b4aa8549656851964d5fb787f0e4f54082-DirectLoanCoordinator\\contracts\\loans\\direct\\DirectLoanCoordinator.sol:DirectLoanCoordinator":
        filename = "bytecodes/%s/combined_solc.json"%(self.addr)
        if not os.path.isfile(filename):
            self.compile()
            if not os.path.isfile(filename):
                print("compile fail addr=%s"%(self.addr))
                return {}
        fp = open(filename,"r")
        data = fp.read()
        fp.close()
        solcinfo = json.loads(data)
        maxlen = 0
        storage_layout = None
        maxkey = None
        for k,v in solcinfo["contracts"].items():
            alls = k.split("/")
            if len(alls) < 4:
                continue
            info = alls[3].split("-")
            if len(info) < 2:
                continue
            addr, name = info[0:2]
            if k.endswith(":%s"%(name)):
                if "storage_layout" not in v:
                    return 
                print("foundKey=%s"%(k))
                storage_layout = v["storage_layout"]
                break
        storageDict: Dict[int,Dict[int,Storage]]= {}
        if storage_layout and "storage" in storage_layout:
            for item in storage_layout["storage"]:
                label = item["label"]
                offset = int(item["offset"])
                slot = int(item["slot"])
                item_type = item["type"]
                storage_type = self.findType(storage_layout, item_type)
                if slot not in storageDict:
                    storageDict[slot] = {}
                showtype = 0
                if  isinstance(storage_type,TType):
                    showtype = 1
                if isinstance(storage_type, MapType):
                    if isinstance(storage_type.value, TType):
                        showtype = 2
                    if  isinstance(storage_type.value, MapType):
                        showtype = 3
                    if isinstance(storage_type.value, StructType):
                        showtype = 4
                if  isinstance(storage_type, StructType):
                    showtype = 5
                    
                storageDict[slot][offset] = Storage(slot=slot, offset=offset, type=storage_type, label=label, showtype=showtype)   
        return storageDict


    def findType(self, storage_layout, item_type: str)->TType:
        oneType = storage_layout["types"][item_type]
        label: str = oneType["label"]
        numberOfBytes: int = int(oneType["numberOfBytes"])
        baseType = TType(numberOfBytes=numberOfBytes,t_type=item_type, label=label)
        if "value" in oneType:
            keyType = self.findType(storage_layout, oneType["key"])
            valueType = self.findType(storage_layout, oneType["value"])
            return MapType(key=keyType, value=valueType,numberOfBytes=numberOfBytes,t_type=item_type, label=label)
        if "members" in oneType:
            members: list[Storage] = []
            for member in oneType["members"]:
                storage_type = self.findType(storage_layout, member["type"])
                storage: Storage  = Storage(slot=int(member["slot"]), offset=member["offset"], type=storage_type, label=member["label"],showtype=0)
                members.append(storage)
            return StructType(members=members,numberOfBytes=numberOfBytes,t_type=item_type, label=label)
        return baseType
            
    
    def getStorageDictByAddress(self):
        if self.addr in  Contract.globalAddressToStorage:
            return Contract.globalAddressToStorage[self.addr]
        storageDict: Dict[int,Dict[int,Storage]] = self.load_storage()
        Contract.globalAddressToStorage[self.addr] = storageDict
        return storageDict


    def  decodeDiff(self, key: str, shakey2value:Dict, storageDict: Dict[int,Dict[int,Storage]])->List[DestructItem]:
        key_int = int(key,16)
        if key_int in storageDict:
            item: DestructItem = DestructItem(key="",slot=key_int)
            return [item]
        key = handleKey(key)
        if key in shakey2value:
            value = shakey2value[key]
            prefixlist = self.decodeDiff("0x"+value[len(value)-64:], shakey2value, storageDict)
            return prefixlist + [DestructItem(key=value[0:len(value)-64], slot=0)]

        for pos in range(1,20):
            newKey = hex(key_int -pos)
            if newKey in shakey2value:
                value = shakey2value[newKey]
                prefixlist = self.decodeDiff("0x"+value[len(value)-64:], shakey2value, storageDict)
                return prefixlist + [DestructItem(key=value[0:len(value)-64], slot=pos)]
        return [None]





    def decodeStorageDiff(self, storage, shakey2value):
        total_result = []
        storageDict = self.getStorageDictByAddress()
        slot_offset_to_result = {}
        for slot in storage:
            v = storage[slot]
            if "*" not in v:
                continue
            diffInfo  = storage[slot]["*"]
            raw = [{"address": self.addr,"key":slot, "original":diffInfo.original,"dirty":diffInfo.dirty}]
            if len(storageDict) == 0:
                print("storageDict is null")
                total_result.append(StateDiffResult(raw=raw))
                continue
            diffList = self.decodeDiff(slot, shakey2value, storageDict)
            if len(diffList) == 0 or diffList[0] is None:
                total_result.append(StateDiffResult(raw=raw))
                print("diffList is null")
                continue
            
            stateDiffResultOnes:Dict[str,StateDiffResult] = genStateDiffResult(raw, diffInfo, diffList,storageDict)
            for key, value in stateDiffResultOnes.items():
                
                if key not in slot_offset_to_result:
                    slot_offset_to_result[key] = value
                else:
                    slot_offset_to_result[key].dirty.update(value.dirty)
                    slot_offset_to_result[key].original.update(value.original)
                    slot_offset_to_result[key].raw += value.raw
        total_result += slot_offset_to_result.values()    
        return total_result
