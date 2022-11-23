from ethtx import EthTx, EthTxConfig
from ethtx.models.decoded_model import DecodedTransaction

import os
#os.environ["http_proxy"] = "http://192.168.10.100:10809"
#os.environ["https_proxy"] = "http://192.168.10.100:10809"



ethtx_config = EthTxConfig(
    mongo_connection_string="mongodb://192.168.243.128:27017/ethtx",  ##MongoDB connection string,
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

ethtx = EthTx.initialize(ethtx_config)
decoded_transaction: DecodedTransaction = ethtx.decoders.decode_transaction(
    '0x5af4d87b25cd92de0714cd21f3db5498ad13a150c18650ee40c9a5c1eb208f64')
print(decoded_transaction[0].metadata)
