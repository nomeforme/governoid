import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.contract import Contract
from web3.types import TxReceipt
from typing import Any, Dict, List, Union
from dotenv import load_dotenv
import os

load_dotenv()

class Governoid:
    def __init__(self, provider_url: str, erc721_abi_path: str, commitment_abi_path: str):
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        
        # Inject the Geth POA middleware for compatibility with certain networks
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        # Read the private key from the file
        self.private_key: str = os.getenv("AGENT_PRIVATE_KEY")
        
        self.account = self.web3.eth.account.from_key(self.private_key)
        
        self.erc721_abi: List[Dict[str, Any]] = self.load_abi(erc721_abi_path)
        self.erc721_bytecode: str = self.load_bytecode(erc721_abi_path)
        self.commitment_abi: List[Dict[str, Any]] = self.load_abi(commitment_abi_path)
        self.commitment_bytecode: str = self.load_bytecode(commitment_abi_path)
        
        self.erc721_contract: Union[None, Contract] = None
        self.commitment_contract: Union[None, Contract] = None

    def load_abi(self, abi_path: str) -> List[Dict[str, Any]]:
        with open(abi_path, 'r') as abi_file:
            contract_data = json.load(abi_file)
        return contract_data['abi']

    def load_bytecode(self, abi_path: str) -> str:
        with open(abi_path, 'r') as abi_file:
            contract_data = json.load(abi_file)
        return contract_data['bytecode']['object']

    def sign_and_send_transaction(self, tx: Dict[str, Any]) -> TxReceipt:
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.web3.eth.wait_for_transaction_receipt(tx_hash)

    def build_transaction(self, func: Contract, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        tx = func(*args).build_transaction({
            'from': self.account.address,
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
            'gas': 200000,
            'gasPrice': self.web3.to_wei('50', 'gwei'),
            **kwargs
        })
        return tx

    def deploy_contract(self, abi: List[Dict[str, Any]], bytecode: str, constructor_args: List[Any]) -> Contract:
        Contract = self.web3.eth.contract(abi=abi, bytecode=bytecode)
        tx = Contract.constructor(*constructor_args).build_transaction({
            'from': self.account.address,
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
            'gas': 2000000,
            'gasPrice': self.web3.to_wei('50', 'gwei')
        })
        tx_receipt = self.sign_and_send_transaction(tx)
        contract_address = tx_receipt.contractAddress
        contract = self.web3.eth.contract(address=contract_address, abi=abi)
        return contract

    def deploy_erc721_contract(self) -> None:
        self.erc721_contract = self.deploy_contract(self.erc721_abi, self.erc721_bytecode, [self.account.address])
        print(f"ERC721 Contract deployed at address: {self.erc721_contract.address}")

    def mint_nft(self) -> int:
        tx = self.build_transaction(self.erc721_contract.functions.mintTo, self.account.address)
        self.sign_and_send_transaction(tx)
        token_id = self.erc721_contract.functions.currentTokenId().call({'from': self.account.address}) - 1
        print(f"NFT minted with token ID {token_id} to address: {self.account.address}")
        return token_id

    def deploy_commitment_contract(self, token_id: int) -> None:
        self.commitment_contract = self.deploy_contract(
            self.commitment_abi, self.commitment_bytecode, [self.erc721_contract.address, token_id]
        )
        print(f"Commitment Contract deployed at address: {self.commitment_contract.address}")

    def check_token_owner(self, token_id: int) -> str:
        owner = self.erc721_contract.functions.ownerOf(token_id).call({'from': self.account.address})
        print(f"Owner of token ID {token_id}: {owner}")
        return owner

    def call_execute(self, a: int, b: int) -> int:
        data = self.web3.codec.encode(['uint256', 'uint256'], [a, b])
        tx = self.build_transaction(self.commitment_contract.functions.execute, data)
        self.sign_and_send_transaction(tx)
        result_bytes = self.commitment_contract.functions.execute(data).call({'from': self.account.address})
        result = self.web3.codec.decode(['uint256'], result_bytes)[0]
        return result

    def call_resolve(self, a: int, b: int) -> int:
        data = self.web3.codec.encode(['uint256', 'uint256'], [a, b])
        tx = self.build_transaction(self.commitment_contract.functions.resolve, data)
        self.sign_and_send_transaction(tx)
        result_bytes = self.commitment_contract.functions.resolve(data).call({'from': self.account.address})
        result = self.web3.codec.decode(['uint256'], result_bytes)[0]
        return result
