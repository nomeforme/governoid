// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "forge-std/Test.sol";
import "../src/CommitmentContract.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";

contract CommitmentContractTest is Test {
    CommitmentContract public commitmentContract;
    address public tokenAddress = address(0x123);
    uint256 public tokenId = 1;
    address public tokenOwner = address(0x456);

    function setUp() public {
        // Mock the ERC721 token
        vm.mockCall(
            tokenAddress,
            abi.encodeWithSelector(IERC721.ownerOf.selector, tokenId),
            abi.encode(tokenOwner)
        );

        commitmentContract = new CommitmentContract(tokenAddress, tokenId);
    }

    function testExecute() public {
        bytes memory data = abi.encode(1, 2);
        vm.prank(tokenOwner);
        bytes memory result = commitmentContract.execute(data);
        uint256 decodedResult = abi.decode(result, (uint256));
        assertEq(decodedResult, 3);
    }

    function testResolve() public {
        bytes memory data = abi.encode(5, 3);
        bytes memory result = commitmentContract.resolve(data);
        uint256 decodedResult = abi.decode(result, (uint256));
        assertEq(decodedResult, 2);
    }
}
