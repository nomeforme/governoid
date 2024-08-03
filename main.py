from agents.governoid import Governoid

# Example usage
if __name__ == "__main__":
    provider_url = 'http://127.0.0.1:8545'  # Local Anvil node
    erc721_abi_path = 'contracts/out/ServiceProviderNFT.sol/ServiceProviderNFT.json'  # Ensure the path is correct
    commitment_abi_path = 'contracts/out/CommitmentContract.sol/CommitmentContract.json'

    agent = Governoid(provider_url, erc721_abi_path, commitment_abi_path)
    print("Agent address: ", agent.account.address)
    agent.deploy_erc721_contract()
    token_id = agent.mint_nft()
    agent.check_token_owner(token_id)
    agent.deploy_commitment_contract(token_id)
    result_execute = agent.call_execute(1, 2)
    print(f"Execute Result: {result_execute}")
    result_resolve = agent.call_resolve(5, 3)
    print(f"Resolve Result: {result_resolve}")