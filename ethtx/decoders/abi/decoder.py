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

import logging
from typing import Optional, Dict, List
from ethtx.models.w3_model import W3StateDiff

from ethtx.models.decoded_model import (
    DecodedTransaction,
    DecodedCall,
    DecodedEvent,
    DecodedTransfer,
    Proxy,
)
from ethtx.models.objects_model import (
    Block,
    BlockMetadata,
    Transaction,
    TransactionMetadata,
    Call,
    Event,
)
from ethtx.utils.measurable import ExecutionTimer
from .abc import IABIDecoder
from .balances import ABIBalancesDecoder
from .calls import ABICallsDecoder
from .events import ABIEventsDecoder
from .transfers import ABITransfersDecoder
from .diffs import ABIDiffsDecoder

log = logging.getLogger(__name__)


def prune_delegates(call: DecodedCall) -> DecodedCall:
    while len(call.subcalls) == 1 and call.subcalls[0].call_type == "delegatecall":
        _value = call.value
        call = call.subcalls[0]
        call.value = _value

    for i, sub_call in enumerate(call.subcalls):
        call.subcalls[i] = prune_delegates(sub_call)

    return call

def get_initial_gas(input: str):
    zero_num = 0 
    nonzero_num = 0  
    for pos in range(2,len(input),2):
        if input[pos:pos+2] == '00':
            zero_num += 1
        else:
            nonzero_num += 1
    return  21000 + zero_num*4 + nonzero_num*16


