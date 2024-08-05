from agents.governoid import Governoid

# Example usage
if __name__ == "__main__":
    provider_url = 'http://127.0.0.1:8545'  # Local Anvil node
    erc721_abi_path = 'contracts/out/ServiceProviderNFT.sol/ServiceProviderNFT.json'  # Ensure the path is correct
    commitment_abi_path = 'contracts/out/CommitmentContract.sol/CommitmentContract.json'

    seller_agent_id = 0
    buyer_agent_id = 1

    seller_agent = Governoid(seller_agent_id, 'seller', provider_url, erc721_abi_path, commitment_abi_path)
    print("Seller Agent address: ", seller_agent.account.address)

    buyer_agent = Governoid(buyer_agent_id, 'buyer', provider_url, erc721_abi_path, commitment_abi_path)
    print("Buyer Agent address: ", buyer_agent.account.address)

    seller_agent.deploy_erc721_contract()
    token_id = seller_agent.mint_nft()
    seller_agent.check_token_owner(token_id)

    # Agent peer discovery
    seller_agent.add_agent(buyer_agent)
    buyer_agent.add_agent(seller_agent)

    while True:

        buyer_message = buyer_agent.send_message()
        seller_message = seller_agent.send_message()

        print(f"Buyer Message: {buyer_message}")
        print(f"Seller Message: {seller_message}")

        buyer_tx_decision, buyer_transact_price = buyer_agent.decide_to_transact()
        seller_tx_decision, seller_transact_price = seller_agent.decide_to_transact()

        print(f"Buyer Transaction Decision: {buyer_tx_decision}")
        print(f"Seller Transaction Decision: {seller_tx_decision}")

        if buyer_tx_decision and seller_tx_decision:

            use_transact_price = (buyer_transact_price + seller_transact_price) / 2

            seller_agent.approve_transfer(buyer_agent.account.address, token_id)
            print(f"Seller's NFT with token ID {token_id} approved for transfer to {buyer_agent.account.address}")

            buyer_agent.set_erc721_contract(seller_agent.erc721_contract.address)
            buyer_agent.purchase_nft(token_id, use_transact_price)

            print(f"Buyer's NFT with token ID {token_id} purchased from {seller_agent.account.address} for {use_transact_price} ETH")

            buyer_agent.deploy_commitment_contract(token_id)
            seller_agent.set_commitment_contract(buyer_agent.commitment_contract.address)
            buyer_agent.check_token_owner(token_id)

            result_execute = buyer_agent.call_execute(1, 2)
            print(f"Execute Result: {result_execute}")
            result_resolve = buyer_agent.call_resolve(5, 3)
            print(f"Resolve Result: {result_resolve}")

            break