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
}
