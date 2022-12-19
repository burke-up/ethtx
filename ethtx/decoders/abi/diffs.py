from typing import List, Dict, Union, Optional

from ethtx.models.decoded_model import DecodedEvent, Proxy, AddressInfo,DecodedDiff
from ethtx.models.objects_model import BlockMetadata, TransactionMetadata, Event, W3StateDiff
from ethtx.semantics.standards.erc20 import ERC20_EVENTS
from ethtx.semantics.standards.erc721 import ERC721_EVENTS
from .abc import ABISubmoduleAbc
from .helpers.utils import decode_event_abi_name_with_external_source
from ..decoders.parameters import decode_event_parameters


class ABIDiffsDecoder(ABISubmoduleAbc):
    """ABI Events Decoder."""

    def decode(
        self,
        diffs: Union[W3StateDiff, List[W3StateDiff]],
        block: BlockMetadata,
        transaction: TransactionMetadata,
        proxies: Optional[Dict[str, Proxy]] = None,
        chain_id: Optional[str] = None,
        shainfo: Dict = None,
    ) -> Union[DecodedEvent, List[DecodedEvent]]:
        """Return list of decoded events."""
        if isinstance(diffs, list):
            return (
                [
                    self.decode_diff(diff, block, transaction, proxies, chain_id, shainfo)
                    for diff in diffs
                ]
                if diffs
                else []
            )

        return self.decode_diff(diffs, block, transaction, proxies, chain_id)

    def decode_diff(
        self,
        diff: W3StateDiff,
        block: BlockMetadata,
        transaction: TransactionMetadata,
        proxies: Dict[str, Proxy] = None,
        chain_id: str = None,
        shainfo: Dict = None
    ) -> DecodedDiff:
        def handle(self, addr, item):
            if not isinstance(item, dict) or '*' not in item:
                return {}
            realdiff = item["*"]
            return {"address":addr,"original":realdiff.original, "dirty":realdiff.dirty,"is_miner": False}

        def handleStorage(self, storage):
            if not isinstance(storage, dict):
                return {}
            for k,v in storage.items():
                if "*" not in v:
                    continue
                #TODO handle v["*"]
            return {}
            
        balances = self.handle(diff.addr, diff.balance)
        nonces = self.handle(diff.nonce)
        storages = self.handleStorage(diff.storage)
        return DecodedDiff(
            balance_diff=balances,
            nonce_diff=nonces,
            storage_diff=storages,
        )