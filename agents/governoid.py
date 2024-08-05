import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.contract import Contract
from web3.types import TxReceipt
from typing import Any, Dict, List, Union
from dotenv import load_dotenv
import os

from agents.lib.think import think_litellm

load_dotenv()

class Governoid:
    def __init__(
        self,
        agent_id: int,
        agent_role: str,
        provider_url: str,
        erc721_abi_path: str,
        commitment_abi_path: str
    ) -> None:
        
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.agent_name = agent_role + "_" + str(agent_id)
        
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        
        # Inject the Geth POA middleware for compatibility with certain networks
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        # Read the private key from the file
        self.private_key: str = os.getenv("AGENT_PRIVATE_KEY_"+str(agent_id))
        
        self.account = self.web3.eth.account.from_key(self.private_key)
        
        self.erc721_abi: List[Dict[str, Any]] = self.load_abi(erc721_abi_path)
        self.erc721_bytecode: str = self.load_bytecode(erc721_abi_path)
        self.commitment_abi: List[Dict[str, Any]] = self.load_abi(commitment_abi_path)
        self.commitment_bytecode: str = self.load_bytecode(commitment_abi_path)
        
        self.erc721_contract: Union[None, Contract] = None
        self.commitment_contract: Union[None, Contract] = None

        # LLM stuff
        self.system_message = ""

        if self.agent_role == "seller":
        
            self.system_message = f"""You are roleplaying as agent with id and role: {self.agent_name}. You can sell
            an NFT which enables the buyer agent to perform a service for you. Based on the message 
            history between yourself and other agents, discuss with the buyer agents regarding selling the NFT.
            Try to get the buyer agent to agree to the transaction, but do not give in too easily.
            Your ideal sale price is of 1 ETH. Quote the buyer agent a price appropriate to the discussions being had.
            Keep your responses to a maximum of 150 words!!!
            """

        if self.agent_role == "buyer":

            self.system_message = f"""You are roleplaying as agent with id and role: {self.agent_name}. You can buy
            an NFT which enables you to perform a service for the seller agent. Based on the message 
            history between yourself and other agents, discuss with the seller agents regarding purchasing the NFT.
            Try to get the seller agent to agree to the transaction, but do not give in too easily.
            Your ideal purchase price is of 0.5 ETH. Quote the seller agent a price appropriate to the discussions being had.
            Keep your responses to a maximum of 150 words!!!
            """

        self.tx_system_message = f"""You are roleplaying as agent with id and role: {self.agent_name} Based on the message 
        history between yourself and other agents, respond with TRUE_<agreed_price (float)> (e.g. TRUE_<1.0>) if you believe a transaction should occur 
        at the agreed price or FALSE_<0> if you believe a transaction should not occur.
        Your only output MUST be either TRUE_<agreed_price> (including angle brackets <,>) or FALSE_<0>!!!
        """

        self.prefix = ""
        self.use_streaming = False
        # self.think_module = None

        self.message_history = []
        self.known_agents = []


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

    def set_erc721_contract(self, contract_address: str) -> None:
        self.erc721_contract = self.web3.eth.contract(address=contract_address, abi=self.erc721_abi)

    def set_commitment_contract(self, contract_address: str) -> None:
        self.commitment_contract = self.web3.eth.contract(address=contract_address, abi=self.commitment_abi)

    def mint_nft(self) -> int:
        tx = self.build_transaction(self.erc721_contract.functions.mintTo, self.account.address)
        self.sign_and_send_transaction(tx)
        token_id = self.erc721_contract.functions.currentTokenId().call({'from': self.account.address}) - 1
        print(f"NFT minted with token ID {token_id} to address: {self.account.address}")
        return token_id
    
    def approve_transfer(self, buyer_address: str, token_id: int) -> None:
        tx = self.build_transaction(self.erc721_contract.functions.approveTransfer, buyer_address, token_id)
        self.sign_and_send_transaction(tx)
        print(f"Approved transfer of token ID {token_id} to {buyer_address}")


    def purchase_nft(self, token_id: int, eth_amount: float) -> None:
        tx = self.build_transaction(
            self.erc721_contract.functions.transferForEth,
            token_id,
            value=self.web3.to_wei(eth_amount, 'ether')
        )
        self.sign_and_send_transaction(tx)
        print(f"Purchased token ID {token_id} for {eth_amount} ETH")

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
    

    # LLM Stuff
    def send_message(self) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
        """

        self.message_history = self.clip_history(self.message_history, n_messages=5)

        use_content = "\n".join(self.message_history + [self.prefix])
        # print("use_content:", use_content)

        message = think_litellm(
            self.system_message,
            use_content,
            self.use_streaming,
        )

        for agent in self.known_agents:
            agent.receive_message(agent.agent_name, message)

        return message
    
    def receive_message(self, agent_name: str, message: str) -> None:

        """
        Concatenates {message} spoken by {name} into message history
        """
        self.message_history.append(f"{agent_name}: {message}")

    def decide_to_transact(self) -> str:
        
        use_content = "\n".join(self.message_history + [self.prefix])
        # print("use_content:", use_content)

        transact_output = think_litellm(
            self.tx_system_message,
            use_content,
            self.use_streaming,
        )

        print(f"{self.agent_name} Transaction Decision: {transact_output}")

        transact_decision = transact_output.split("_")[0]
        transact_price = float(transact_output.split("_")[1].strip("<").strip(">"))

        if transact_decision == "TRUE":
            return (True, transact_price)
        else:
            return (False, 0)
    
    def clip_history(self, lst, n_messages=5):
        """
        Clips the history to the last n messages
        """
        if len(lst) == 0:
            return []  # Return an empty list if the input list is empty
        
        return [lst[0]] + lst[-n_messages:] if len(lst) > n_messages else lst
    
    def reset_history(self):
        self.message_history = []

    def add_agent(self, agent):
        if agent.agent_name not in [agent.agent_name for agent in self.known_agents]:
            self.known_agents.append(agent)