// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0 <0.9.0;

import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title Chain Estate DAO NFT Contract
 * @dev NFT contract that will be used with the marketplace contract
 */
contract ChainEstateNFT is ERC721URIStorage, Ownable {
    using Counters for Counters.Counter;

    // Counter to give each NFT a unique ID.
    Counters.Counter public _tokenIds;

    // Address of the Chain Estate DAO NFT marketplace.
    address public marketplaceAddress;

    // Each NFT will be associated with a property through a property ID.
    // This makes it easy to identify NFT holders with the property they will receive rewards from the cash flow of.
    mapping(uint256 => uint256) public tokenIdToPropertyId;

    constructor(address _marketplaceAddress) ERC721("ChainEstateNFT", "CHESNFT") {
        marketplaceAddress = _marketplaceAddress;
    }

    /**
    * @dev Only owner function to mint a new NFT that's associated with a property.
    * @param tokenURI the token URI on IPFS for the NFT metadata
    * @param propertyId the ID of the property the NFT will be associated with
    * @return the ID of the newly minted NFT
     */
    function createToken(string memory tokenURI, uint256 propertyId) public onlyOwner returns (uint) {
        _tokenIds.increment();
        uint256 newItemId = _tokenIds.current();

        _mint(msg.sender, newItemId);
        tokenIdToPropertyId[newItemId] = propertyId;
        _setTokenURI(newItemId, tokenURI);
        approve(address(this), newItemId);
        setApprovalForAll(marketplaceAddress, true);
        return newItemId;
    }
}