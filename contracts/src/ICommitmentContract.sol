// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

interface ICommitmentContract {
    function execute(bytes calldata data) external payable returns (bytes memory);
    function resolve(bytes calldata data) external returns (bytes memory);
}
