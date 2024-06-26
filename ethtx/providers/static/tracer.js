/*
# Copyright 2021 DAI FOUNDATION (the original version https://github.com/daifoundation/ethtx_ce)
# Copyright 2021-2022 Token Flow Insights SA (modifications to the original software as recorded
# in the changelog https://github.com/EthTx/ethtx/blob/master/CHANGELOG.md)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
#
# The product contains trademarks and other branding elements of Token Flow Insights SA which are
# not licensed under the Apache 2.0 license. When using or reproducing the code, please remove
# the trademark and/or other branding elements.
 */

{
	// callstack is the current recursive call stack of the EVM execution.
	callstack: [{}],

	// descended tracks whether we've just descended from an outer transaction into
	// an inner call.
	descended: false,

	returnData: undefined,

	lastThreeOps:   [],

	afterSHA: false,
	lastKey: "",
	shainfo : {},
	iscall: true,
        lastPc: 0,
	gas_refund: 0,
	

	// step is invoked for every opcode that the VM executes.
	step: function(log, db) {
                this.gas_refund = log.getRefund();
		// Capture any errors immediately
		var error = log.getError();
		if (error !== undefined) {
			this.fault(log, db);
			return;
		}
		var op = log.op.toString();	
		if(this.afterSHA){
			var key = log.stack.peek(0).toString(16);
			this.shainfo[key] = this.lastKey;
		}

		this.afterSHA  = false;		
		if(op == "SHA3" || op == "KECCAK256"){
			var outOff = log.stack.peek(0).valueOf();
			var outEnd = outOff + log.stack.peek(1).valueOf();
			var param = toHex(log.memory.slice(outOff, outEnd));
			this.lastKey = param;
			this.afterSHA  =true;
		}
		

		if(this.iscall){
			if(this.lastThreeOps.length>=3){
				if(op == "JUMPDEST"){
					length = this.lastThreeOps.length;
					if(this.lastThreeOps[length-1] == "JUMP"
					 || (this.lastThreeOps[length-1] == "JUMPI" && this.lastThreeOps[length-3]=="EQ")){
						this.callstack[this.callstack.length-1].toPc  =  log.getPC();
						this.iscall = false;
					}					
				}	
				this.lastThreeOps.shift();
			}
			this.lastThreeOps.push(op);
		}else{
			var left = this.callstack.length;
			if(op == "JUMP"){				
				if(this.callstack[left-1].jumps == undefined){
					this.callstack[left-1].jumps = [];
				}
				this.callstack[left-1].jumps.push(log.getPC());
			}
		}
                this.lastPc = log.getPC();

		// We only care about system opcodes, faster if we pre-check once
		var syscall = (log.op.toNumber() & 0xf0) == 0xf0;
		if (syscall) {
			var op = log.op.toString();
		}
		if (op === "RETURN") {
			var outOff = log.stack.peek(0).valueOf();
			var outEnd = outOff + log.stack.peek(1).valueOf();
			this.returnData = toHex(log.memory.slice(outOff, outEnd));
		}
		// If a new contract is being created, add to the call stack
		if (syscall && (op == 'CREATE' || op == "CREATE2")) {
			var inOff = log.stack.peek(1).valueOf();
			var inEnd = inOff + log.stack.peek(2).valueOf();

			// Assemble the internal call report and store for completion
			var call = {
				type:    op,
				from:    toHex(log.contract.getAddress()),
				input:   toHex(log.memory.slice(inOff, inEnd)),
				gasIn:   log.getGas(),
				gasCost: log.getCost(),
				value:   '0x' + log.stack.peek(0).toString(16),
				pc:      log.getPC(),
                                toPc: 0,
				revertPc: 0,
				jumps: [],
			};
			this.callstack.push(call);
			this.descended = true
			return;
		}
		// If a contract is being self destructed, gather that as a subcall too
		if (syscall && op == 'SELFDESTRUCT') {
			var left = this.callstack.length;
			if (this.callstack[left-1].calls === undefined) {
				this.callstack[left-1].calls = [];
			}
			this.callstack[left-1].calls.push({
				type:    op,
				from:    toHex(log.contract.getAddress()),
				to:      toHex(toAddress(log.stack.peek(0).toString(16))),
				gasIn:   log.getGas(),
				gasCost: log.getCost(),
				value:   '0x' + db.getBalance(log.contract.getAddress()).toString(16),
				pc:       log.getPC(),
                                toPc:  0,
				revertPc: 0,
				jumps: [],
			});
			return
		}
		// If a new method invocation is being done, add to the call stack
		if (syscall && (op == 'CALL' || op == 'CALLCODE' || op == 'DELEGATECALL' || op == 'STATICCALL')) {
			// Skip any pre-compile invocations, those are just fancy opcodes
			var to = toAddress(log.stack.peek(1).toString(16));
			if (isPrecompiled(to)) {
				return
			}
			var off = (op == 'DELEGATECALL' || op == 'STATICCALL' ? 0 : 1);

			var inOff = log.stack.peek(2 + off).valueOf();
			var inEnd = inOff + log.stack.peek(3 + off).valueOf();

			// Assemble the internal call report and store for completion
			var call = {
				type:    op,
				from:    toHex(log.contract.getAddress()),
				to:      toHex(to),
				input:   toHex(log.memory.slice(inOff, inEnd)),
				gasIn:   log.getGas(),
				gasCost: log.getCost(),
				outOff:  log.stack.peek(4 + off).valueOf(),
				outLen:  log.stack.peek(5 + off).valueOf(),
				pc:      log.getPC(),
				toPc: 0,
				revertPc: 0,
				jumps: [],
			};
			if (op != 'DELEGATECALL' && op != 'STATICCALL') {
				call.value = '0x' + log.stack.peek(2).toString(16);
			}
			this.callstack.push(call);
			this.descended = true
            this.iscall = true;
			return;
		}
		// If we've just descended into an inner call, retrieve it's true allowance. We
		// need to extract if from within the call as there may be funky gas dynamics
		// with regard to requested and actually given gas (2300 stipend, 63/64 rule).
		if (this.descended) {
			if (log.getDepth() >= this.callstack.length) {
				this.callstack[this.callstack.length - 1].gas = log.getGas();
			} else {
				// TODO(karalabe): The call was made to a plain account. We currently don't
				// have access to the true gas amount inside the call and so any amount will
				// mostly be wrong since it depends on a lot of input args. Skip gas for now.
			}
			this.descended = false;
		}
		// If an existing call is returning, pop off the call stack
		if (syscall && op == 'REVERT') {
			this.callstack[this.callstack.length - 1].error = "execution reverted";
			this.callstack[this.callstack.length - 1].revertPc = log.getPC();
			return;
		}
		if (log.getDepth() == this.callstack.length - 1) {
			// Pop off the last call and get the execution results
			var call = this.callstack.pop();

			if (call.type == 'CREATE' || call.type == "CREATE2") {
				// If the call was a CREATE, retrieve the contract address and output code
				call.gasUsed = '0x' + bigInt(call.gasIn - call.gasCost - log.getGas()).toString(16);
				delete call.gasIn; delete call.gasCost;

				var ret = log.stack.peek(0);
				if (!ret.equals(0)) {
					call.to     = toHex(toAddress(ret.toString(16)));
					call.output = toHex(db.getCode(toAddress(ret.toString(16))));
				} else if (call.error === undefined) {
					call.error = "internal failure"; // TODO(karalabe): surface these faults somehow
				}
			} else {
				// If the call was a contract call, retrieve the gas usage and output
				if (call.gas !== undefined) {
					call.gasUsed = '0x' + bigInt(call.gasIn - call.gasCost + call.gas - log.getGas()).toString(16);
				}
				var ret = log.stack.peek(0);
				if (!ret.equals(0)) {
					call.output = this.returnData;
				} else if (call.error === undefined) {
					call.error = "internal failure"; // TODO(karalabe): surface these faults somehow
				}
				delete call.gasIn; delete call.gasCost;
				delete call.outOff; delete call.outLen;
			}
			if (call.gas !== undefined) {
				call.gas = '0x' + bigInt(call.gas).toString(16);
			}
			// Inject the call into the previous one
			var left = this.callstack.length;
			if (this.callstack[left-1].calls === undefined) {
				this.callstack[left-1].calls = [];
			}
			this.callstack[left-1].calls.push(call);
			this.returnData = undefined;
		}
	},

	// fault is invoked when the actual execution of an opcode fails.
	fault: function(log, db) {
                this.gas_refund = log.getRefund();
		// If the topmost call already reverted, don't handle the additional fault again
		if (this.callstack[this.callstack.length - 1].error !== undefined) {
			return;
		}
		// Pop off the just failed call
		var call = this.callstack.pop();
		call.error = log.getError();

		// Consume all available gas and clean any leftovers
		if (call.gas !== undefined) {
			call.gas = '0x' + bigInt(call.gas).toString(16);
			call.gasUsed = call.gas
		}
		delete call.gasIn; delete call.gasCost;
		delete call.outOff; delete call.outLen;

		// Flatten the failed call into its parent
		var left = this.callstack.length;
		if (left > 0) {
			if (this.callstack[left-1].calls === undefined) {
				this.callstack[left-1].calls = [];
			}
			this.callstack[left-1].calls.push(call);
			return;
		}
		// Last call failed too, leave it in the stack
		this.callstack.push(call);
	},

	// result is invoked when all the opcodes have been iterated over and returns
	// the final result of the tracing.
	result: function(ctx, db) {

		var result = {
			type:    ctx.type,
			from:    toHex(ctx.from),
			to:      toHex(ctx.to),
			value:   '0x' + ctx.value.toString(16),
			gas:     '0x' + bigInt(ctx.gas).toString(16),
			gasUsed: '0x' + bigInt(ctx.gasUsed).toString(16),
			input:   toHex(ctx.input),
			output:  toHex(ctx.output),
			time:    ctx.time,
			pc:      0,
			toPc:    0,
			revertPc: 0,
			jumps: [],
			shainfo: this.shainfo,
			gas_refund: this.gas_refund,	
		};
		if (this.callstack[0].calls !== undefined) {
			result.calls = this.callstack[0].calls;
		}
		if (this.callstack[0].error !== undefined) {
			result.error = this.callstack[0].error;
		} else if (ctx.error !== undefined) {
			result.error = ctx.error;
		}
		if(this.callstack[0].toPc !== undefined){
                   result.pc = this.callstack[0].toPc;
                   result.toPc = this.callstack[0].toPc;
		}
		if(this.callstack[0].revertPc !== undefined){
                    result.revertPc = this.callstack[0].revertPc;
		}
		if (result.error !== undefined && (result.error !== "execution reverted" || result.output ==="0x")) {
			delete result.output;
		}
		if(this.callstack[0].jumps !== undefined){
			result.jumps = this.callstack[0].jumps;
		}
		
		return this.finalize(result);
	},

	// finalize recreates a call object using the final desired field oder for json
	// serialization. This is a nicety feature to pass meaningfully ordered results
	// to users who don't interpret it, just display it.
	finalize: function(call) {
		var sorted = {
			type:    call.type,
			from:    call.from,
			to:      call.to,
			value:   call.value,
			gas:     call.gas,
			gasUsed: call.gasUsed,
			input:   call.input,
			output:  call.output,
			error:   call.error,
			time:    call.time,
			calls:   call.calls,
			pc:      call.pc,
			toPc:      call.toPc,
			revertPc: call.revertPc,
			jumps: call.jumps,
			shainfo: call.shainfo,
			gas_refund: call.gas_refund,

		}
		for (var key in sorted) {
			if (sorted[key] === undefined) {
				delete sorted[key];
			}
		}
		if (sorted.calls !== undefined) {
			for (var i=0; i<sorted.calls.length; i++) {
				sorted.calls[i] = this.finalize(sorted.calls[i]);
			}
		}
		return sorted;
	}
}
