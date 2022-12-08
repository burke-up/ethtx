from ethtx import EthTx, EthTxConfig
from ethtx.models.decoded_model import DecodedTransaction,DecodedCall
import json
import binascii
import json
from pyevmasm import *
from eth_utils import event_abi_to_log_topic, function_abi_to_4byte_selector
import typing
import sys

import os
#os.environ["http_proxy"] = "http://192.168.10.100:10809"
#os.environ["https_proxy"] = "http://192.168.10.100:10809"

def abi_to_selector(abi):
    if abi['type'] == 'event':
        selector = '0x' + event_abi_to_log_topic(abi).hex()
    else:
        selector = '0x' + function_abi_to_4byte_selector(abi).hex()
    return selector

def abi_to_selectors(info):
    result = []
    for item in info:
        if not "name" in item or item["name"] == None or item["name"] == "":
            continue
        selector = abi_to_selector(item)
        result.append({"selector":selector,"abi":item})
    return result

def decompressSourceMap(sourcemap):
    maps = sourcemap.split(";")
    firstMaps = maps[0].split(":")
    if len(firstMaps) < 4: return False
    #start, length, fileno, jump = firstMaps
    result = [firstMaps]
    lastMapping = firstMaps.copy()
    for pos in range(1, len(maps)):
        items = maps[pos].split(":")
        for firstPos in range(len(lastMapping)):
            if len(items)<=firstPos:
                items.append("")
            if items[firstPos] == "":
                items[firstPos] = lastMapping[firstPos]
        lastMapping = items.copy()
        result.append(items)
    return result

def loadCompileResult(contractAddress):
    
    #contractAddress,functionselector ==> filename
    #contractAddress=>sourceList
    #filename=>[pc=>[decompressedSourceMap],]
    fp = open("/root/project/compileTests/bytecodes/%s/combined_solc.json"%(contractAddress),"r")
    data = fp.read()
    fp.close()
    compileInfo = json.loads(data)
    sourceList = compileInfo["sourceList"]
    functionselector2filename = {}
    filenameAndPc2SourceMap = {}
    
    maxByteCodeKey = ""
    maxByteCode = -1
    for filenameWithSol, compileUnit in compileInfo["contracts"].items():
        if  "bin-runtime" in compileUnit and len(compileUnit["bin-runtime"]) > maxByteCode:
            maxByteCodeKey = filenameWithSol
            maxByteCode =  len(compileUnit["bin-runtime"]) 
    filenameWithSol =   maxByteCodeKey    
    compileUnit =   compileInfo["contracts"][filenameWithSol]
    filename = filenameWithSol[0:filenameWithSol.rindex(":")]
    if "abi" not in compileUnit or "srcmap-runtime" not in compileUnit or "bin-runtime" not in compileUnit:            
        raise Exception("cannot get abi or srcmap-runtime or bin-runtime ")
    if compileUnit["abi"] == "" or compileUnit["srcmap-runtime"] == "" or compileUnit["bin-runtime"] =="":            
        raise Exception("cannot get abi or srcmap-runtime or bin-runtime empty ")
    abi = compileUnit["abi"]
    #current_app.logger.info("abi1=%s"%(abi))
    jsonabi = json.loads(abi)
    if len(jsonabi) == 0:            
        raise Exception("cannot get jsonabi or bin-runtime ")
    abiresult = abi_to_selectors(jsonabi)

    for row in abiresult:
        selector = row["selector"]    
        functionselector2filename[selector] = filename


    srcmapRuntime = compileUnit["srcmap-runtime"]
    bytecodeRuntime = compileUnit["bin-runtime"]
    decompressedSourceMap = decompressSourceMap(sourcemap=srcmapRuntime)

    bytecode = bytecodeRuntime.strip().rstrip()
    bytecodeReal = bytecode
    if bytecode.startswith("0x"):
        bytecodeReal = bytecode[2:]
    buf = binascii.unhexlify(bytecodeReal)
    disassemBytecode = tuple(disassemble_all(buf))
    pc2sourcemap = {}
    postfix = filenameWithSol[filenameWithSol.rindex(":")+1:]
    output_fp = open("output_%s.txt"%(postfix),"w")
    for pos in range(len(disassemBytecode)):
        row = disassemBytecode[pos]
        if len(decompressedSourceMap) <= pos:
            break
        output_fp.write("%s,%s,\n"%(row.pc, row.name))
        pc2sourcemap[row.pc] = [decompressedSourceMap[pos],row]
    output_fp.close()

    filenameAndPc2SourceMap[filename] = pc2sourcemap
    return [sourceList, pc2sourcemap]    

# confs = loadCompileResult("0x306b1ea3ecdf94ab739f1910bbda052ed4a9f949")
# print(confs)

# sys.exit(-1)

contract2compile = {}
baseFileDir="/root/project/compileTests"
def getFileNameAndNo(contract_address,pc):
    if contract_address not in contract2compile:
        compileResult = loadCompileResult(decoded_transaction.calls.to_address.address)
        contract2compile[contract_address] = compileResult
    sourcelist, pc2sourcemap = contract2compile.get(contract_address)
    sourcemap = pc2sourcemap[pc][0]
    start,length,fileno = sourcemap[0:3]
    start = int(start)
    length = int(length)
    fileno = int(fileno)
    filename = sourcelist[fileno]
    fp = open("%s/%s"%(baseFileDir,filename),"r")
    data = fp.read()
    fp.close()
    code = data[start:start+length]
    lineinfo = data[0:start].split('\n')
    lineno = len(lineinfo)
    linecode = data.split("\n")[lineno-1]
    shortfilename = filename.split('/')[-1]
    return [code, linecode, filename,shortfilename,lineno]

ethtx_config = EthTxConfig(
    mongo_connection_string="mongodb://127.0.0.1:27017/ethtx",  ##MongoDB connection string,
    etherscan_api_key="9MB9GKUGPQIFN9V4UW73NNEI2D3HKSQYCG",  ##Etherscan API key,
    web3nodes={
        "mainnet": {
            "hook": "https://white-bitter-leaf.discover.quiknode.pro/5f1727b7556c2d874c1050aa0f3c23ac8ded3d73/",  # multiple nodes supported, separate them with comma
            "poa": False  # represented by bool value
        }
    },
    default_chain="mainnet",
    etherscan_urls={"mainnet": "https://api.etherscan.io/api", },
)

txhash = "0x07b5e887131fc6d7ba126c7d433fee5b74e9e194a73270a676bbc33bb4220335"
ethtx = EthTx.initialize(ethtx_config)
decoded_transaction = ethtx.decoders.decode_transaction(txhash)
calls  = decoded_transaction.calls
print(decoded_transaction)

#print("showCallsStart:")
#def printCall(call):
#    print(call.pc,call.call_type, call.revertPc,call.from_address, call.to_address)
#    filenoinfo = getFileNameAndNo(call.to_address,call.pc)
#    print(filenoinfo)
#    if not call.subcalls or len(call.subcalls) == 0:
#        if call.revertPc != 0:
#            filenoinfo = getFileNameAndNo(call.to_address,call.revertPc)
#            print(filenoinfo)
#        return 
#    printCall(call.subcalls[len(call.subcalls)-1])
#printCall(calls)
#print("showCallsEnd:")
