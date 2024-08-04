// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ServiceProviderNFT is ERC721, Ownable {
    uint256 public currentTokenId;

    constructor(address initialOwner)
        ERC721("ServiceProviderNFT", "SPNFT")
        Ownable(initialOwner)
    {}

    function mintTo(address recipient) public onlyOwner returns (uint256) {
        uint256 newTokenId = currentTokenId;
        _safeMint(recipient, newTokenId);
        currentTokenId++;
        return newTokenId;
    }

    function approveTransfer(address to, uint256 tokenId) public {
        require(ownerOf(tokenId) == msg.sender, "Not the owner");
        approve(to, tokenId);
    }

    function transferForEth(uint256 tokenId) external payable {
        require(msg.value > 0, "Must send ETH");
        address owner = ownerOf(tokenId);
        require(getApproved(tokenId) == msg.sender, "Not approved for transfer");

        // Transfer the NFT
        _transfer(owner, msg.sender, tokenId);

        // Transfer the ETH to the owner
        payable(owner).transfer(msg.value);
    }
}
