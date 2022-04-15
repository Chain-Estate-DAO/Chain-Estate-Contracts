// SPDX-License-Identifier: MIT
 
pragma solidity >=0.8.0 <0.9.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import './ChainEstateToken.sol';
import './ChainEstateTokenV1.sol';

/**
 * @title Chain Estate Token Claim Contract for V2 Migration
 * @dev Contract for users to claim their v2 tokens 1 for 1 based on their v1 balance at the time of migration.
 */
contract ChainEstateTokenClaim is Ownable {

    // References the deployed v1 Chain Estate token.
    ChainEstateTokenV1 public CHESV1;

    // References the deployed v2 Chain Estate token.
    ChainEstateToken public CHESV2;

    // Mapping to determine the V1 CHES balance of any address.
    mapping (address => uint256) public balances;

    // Mapping to determine if an address has claimed their v2 CHES tokens yet.
    mapping (address => bool) public claimed;

    // Events for the claim smart contract.
    event TokensClaimed(address indexed user, uint256 claimAmount);
 
    // Sets the reference to the contract addresses for the v1 and v2 Chain Estate DAO token when the token claim contract is deployed.
    constructor(address payable CHESTokenAddressV1, address payable CHESTokenAddressV2) {
        CHESV1 = ChainEstateTokenV1(CHESTokenAddressV1);
        CHESV2 = ChainEstateToken(CHESTokenAddressV2);
    }

    /**
     * @dev Only owner function to set the V1 CHES balance of each investor for the V2 CHES token claims.
     * @param accounts the list of addresses that held the V1 CHES token.
     * @param tokenAmount list of token amounts for each of the V1 CHES holders.
    */
    function setupTokenBalances(address[] calldata accounts, uint256[] calldata tokenAmount) public onlyOwner {
        for(uint256 i = 0; i < accounts.length; i++){
            balances[accounts[i]] = tokenAmount[i];
        }
    }

    /**
     * @dev Function to migrate V1 CHES tokens to V2 CHES.
    */
    function claimV2CHESTokens() public {
        require(claimed[msg.sender] == false, "You already claimed your CHES tokens for the v2 migration.");

        uint256 v1CHESBalance = CHESV1.balanceOf(msg.sender);
        uint256 userClaimAmount = balances[msg.sender];
        require(userClaimAmount <= v1CHESBalance, "You sold at least some of your V1 CHES tokens during the migration process so you cannot migrate to V2.");

        require(CHESV1.allowance(msg.sender, address(this)) >= userClaimAmount, "You must first allow the token claim contract to spend your V1 CHES tokens before you can claim your V2 CHES tokens.");

        claimed[msg.sender] = true;
        CHESV1.transferFrom(msg.sender, address(this), userClaimAmount);
        CHESV2.transfer(msg.sender, userClaimAmount);
        CHESV2.setAirDropInvestTime(msg.sender, CHESV1.airDropInvestTime(msg.sender));
    }

    function setUserClaimedV2CHES(address user, bool hasClaimed) public onlyOwner {
        claimed[user] = hasClaimed;
    }

    function setUserV2CHESBalance(address user, uint256 balance) public onlyOwner {
        balances[user] = balance;
    }

    /**
     * @dev Only owner function to withdraw the remaining V2 CHES tokens after a while if some people didn't claim their V2 CHES tokens.
    */
    function withdrawV2CHESTokens() public onlyOwner {    
        CHESV2.transfer(msg.sender, CHESV2.balanceOf(address(this)));
    }
}