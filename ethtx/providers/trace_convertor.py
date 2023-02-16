import json
import sys

class TraceConvertor():
    def __init__(self, from_address, to_address):
        self.callstack = [{"from":from_address,"to":to_address, "type":"CALL"}]
        self.shainfo = {}
        self.descended = False
        self.lastThreeOps = []
        self.afterSHA = False
        self.lastKey = ""
        self.iscall = True
        self.lastPc = 0
        self.returnData = None
        self.gas_refund = 0
        
    
    def getStackPeek(self, stack, pos):
        return stack[len(stack)-1-pos]
        



    def handleSHA(self, item):
        stack = item["stack"]
        if self.afterSHA:
            key = stack[len(stack)-1][2:]
            self.shainfo[key] = self.lastKey
            self.afterSHA = False
        op = item["op"]
        if op == "SHA3" or op == "KECCAK256":
            outOff = int(self.getStackPeek(stack,0),16)
            outEnd = outOff + int(self.getStackPeek(stack,1),16)
            param = "".join(item["memory"])[outOff*2:outEnd*2]
            if len(param) == 0:
                print("empty: %s %s %s"%(outOff, outEnd, item["memory"]))
            self.lastKey = "0x%s"%param
            self.afterSHA = True


    def handleJUMP(self, item):
        op = item["op"]
        self.lastPc = item["pc"]
        if self.iscall:
            if len(self.lastThreeOps) >= 3:
                if op == "JUMPDEST":
                    opsLen = len(self.lastThreeOps)
                    if self.lastThreeOps[opsLen-1] == "JUMP" or self.lastThreeOps[opsLen-1] == "JUMPI" and  self.lastThreeOps[opsLen-3] == "EQ":
                        self.callstack[len(self.callstack)-1]["toPc"] = item["pc"] 
                        self.iscall = False
            self.lastThreeOps.append(op)
            return 
        
        callstackLens = len(self.callstack)
        if op == "JUMP":
            if "jumps" not in self.callstack[callstackLens-1]:
                self.callstack[callstackLens-1]["jumps"] = []
            self.callstack[callstackLens-1]["jumps"].append(item["pc"])


    def handleReturn(self, item):
        if item["op"] != "RETURN":
            return 
        stack = item["stack"]
        outOff = int(self.getStackPeek(stack,0),16)
        outEnd = outOff + int(self.getStackPeek(stack, 1),16)
        self.returnData = "0x%s"%("".join(item["memory"])[outOff*2:outEnd*2])

    def handleContractCreate(self, item):
        op = item["op"]
        if op != "CREATE" and op != "CREATE2":
            return False
        inOff = int(self.getStackPeek(stack, 1),16)
        inEnd = inOff + int(self.getStackPeek(stack, 2),16)
        input = "0x%s"%("".join(item["memory"])[inOff*2:inEnd*2])

        stack = item["stack"]
        call = {
            "type": op,
            "from": "",
            "input":input,
            "gasIn": item["gas"],
            "gasCost": item["gasCost"],
            "value": self.getStackPeek(stack, 0),
            "pc": item["pc"],
            "toPc": 0,
            "revertPc": 0,
            "jumps":[]
        }
        self.callstack.append(call)
        self.descended = True
        return True



    def handleSelfDestrcut(self, item):
        op = item["op"]
        if op != "SELFDESTRUCT":
            return False
        left = len(self.callstack)
        if "calls" not in self.callstack[left-1]:
            self.callstack[left-1]["calls"] = []
        stack = item["stack"]
        call = {
            "type": op,
            "from":"",
            "to": self.getStackPeek(0),
            "gasIn": item["gas"],
            "gasCost": item["gasCost"],
            "value": 0,  #TODO  cal value from balance
            "pc": item["pc"],
            "toPc": 0,
            "revertPc": 0,
            "jumps":[]
        } 
        self.callstack[left-1]["calls"].append(call)        
        return True

    def handleCall(self, item):
        op = item["op"]
        if op != 'CALL' and op != 'CALLCODE' and  op != 'DELEGATECALL' and  op != 'STATICCALL':
            return False
        stack = item["stack"]
        to = self.getStackPeek(stack, 1)
        if len(to) == 3 and 1<=int(to,16) <= 9:
            return True
        off = 1
        if op == "DELEGATECALL" or op == "STATICCALL": 
            off = 0
        
        inOff = int(self.getStackPeek(stack, 2+off),16)
        inEnd = inOff + int(self.getStackPeek(stack, 3+off),16)

        input = "0x%s"%("".join(item["memory"])[inOff*2:inEnd*2]) 

        call = {
            "type": op,
            "from": self.callstack[len(self.callstack)-1].get("to","111"),
            "to": "0x%s"%(to[2:].zfill(40)),
            "input":input,
            "gasIn": item["gas"],
            "gasCost": item["gasCost"],
            "outOff": int(self.getStackPeek(stack, 4+off),16),
            "outLen": int(self.getStackPeek(stack, 5+off),16),
            "pc": item["pc"],
            "toPc": 0,
            "revertPc": 0,
            "jumps":[]
        }
        if op != "DELEGATECALL" and op != "STATICCALL":
            call["value"] = self.getStackPeek(stack, 2)
        self.callstack.append(call)
        self.descended = True
        self.iscall = True
        return True

    def handleDescended(self, item):
        if not self.descended:
            return 
        if item["depth"] >= len(self.callstack):
            self.callstack[len(self.callstack)-1]["gas"] = item["gas"]
        self.descended = False

    def handleRevert(self, item):
        if item["op"] != "REVERT":
            return  False
        self.callstack[len(self.callstack)-1]["error"] = "execution reverted"
        self.callstack[len(self.callstack)-1]["revertPc"] = item["pc"]
        return True

    def handleContractChange(self, item):
        if item["depth"] != len(self.callstack)-1:
            return 
        call = self.callstack.pop()
        stack = item["stack"]
        ret = self.getStackPeek(stack,0)

        if call["type"] == "CREATE" or call["type"] == "CREATE2":
            call["gasUsed"] = call["gasIn"] - call["gasCost"]-item["gas"]
            del call["gasIn"]
            del call["gasCost"]

            if ret != "0":
                call["to"] = ret
                call["output"] = ""   #TODO toHex(db.getCode(toAddress(ret.toString(16))));
            elif "error" not in call:
                call["error"] = "internal failure"
        else:
            if "gas"  in call:
                call["gasUsed"] = call["gasIn"] - call["gasCost"] + call["gas"] - item["gas"]
            if ret != "0":
                call["output"] = self.returnData
            elif "error" not in call:
                call["error"] = "internal failure"
            del call["gasIn"]
            del call["gasCost"]
            del call["outOff"]
            del call["outLen"]

        # if "gas" in call:
        #     call["gas"] = int(call["gas"],16)
        
        left = len(self.callstack)
        if "calls" not in self.callstack[left-1]:
            self.callstack[left-1]["calls"] = []
        # call["from"] =  self.callstack[left-1].get("to","not")
        self.callstack[left-1]["calls"].append(call)
        self.returnData = None

    def delempty(self, result):
        fullkeys = list(result.keys())
        for key in fullkeys: 
            if  result[key] is None:
                del result[key]

        if "calls" in result and len(result["calls"]) > 0:
            for call in  result["calls"]:
                self.delempty(call)

    def addFrom(self, call, curaddress):
        if call["type"] != "DELEGATECALL":
            curaddress = call["to"]
        for subcall in call.get("calls",[]):
            # print("call=%s subcall:%s"%(call, subcall))            
            subcall["from"] = curaddress
            self.addFrom(subcall, curaddress)
    
    def addFromTotal(self):
        self.addFrom(self.callstack[0], self.callstack[0]["from"])


    def decode(self, tracedata, w3transaction):
        structLogs = tracedata.get("structLogs",[])
        for item in structLogs:
            self.handleSHA(item)
            self.handleJUMP(item)
            self.handleReturn(item)
            if self.handleContractCreate(item):
                continue
            if self.handleSelfDestrcut(item):
                continue

            if self.handleCall(item):
                continue
            self.handleDescended(item)
            if  self.handleRevert(item):
                continue

            self.handleContractChange(item)
        self.addFromTotal()

        result = {
            "type": "CALL",
            "from": w3transaction.from_address,
            "to": w3transaction.to,
            "value": w3transaction.value,
            "gas": tracedata["gas"],
            "gasUsed": w3transaction.gas ,
            "input": w3transaction.input,
            "output": tracedata["returnValue"],
            "time": "",
            "pc": 0,
            "toPc": 0,
            "revertPc": 0,
            "jumps": [],
            "shainfo": self.shainfo,
            "gas_refund": self.gas_refund            
        }

        if "calls" in self.callstack[0]:
            result["calls"] = self.callstack[0]["calls"]
        if "error" in self.callstack[0]:
            result["error"] = self.callstack[0]["error"]
        
        if "toPc" in self.callstack[0]:
            result["pc"] = self.callstack[0]["toPc"]
            result["toPc"] = self.callstack[0]["toPc"]
        
        if "revertPc" in self.callstack[0]:
            result["revertPc"] = self.callstack[0]["revertPc"]
        
        if "error" in result and (result["error"] != "execution reverted" or result["output"] == "0x"):
            del result["output"]
        if "jumps" in self.callstack[0]:
            result["jumps"] = self.callstack[0]["jumps"]
        self.delempty(result)
        return result        
