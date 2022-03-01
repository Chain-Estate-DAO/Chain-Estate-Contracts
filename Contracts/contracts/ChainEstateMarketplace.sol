// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0 <0.9.0;

import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import './ChainEstateNFT.sol';
import './ChainEstateToken.sol';

/**
 * @title Chain Estate DAO NFT Marketplace Contract
 * @dev NFT marketplace contract that users will interact with on the Chain Estate DAO website
 */
contract ChainEstateMarketplace is ReentrancyGuard, Ownable {
  using Counters for Counters.Counter;

  // Counter to give each marketplace item a unique ID.
  Counters.Counter public _itemIds;

  // Counter to keep track of how many items have been sold on the CHES marketplace.
  Counters.Counter public _itemsSold;

  // The listing fee for any users that want to resell their CHES NFTs.
  uint256 listingPrice = 0.2 ether;

  // Properties of a CHES NFT on the marketplace.
  struct MarketItem {
    uint itemId;
    address nftContract;
    uint256 tokenId;
    address payable seller;
    address payable owner;
    uint256 price;
    bool sold;
  }

  // Maps each NFT's marketplace item ID to all of the properties for the NFT on the marketplace.
  mapping(uint256 => MarketItem) public idToMarketItem;

  // If the NFT contract address ever changes, this mapping keeps track of past NFT contract addresses
  // so that users can still sell NFTs minted with the old contract on the marketplace. If a user tries
  // to sell an NFT from a contract that isn't true in this mapping, it will be rejected.
  mapping (address => bool) public addressToPreviousNFTAddress;

  // Event emitted whenever a CHES NFT is put up for sale on the CHES marketplace.
  event MarketItemCreated (
    uint indexed itemId,
    address indexed nftContract,
    uint256 indexed tokenId,
    address seller,
    address owner,
    uint256 price,
    bool sold
  );

  // References the deployed Chain Estate token.
  ChainEstateToken public CHES;

  // References the deployed Chain Estate NFT contract.
  ChainEstateNFT public CHESNFT;

  constructor(address payable CHESTokenAddress) {
    CHES = ChainEstateToken(CHESTokenAddress);
  }

  /**
  * @dev Gets the listing price for listing an NFT on the marketplace
  * @return the current listing price
  */
  function getListingPrice() public view returns (uint256) {
    return listingPrice;
  }

  /**
  * @dev Only owner function to set the listing price
  * @param newListingPrice the new listing price
  */
  function setListingPrice(uint256 newListingPrice) public onlyOwner {
      listingPrice = newListingPrice;
  }

  /**
  * @dev Only owner function to set the reference to the Chain Estate token (CHES)
  * @param CHESTokenAddress the contract address for the CHES token
  */
  function setChainEstateToken(address payable CHESTokenAddress) public onlyOwner {
      CHES = ChainEstateToken(CHESTokenAddress);
  }

  /**
  * @dev Only owner function to set the reference to the Chain Estate NFT contract
  * @param CHESNFTAddress the address for the CHES NFT contract
  */
  function setChainEstateNFT(address payable CHESNFTAddress) public onlyOwner {
      CHESNFT = ChainEstateNFT(CHESNFTAddress);
      addressToPreviousNFTAddress[CHESNFTAddress] = true;
  }
  
  /**
  * @dev Function to list a CHES NFT on the marketplace
  * @param nftContract contract that the NFT was minted on. Only accepts CHES NFT contract addresses
  * @param tokenId the token ID of the NFT on the NFT contract
  * @param price the price of the token in Chain Estate tokens
  */
  function createMarketItem(
    address nftContract,
    uint256 tokenId,
    uint256 price
  ) public payable nonReentrant {
    require(addressToPreviousNFTAddress[nftContract], "This isn't a valid Chain Estate DAO NFT contract.");
    require(price > 0, "Price must be at least 1 wei");

    if (msg.sender != owner()) {
        require(msg.value == listingPrice, "Price must be equal to listing price");
    }

    _itemIds.increment();
    uint256 itemId = _itemIds.current();
  
    idToMarketItem[itemId] =  MarketItem(
      itemId,
      nftContract,
      tokenId,
      payable(msg.sender),
      payable(address(0)),
      price,
      false
    );

    IERC721(nftContract).transferFrom(msg.sender, address(this), tokenId);

    emit MarketItemCreated(
      itemId,
      nftContract,
      tokenId,
      msg.sender,
      address(0),
      price,
      false
    );
  }

  /**
  * @dev Creates the sale of a marketplace item. Transfers ownership of the NFT and sends funds to the seller
  * @param nftContract contract that the NFT was minted on. Only accepts CHES NFT contract addresses
  * @param itemId the item ID of the NFT on the marketplace
  * @param amountIn the amount of CHES token the user is supplying to purchase the NFT
  */
  function createMarketSale(
    address nftContract,
    uint256 itemId,
    uint256 amountIn
    ) public nonReentrant {
    require(addressToPreviousNFTAddress[nftContract], "This isn't a valid Chain Estate DAO NFT contract.");
    uint price = idToMarketItem[itemId].price;
    uint tokenId = idToMarketItem[itemId].tokenId;
    require(amountIn == price, "Please submit the asking price in order to complete the purchase");

    CHES.transferFrom(msg.sender, idToMarketItem[itemId].seller, amountIn);

    IERC721(nftContract).transferFrom(address(this), msg.sender, tokenId);
    idToMarketItem[itemId].owner = payable(msg.sender);
    idToMarketItem[itemId].sold = true;
    _itemsSold.increment();
    if (idToMarketItem[itemId].seller != owner()) {
        payable(owner()).transfer(listingPrice);
    }
  }

  /**
  * @dev Returns all unsold market items
  * @return the list of market items that haven't been sold
  */
  function fetchMarketItems() public view returns (MarketItem[] memory) {
    uint itemCount = _itemIds.current();
    uint unsoldItemCount = _itemIds.current() - _itemsSold.current();
    uint currentIndex = 0;

    MarketItem[] memory items = new MarketItem[](unsoldItemCount);
    for (uint i = 0; i < itemCount; i++) {
      if (idToMarketItem[i + 1].owner == address(0)) {
        uint currentId = i + 1;
        MarketItem storage currentItem = idToMarketItem[currentId];
        items[currentIndex] = currentItem;
        currentIndex += 1;
      }
    }
    return items;
  }

  /**
  * @dev Returns only items that a user has purchased
  * @return the list of market items the user owners
  */
  function fetchMyNFTs() public view returns (MarketItem[] memory) {
    uint totalItemCount = _itemIds.current();
    uint itemCount = 0;
    uint currentIndex = 0;

    for (uint i = 0; i < totalItemCount; i++) {
      if (idToMarketItem[i + 1].owner == msg.sender) {
        itemCount += 1;
      }
    }

    MarketItem[] memory items = new MarketItem[](itemCount);
    for (uint i = 0; i < totalItemCount; i++) {
      if (idToMarketItem[i + 1].owner == msg.sender) {
        uint currentId = i + 1;
        MarketItem storage currentItem = idToMarketItem[currentId];
        items[currentIndex] = currentItem;
        currentIndex += 1;
      }
    }
    return items;
  }

  /**
  * @dev Returns only items a user has created
  * @return the list of market items the user has put on the market
  */
  function fetchItemsCreated() public view returns (MarketItem[] memory) {
    uint totalItemCount = _itemIds.current();
    uint itemCount = 0;
    uint currentIndex = 0;

    for (uint i = 0; i < totalItemCount; i++) {
      if (idToMarketItem[i + 1].seller == msg.sender) {
        itemCount += 1;
      }
    }

    MarketItem[] memory items = new MarketItem[](itemCount);
    for (uint i = 0; i < totalItemCount; i++) {
      if (idToMarketItem[i + 1].seller == msg.sender) {
        uint currentId = i + 1;
        MarketItem storage currentItem = idToMarketItem[currentId];
        items[currentIndex] = currentItem;
        currentIndex += 1;
      }
    }
    return items;
  }
}