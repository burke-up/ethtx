import json


def  addStateDiffData(semantically_decoded_tx):
        data0 = """
{
	"contract": {
		"address": "0xe0554a476a092703abdb3ef35c80e0d76d32939f",
		"badge": null,
		"name": "0xe0554a476a092703abdb3ef35c80e0d76d32939f"
	},
	"standard": null,
	"showtype": 0,
	"raw": [
		{
			"address": "0xe0554a476a092703abdb3ef35c80e0d76d32939f",
			"key": "0x0000000000000000000000000000000000000000000000000000000000000000",
			"original": "0x0001000001000100000320b70000000000006e5456544faf19e228e0a890bd67",
			"dirty": "0x0001000001000100000320b90000000000006e57f633dd937350628ae5e3d9ea"
		}
	],
	"soltype": null,
	"original": null,
	"dirty": null
}
"""

        data1 = """
{
	"contract": {
		"address": "0xec7a6619c3b5c251ca6ac8ee3d126d66e9541050",
		"badge": null,
		"name": "UniswapV2Pair"
	},
	"standard": null,
	"showtype": 1,
	"soltype": {
		"name": "reserve1",
		"type": "uint112",
		"storage_location": "storage"
	},
	"original": "10221902306807939098830",
	"dirty": "10295072266380939098830",
	"raw": [
		{
			"address": "0xec7a6619c3b5c251ca6ac8ee3d126d66e9541050",
			"key": "0x0000000000000000000000000000000000000000000000000000000000000008",
			"original": "0x638fc81f00000000022a21642615113468ce0000000000047247a20ddc61d09a",
			"dirty": "0x638fc87300000000022e18d410a4938fface0000000000046a36be51cd8a33a9"
		}
	]
}

"""
        data2 = """
{
	"contract": {
		"address": "0xb0853c198de261c8fcc277961b607b02caba608a1e14de7209b1c1f9cb5ca5ef",
		"badge": null,
		"name": "FiatTokenProxy"
	},
	"standard": null,
	"showtype": 2,
	"raw": [
		{
			"address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
			"key": "0xb9f6591fc52eba3e15c8a35522a85e6d320e9084debe30399ae4770e63f89389",
			"original": "0x000000000000000000000000000000000000000000000000000000b341e17238",
			"dirty": "0x000000000000000000000000000000000000000000000000000000b31676d294"
		},
		{
			"address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
			"key": "0xefe0aee3351f0e467e6955cf34388cf3518c95410d79450000a4f0a16f687cff",
			"original": "0x0000000000000000000000000000000000000000000000000000000a4ae25021",
			"dirty": "0x0000000000000000000000000000000000000000000000000000000a764cefc5"
		}
	],
	"soltype": {
		"name": "balances",
		"type": "mapping (address => uint256)",
		"storage_location": "storage"
	},
	"original": {
		"0x88f859db067c45b114897db6920f3e4a61a5ca66": "44206018593",
		"0xe0554a476a092703abdb3ef35c80e0d76d32939f": "769904439864"
	},
	"dirty": {
		"0x88f859db067c45b114897db6920f3e4a61a5ca66": "44934426565",
		"0xe0554a476a092703abdb3ef35c80e0d76d32939f": "769176031892"
	}
}

        """

        data3 = """
{
	"contract": {
		"address": "0xd9c2d319cd7e6177336b0a9c93c21cb48d84fb54",
		"badge": null,
		"name": "HAPI"
	},
	"standard": "ERC20",
	"showtype": 3,
	"soltype": {
		"name": "_allowances",
		"type": "mapping (address => mapping (address => uint256))",
		"storage_location": "storage"
	},
	"original": {
		"0x88f859db067c45b114897db6920f3e4a61a5ca66": {
			"0x216b4b4ba9f3e719726886d34a177484278bfcae": "115792089237316195423570985008687907853269984665640564038258935799533129639935"
		}
	},
	"dirty": {
		"0x88f859db067c45b114897db6920f3e4a61a5ca66": {
			"0x216b4b4ba9f3e719726886d34a177484278bfcae": "115792089237316195423570985008687907853269984665640564038185765839960129639935"
		}
	},
	"raw": [
		{
			"address": "0xd9c2d319cd7e6177336b0a9c93c21cb48d84fb54",
			"key": "0x99a21c1e6a4c67496c8229bf236037e8816dbfa2b290df1ef4c231ca04e5b8ae",
			"original": "0xffffffffffffffffffffffffffffffffffffffffffffffbf056a1d3053b327ff",
			"dirty": "0xffffffffffffffffffffffffffffffffffffffffffffffbb0dfa32a0d15795ff"
		}
	]
}
"""
        data4 = """
{
	"contract": {
		"address": "0x306b1ea3ecdf94ab739f1910bbda052ed4a9f949",
		"badge": null,
		"name": "Beanz"
	},
	"standard": "ERC721",
	"showtype": 4,
	"soltype": {
		"name": "_addressData",
		"type": "mapping (address => tuple)",
		"storage_location": "storage",
		"components": [
			{
				"name": "balance",
				"type": "uint64",
				"storage_location": "memory",
				"components": null
			},
			{
				"name": "numberMinted",
				"type": "uint64",
				"storage_location": "memory",
				"components": null
			},
			{
				"name": "numberBurned",
				"type": "uint64",
				"storage_location": "memory",
				"components": null
			},
			{
				"name": "aux",
				"type": "uint64",
				"storage_location": "memory",
				"components": null
			}
		]
	},
	"original": {
		"0x0087b34553830a3da3a64614b3eae9f5aca5ea38": {
			"balance": 3,
			"numberMinted": 0,
			"numberBurned": 0,
			"aux": 0
		},
		"0xe52cec0e90115abeb3304baa36bc2655731f7934": {
			"balance": 4,
			"numberMinted": 0,
			"numberBurned": 0,
			"aux": 0
		}
	},
	"dirty": {
		"0x0087b34553830a3da3a64614b3eae9f5aca5ea38": {
			"balance": 2,
			"numberMinted": 0,
			"numberBurned": 0,
			"aux": 0
		},
		"0xe52cec0e90115abeb3304baa36bc2655731f7934": {
			"balance": 5,
			"numberMinted": 0,
			"numberBurned": 0,
			"aux": 0
		}
	},
	"raw": [
		{
			"address": "0x306b1ea3ecdf94ab739f1910bbda052ed4a9f949",
			"key": "0x0a3cc99e5b9b9e7e787ce38a85d4adae42bca89b3348ec6c28ce9124874c9a6e",
			"original": "0x0000000000000000000000000000000000000000000000000000000000000004",
			"dirty": "0x0000000000000000000000000000000000000000000000000000000000000005"
		},
		{
			"address": "0x306b1ea3ecdf94ab739f1910bbda052ed4a9f949",
			"key": "0xa73551852fd157f4ce21d0c2c8de1858754a4621698fe8f1b89f6abc59ebaaa6",
			"original": "0x0000000000000000000000000000000000000000000000000000000000000003",
			"dirty": "0x0000000000000000000000000000000000000000000000000000000000000002"
		}
	]
}

"""
        item0 = json.loads(data0) 
        item1 = json.loads(data1) 
        item3 = json.loads(data3) 
        item2 = json.loads(data2) 
        item4 = json.loads(data4) 
        semantically_decoded_tx.state_diff = [item0, item1, item2, item3, item4]

        data_nonce = """
[
	{
		"address": {
			"address": "0xDAFEA492D9c6733ae3d56b7Ed1ADB60692c98Bc5",
			"badge": null,
			"name": null
		},
		"original": "31799",
		"dirty": "31800"
	}
]
"""

        data_balance = """
[
	{
		"address": {
			"address": "0x88f859dB067C45b114897dB6920F3E4A61A5ca66",
			"badge": null,
			"name": null
		},
		"original": "1597689908772199797",
		"dirty": "1593284899473467061",
		"is_miner": false
	},
	{
		"address": {
			"address": "0x88f859dB067C45b114897dB6920F3E4A61A5ca66",
			"badge": null,
			"name": null
		},
		"original": "1165477135605848136",
		"dirty": "1166073127605848136",
		"is_miner": true
	}
]

"""

        semantically_decoded_tx.nonce_diff = json.loads(data_nonce)
        semantically_decoded_tx.balance_diff = json.loads(data_balance)
        return semantically_decoded_tx