class ABIDecoder(IABIDecoder):
    def decode_transaction(
        self,
        block: Block,
        transaction: Transaction,
        chain_id: str,
        proxies: Optional[Dict[str, Proxy]] = None,
    ) -> Optional[DecodedTransaction]:

        with ExecutionTimer(f"ABI decoding for " + transaction.metadata.tx_hash):
            log.info(
                "ABI decoding for %s / %s.", transaction.metadata.tx_hash, chain_id
            )
            full_decoded_transaction = self._decode_transaction(
                block.metadata, transaction, chain_id, proxies
            )

        return full_decoded_transaction

    def decode_calls(
        self,
        root_call: Call,
        block: BlockMetadata,
        transaction: TransactionMetadata,
        proxies: Optional[Dict[str, Proxy]] = None,
        chain_id: Optional[str] = None,
    ) -> Optional[DecodedCall]:
        return ABICallsDecoder(
            repository=self._repository, chain_id=chain_id or self._default_chain
        ).decode(
            call=root_call,
            block=block,
            transaction=transaction,
            proxies=proxies,
            chain_id=chain_id or self._default_chain,
        )

    def decode_call(
        self,
        root_call: Call,
        block: BlockMetadata,
        transaction: TransactionMetadata,
        proxies: Optional[Dict[str, Proxy]] = None,
    ) -> Optional[DecodedCall]:
        return ABICallsDecoder(
            repository=self._repository, chain_id=self._default_chain
        ).decode(call=root_call, block=block, transaction=transaction, proxies=proxies)

    def decode_diffs(
        self,
        block: BlockMetadata,
        diffs: List[W3StateDiff],
        shainfo: Dict,
        chain_id: Optional[str] = None,
	proxies: Dict[str, Proxy] = None,
    ):
        return ABIDiffsDecoder(
            repository=self._repository, chain_id=chain_id or self._default_chain
            ).decode(
                diffs=diffs,
                block=block,
                shainfo=shainfo,
                proxies=proxies,
            )

    def decode_events(
        self,
        events: [Event],
        block: BlockMetadata,
        transaction: TransactionMetadata,
        proxies: Optional[Dict[str, Proxy]] = None,
        chain_id: Optional[str] = None,
    ) -> List[DecodedEvent]:
        return ABIEventsDecoder(
            repository=self._repository, chain_id=chain_id or self._default_chain
        ).decode(
            events=events,
            block=block,
            transaction=transaction,
            proxies=proxies or {},
            chain_id=chain_id or self._default_chain,
        )

    def decode_event(
        self,
        events: Event,
        block: BlockMetadata,
        transaction: TransactionMetadata,
        proxies: Optional[Dict[str, Proxy]] = None,
        chain_id: Optional[str] = None,
    ) -> DecodedEvent:
        return ABIEventsDecoder(
            repository=self._repository, chain_id=chain_id or self._default_chain
        ).decode(
            events=events,
            block=block,
            transaction=transaction,
            proxies=proxies or {},
            chain_id=chain_id or self._default_chain,
        )

    def decode_transfers(
        self,
        call: DecodedCall,
        events: List[DecodedEvent],
        proxies: Optional[Dict[str, Proxy]] = None,
        chain_id: Optional[str] = None,
    ):
        return ABITransfersDecoder(
            repository=self._repository, chain_id=chain_id or self._default_chain
        ).decode(call=call, events=events, proxies=proxies or {})

    def decode_balances(self, transfers: List[DecodedTransfer]):
        return ABIBalancesDecoder(
            repository=self._repository, chain_id=self._default_chain
        ).decode(transfers=transfers)

    def _decode_transaction(
        self,
        block: BlockMetadata,
        transaction: Transaction,
        chain_id: str,
        proxies: Optional[Dict[str, Proxy]] = None,
    ) -> DecodedTransaction:


        full_decoded_transaction = DecodedTransaction(
            block_metadata=block,
            metadata=transaction.metadata,
            events=[],
            calls=None,
            transfers=[],
            balances=[],
            nonce=0,
        )

        try:
            full_decoded_transaction.events = self.decode_events(
                transaction.events, block, transaction.metadata, proxies, chain_id
            )
        except Exception as e:
            log.exception(
                "ABI decoding of events for %s / %s failed.",
                transaction.metadata.tx_hash,
                chain_id,
            )
            raise e

        gas_refund = 0
        try:
            full_decoded_transaction.calls = self.decode_calls(
                transaction.root_call, block, transaction.metadata, proxies, chain_id
            )
            if full_decoded_transaction.calls is not None:
                gas_refund = full_decoded_transaction.calls.gas_refund
        except Exception as e:
            log.exception(
                "ABI decoding of calls tree for %s / %s failed.",
                transaction.metadata.tx_hash,
                chain_id,
            )
            raise e

        full_decoded_transaction.metadata.gas_refund =  gas_refund  
        full_decoded_transaction.metadata.total_gas =  full_decoded_transaction.metadata.gas_used + gas_refund  

        try:
            full_decoded_transaction.transfers = self.decode_transfers(
                full_decoded_transaction.calls,
                full_decoded_transaction.events,
                proxies,
                chain_id,
            )
        except Exception as e:
            log.exception(
                "ABI decoding of transfers for %s / %s failed.",
                transaction.metadata.tx_hash,
                chain_id,
            )
            raise e

        try:
            full_decoded_transaction.balances = self.decode_balances(
                full_decoded_transaction.transfers
            )
        except Exception as e:
            log.exception(
                "ABI decoding of balances for %s / %s failed.",
                transaction.metadata.tx_hash,
                chain_id,
            )
            raise e
        try:
            full_decoded_transaction.nonce = transaction.metadata.nonce
        except Exception as e:
            log.exception(
                "getNonce fail %s /%s %s",
                transaction.metadata.tx_hash,
                chain_id,
                transaction.metadata.nonce
            )
            raise e

        try:
            full_decoded_transaction.input = transaction.metadata.input
        except Exception as e:
            log.exception(
                "getNonce fail %s /%s %s",
                transaction.metadata.tx_hash,
                chain_id,
                transaction.metadata
            )
            raise e

        full_decoded_transaction.metadata.initial_gas =   get_initial_gas(full_decoded_transaction.input) 

        print("thechain_id1:", chain_id)
        try:
            diffresults = self.decode_diffs(
                block=block,
                chain_id=chain_id,
                proxies=proxies,
                diffs = transaction.statediff,
                shainfo = transaction.root_call.shainfo, 
            )

            storage_diffs = {}
            balance_nonce_diffs = {}
            for diff in diffresults:
                if len(diff.balance_diff) > 0:
                    balance_diff = diff.balance_diff
                    key =  balance_diff["address"].address
                    if key not in balance_nonce_diffs:
                        balance_nonce_diffs[key] = {"address":balance_diff["address"], "is_miner":balance_diff["is_miner"]}
                    balance_nonce_diffs[key]["Balance"] = {"original":balance_diff["original"],"dirty":balance_diff["dirty"]}

                if len(diff.nonce_diff) > 0:
                    nonce_diff = diff.nonce_diff
                    key = nonce_diff["address"].address
                    if key not in balance_nonce_diffs:
                        balance_nonce_diffs[key] = {"address":nonce_diff["address"], "is_miner":nonce_diff["is_miner"]}
                    balance_nonce_diffs[key]["Nonce"] = {"original":nonce_diff["original"],"dirty":nonce_diff["dirty"]}

                if len(diff.storage_diff) > 0:
                    for storage_diff in diff.storage_diff:
                        key  = storage_diff.contract.address
                        if  key not in storage_diffs:
                            storage_diffs[key] = {"list":[], "contract":storage_diff.contract}
                        storage_diffs[key]["list"].append(storage_diff)
            full_decoded_transaction.balance_nonce_diff = list(balance_nonce_diffs.values())
            full_decoded_transaction.state_diff = list(storage_diffs.values())
        except Exception as e:
            log.exception(
                "ABI decoding of diff for %s / %s failed.",
                transaction.metadata.tx_hash,
                chain_id,
            )
            raise e
        # remove chained delegatecalls from the tree
        prune_delegates(full_decoded_transaction.calls)

        full_decoded_transaction.status = True

        return full_decoded_transaction
