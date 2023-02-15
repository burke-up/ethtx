import json
import sys

fp = open("data.txt","r")
data = fp.read()
fp.close()

info = json.loads(data)
structLogs = info["result"]["structLogs"]



class TraceConvertor():
    def __init__(self):
        self.callstack = [{}]
        self.shainfo = {}
        self.descended = False
        self.lastThreeOps = []
        self.afterSHA = False
        self.lastKey = ""
        self.iscall = True
        self.lastPc = 0
        self.returnData = ""
        self.precompiledContracts = []
        self.gas_refund = 0
    
    def getStackPeek(self, stack, pos):
        return stack[len(stack)-1-pos]
        



    def handleSHA(self, item):
        stack = item["stack"]
        if self.afterSHA:
            key = stack[len(stack)-1]
            self.shainfo[key] = self.lastKey
            self.afterSHA = False
        op = item["op"]
        if op == "SHA3" or op == "KECCAK256":
            outOff = int(self.getStackPeek(stack,0),16)
            outEnd = int(self.getStackPeek(stack,1),16)
            param = "".join(item["memory"])[outOff*2:outEnd*2]
            self.lastKey = param
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
        outEnd = int(self.getStackPeek(stack, 1),16)
        self.returnData = "".join(item["memory"])[outOff*2:outEnd*2] 

    def handleContractCreate(self, item):
        op = item["op"]
        if op != "CREATE" and op != "CREATE2":
            return False
        inOff = int(self.getStackPeek(stack, 1),16)
        inEnd = inOff + int(self.getStackPeek(stack, 2),16)
        input = "".join(item["memory"])[inOff*2:inEnd*2] 

        stack = item["stack"]
        call = {
            "type": op,
            "from": "",
            "input":input,
            "gasIn": item["gas"],
            "gasCost": item["gasCost"],
            "value": int(self.getStackPeek(stack, 0),16),
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
        to = stack[len(stack)-1]
        if to in self.precompiledContracts:
            return True
        off = 1
        if op == "DELEGATECALL" or op == "STATICCALL":
            off = 0
        
        inOff = int(self.getStackPeek(stack, 2+off),16)
        inEnd = inOff + int(self.getStackPeek(stack, 3+off),16)


			# var call = {
			# 	type:    op,
			# 	from:    toHex(log.contract.getAddress()),
			# 	to:      toHex(to),
			# 	input:   toHex(log.memory.slice(inOff, inEnd)),
			# 	gasIn:   log.getGas(),
			# 	gasCost: log.getCost(),
			# 	outOff:  log.stack.peek(4 + off).valueOf(),
			# 	outLen:  log.stack.peek(5 + off).valueOf(),
			# 	pc:      log.getPC(),
			# 	toPc: 0,
			# 	revertPc: 0,
			# 	jumps: [],
			# };

        input = "".join(item["memory"])[inOff*2:inEnd*2] 

        call = {
            "type": op,
            "from": "",
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
            call["value"] = int(self.getStackPeek(stack, 2), 16)
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
        self.callstack[left-1]["calls"].append(call)
        self.returnData = None

    def decode(self, structLogs):
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
        result = {
            "type": "CALL",
            "from": "",
            "to": "",
            "value": "",
            "gas": 0,
            "gasUsed": 0,
            "input": "",
            "output":"",
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
        return result        

    



