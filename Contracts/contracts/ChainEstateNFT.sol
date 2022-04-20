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

    // Each NFT will have a unique listing fee that is kept track of in this mapping.
    mapping(uint256 => uint256) public tokenIdToListingFee;

    // Mapping of token ID to address for whitelist spots.
    mapping(uint256 => address) public tokenIdToWhitelistAddress;

    // The property ID for the reflection NFTs.
    uint256 public reflectionId = 1;

    // Array of the reflection token IDs for listing fees.
    uint256[] public reflectionTokenIds;

    constructor(address _marketplaceAddress) ERC721("ChainEstateNFT", "CHESNFT") {
        marketplaceAddress = _marketplaceAddress;
    }

    /**
    * @dev Only owner function to mint a new NFT that's associated with a property.
    * @param tokenURI the token URI on IPFS for the NFT metadata
    * @param propertyId the ID of the property the NFT will be associated with
    * @param listingFee the fee the user pays when putting the NFT for sale on the marketplace
    * @return the ID of the newly minted NFT
     */
    function createToken(string memory tokenURI, uint256 propertyId, uint256 listingFee) public onlyOwner returns (uint) {
        _tokenIds.increment();
        uint256 newItemId = _tokenIds.current();

        _mint(msg.sender, newItemId);
        tokenIdToPropertyId[newItemId] = propertyId;
        tokenIdToListingFee[newItemId] = listingFee;
        _setTokenURI(newItemId, tokenURI);
        approve(address(this), newItemId);
        setApprovalForAll(marketplaceAddress, true);

        if (propertyId == reflectionId) {
            reflectionTokenIds.push(newItemId);
        }

        return newItemId;
    }

    /**
    * @dev Function to get all token URIs for tokens that a given user owns.
    * @param userAddress the user's address to get token URIs of
    * @return list of token URIs for a user's NFTs
     */
    function getUserTokenURIs(address userAddress) public view returns (string[] memory) {
        uint NFTCount = _tokenIds.current();
        uint userNFTCount = 0;
        uint currentIndex = 0;

        for (uint id = 1; id <= NFTCount; id++) {
            if (ownerOf(id) == userAddress) {
                userNFTCount += 1;
            }
        }

        string[] memory userNFTTokenURIs = new string[](userNFTCount);

        for (uint id = 1; id <= NFTCount; id++) {
            if (ownerOf(id) == userAddress) {
                string memory currentNFT = tokenURI(id);
                userNFTTokenURIs[currentIndex] = currentNFT;
                currentIndex += 1;
            }
        }
        
        return userNFTTokenURIs;
    }

    /**
    * @dev Function to get a list of all the reflection NFT IDs.
    * @return list of the reflection NFT IDs
     */
    function getReflectionTokenIds() public view returns (uint256[] memory) {
        return reflectionTokenIds;
    }


    /**
    * @dev Function to assign an NFT to a whitelist spot so only one address can purchase the NFT.
    * @param whiteListAddress the address of the user who will be able to purchase the NFT
    * @param tokenId the ID of the NFT that the whitelist spot is for
     */
    function addWhiteListToToken(address whiteListAddress, uint256 tokenId) public onlyOwner {
        tokenIdToWhitelistAddress[tokenId] = whiteListAddress;
    }

    /**
    * @dev updates the listing fee of an NFT.
    * @param tokenId the ID of the NFT to update the listing fee of
    * @param newListingFee the listing fee value for the NFT
     */
    function updateTokenListingFee(uint256 tokenId, uint256 newListingFee) public onlyOwner {
        tokenIdToListingFee[tokenId] = newListingFee;
    }

    /**
    * @dev updates the property ID of an NFT.
    * @param tokenId the ID of the NFT to update the property ID of
    * @param newPropertyId the property ID value for the NFT
     */
    function updateTokenPropertyId(uint256 tokenId, uint256 newPropertyId) public onlyOwner {
        tokenIdToPropertyId[tokenId] = newPropertyId;
    }

    /**
    * @dev updates the property ID that represents the reflection NFTs
    * @param newReflectionId the new property ID of the reflection NFTs
     */
    function updateReflectionId(uint256 newReflectionId) public onlyOwner {
        reflectionId = newReflectionId;
    }

}