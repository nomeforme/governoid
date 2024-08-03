// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "./ICommitmentContract.sol";

contract CommitmentContract is ICommitmentContract {
    address public tokenAddress;
    IERC721 public tokenContract;
    uint256 public tokenId;

    constructor(address _tokenAddress, uint256 _tokenId) {
        tokenAddress = _tokenAddress;
        tokenContract = IERC721(_tokenAddress);
        tokenId = _tokenId;
    }

    function execute(bytes calldata data) external payable override returns (bytes memory) {
        require(msg.sender == tokenContract.ownerOf(tokenId), "Not the owner");
        // Dummy logic: Add two numbers
        (uint256 a, uint256 b) = abi.decode(data, (uint256, uint256));
        uint256 result = a + b;
        return abi.encode(result);
    }

    function resolve(bytes calldata data) external override returns (bytes memory) {
        // Dummy logic: Subtract two numbers
        (uint256 a, uint256 b) = abi.decode(data, (uint256, uint256));
        uint256 result = a - b;
        // uint256 result = 0;
        return abi.encode(result);
    }
}
