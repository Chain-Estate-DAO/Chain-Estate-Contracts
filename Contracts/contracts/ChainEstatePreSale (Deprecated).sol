// SPDX-License-Identifier: MIT
 
pragma solidity >=0.8.0 <0.9.0;
 
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import './ChainEstateToken.sol';

/**
 * @title Chain Estate Presale
 * @dev Contract responsible for the Chain Estate presale mechanism
 */
contract ChainEstatePreSale is Ownable {

    // References the deployed Chain Estate token.
    ChainEstateToken public CHES;

    // Mapping to determine how much CHES each address has purchased in the presale.
    mapping(address => uint256) public addressToAmountPurchased;

    // The limit for how many CHES tokens each user can purchase during the presale.
    uint256 public purchaseCap = 15000000 * 10 ** 18;

    // 1 BNB can be used to buy this many ChainEstate tokens.
    uint256 public BNBToCHESRate = 52500;
 
    /**
    * @dev Once the CHES token contract is deployed, this function is used to set a reference to that token in this contract.
    * @param CHESTokenAddress address of the ChainEstate token.
     */
    function setToken(address payable CHESTokenAddress) public onlyOwner {
        CHES = ChainEstateToken(CHESTokenAddress);
    }

    /**
    * @dev Gets the amount of CHES the sender owns.
    * @return the CHES balance of the sender
    */
    function getUserBalance() public view returns (uint256) {
        return CHES.balanceOf(msg.sender);
    }
 
     /**
     * @dev Returns the contract address
     * @return contract address
     */
    function getContractAddress() public view returns (address) {
        return address(this);
    }
 
     /**
     * @dev Returns the CHES token address
     * @return CHES token contract address
     */
    function getTokenAddress() public view returns (address) {
        return CHES.getContractAddress();
    }
 
    /**
    * @dev Allows a user to pay BNB for CHES tokens. Conversion rate is 1 BNB to BNBToCHESRate CHES where BNBToCHESRate is the variable defined in the contract.
     */
    function purchaseCHESTokens() public payable {
        // 1 BNB = [BNBToCHESRate] CHES to transfer to msg sender
        uint256 CHESAmount = msg.value * BNBToCHESRate;
        require(addressToAmountPurchased[msg.sender] + CHESAmount <= purchaseCap,  "You cannot purchase this many CHES tokens, that would put you past your presale cap.");
 
        CHES.transfer(msg.sender, CHESAmount);
        addressToAmountPurchased[msg.sender] += CHESAmount;
    }

    /**
    * @dev Only owner function to change the presale CHES token purchase cap per user.
    * @param newPurchaseCap the new CHES token purchase cap in CHES (NOT BNB). Use the conversion rate to figure out how many CHES to set here.
     */
    function changeCHESPurchaseCap(uint256 newPurchaseCap) public onlyOwner {
        purchaseCap = newPurchaseCap;
    }

    /**
    * @dev Only owner function to change the conversion rate for BNB to CHES.
    * @param newConversionRate the new BNB to CHES conversion rate.
     */
    function changeBNBToCHESRate(uint256 newConversionRate) public onlyOwner {
        BNBToCHESRate = newConversionRate;
    }
 
    /**
    * @dev Only owner function to withdraw the BNB from this contract.
    * @param amount the amount of BNB to withdraw from the pre-sale contract.
     */
    function withdrawBNB(uint256 amount) public onlyOwner {
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Failed to send BNB");
    }
 
    /**
    * @dev Gets the amount of BNB that the contract has.
    * @return the amount of BNB the contract has.
     */
    function getContractBNB() public view returns(uint256) {
        return address(this).balance;
    }
 
    /**
    * @dev Gets the CHES token balance of the contract.
    * @return the amount of CHES tokens the contract has.
     */
    function getContractTokens() public view returns(uint256) {
        return CHES.balanceOf(address(this));
    }
}