from typing import List, Dict, Union, Optional

from ethtx.models.decoded_model import DecodedEvent, Proxy, AddressInfo,DecodedDiff
from ethtx.models.objects_model import BlockMetadata, TransactionMetadata, Event, StateDiff
from ethtx.semantics.standards.erc20 import ERC20_EVENTS
from ethtx.semantics.standards.erc721 import ERC721_EVENTS
from .abc import ABISubmoduleAbc
from .helpers.utils import decode_event_abi_name_with_external_source
from ..decoders.parameters import decode_event_parameters
from ethtx.contracts.contract import Contract


class ABIDiffsDecoder(ABISubmoduleAbc):
    """ABI Events Decoder."""

    def decode(
        self,
        block: BlockMetadata,
        diffs: Union[StateDiff, List[StateDiff]],
        shainfo: Dict = None,
        proxies: Dict[str, Proxy] = None,
    ) -> Union[DecodedDiff, List[DecodedDiff]]:
        """Return list of decoded events."""
        if isinstance(diffs, list):
            return (
                [
                    self.decode_diff(block, diff, shainfo,proxies)
                    for diff in diffs
                ]
                if diffs
                else []
            )

        return self.decode_diff(block, diffs, shainfo,proxies)

    def decode_diff(
        self,
        block: BlockMetadata,
        diff: StateDiff,
        shainfo: Dict = None,
        proxies: Dict[str, Proxy] = None,
    ) -> DecodedDiff:
 
        addr_name = self._repository.get_address_label(
            self._default_chain, diff.addr, proxies
        )
        def handle(addr, item):
            if not isinstance(item, dict) or '*' not in item:
                return {}
            realdiff = item["*"]
            return {"address":addr,"original":int(realdiff.original,16), "dirty":int(realdiff.dirty,16),"is_miner": False}

        def handleStorage(addr, storage, shainfo):
            if not isinstance(storage, dict):
                return []
            c = Contract(addr.address)
            res = c.decodeStorageDiff(storage, shainfo)
            for item in res:
                item.contract = addr 
            return res


        addr = AddressInfo(address=diff.addr, name=addr_name)    
        balances = handle(addr, diff.balance)
        if len(balances) > 0:
            balances["is_miner"] = diff.addr == block.miner
        nonces = handle(addr, diff.nonce)
        storages = handleStorage(addr, diff.storage, shainfo)
        return DecodedDiff(
            balance_diff=balances,
            nonce_diff=nonces,
            storage_diff=storages,
        )
