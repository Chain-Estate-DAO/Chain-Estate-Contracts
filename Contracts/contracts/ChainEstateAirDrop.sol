// SPDX-License-Identifier: MIT
 
pragma solidity >=0.8.0 <0.9.0;
 
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import './ChainEstateToken.sol';

/**
 * @title Chain Estate DAO Air Drop
 * @dev Contract responsible for the Chain Estate DAO air drop mechanism
 */
contract ChainEstateAirDrop is Ownable {

    // References the deployed Chain Estate token.
    ChainEstateToken public CHES;

    // Determines if the air drop is active for users to collect rewards.
    bool public airDropActive = false;

    // The minimum amount of CHES a user needs to have invested to receive air drop rewards.
    uint256 public airDropMinimumToInvest = 10000 * 10 ** 18;

    // Initial percentage gained from claiming air drop before invest time calculations.
    uint256 public airDropInitialPercent = 10;

    // How long users have to hold their CHES tokens before they can participate in airdrops.
    uint256 public minimumInvestTime = 14 days;

    // Mapping that determines if each user has already claimed their air drop rewards - resets every new air drop
    mapping(address => bool) public userClaimedAirDrop;

    // List of all users who participated in the air drop - resets every new air drop
    address[] public airDropUsers;

    // Event to emit when someone claims an air drop.
    event AirDropClaimed(address indexed claimAddress, uint256 timeStamp, uint256 amount);
 
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
    * @dev Only owner function to change the minimum amount of CHES a user needs to have to participate in air drops.
    * @param newMinimum the new minimum amount of CHES
     */
    function changeAirDropMinimumToInvest(uint256 newMinimum) public onlyOwner {
        airDropMinimumToInvest = newMinimum;
    }

    /**
    * @dev Only owner function to change the initial percentage gained from air drop rewards before invest time calculation.
    * @param amount the new air drop initial percent reward (percent of user's current holdings).
     */
    function changeAirDropInitialPercent(uint256 amount) public onlyOwner {
        airDropInitialPercent = amount;
    }

    /**
    * @dev Only owner function to change how long users need to hold their CHES tokens before being able to claim airdrop rewards.
    * @param newMinimumTime the new minimum amount of time users need to have held their CHES tokens for.
    * @param convertToDays boolean to determine if the number provided should be treated as a number of days (true) or seconds (false).
     */
    function changeMinimumInvestTime(uint256 newMinimumTime, bool convertToDays) public onlyOwner {
        if (convertToDays) {
            minimumInvestTime = newMinimumTime * 24 * 60 * 60;
        }
        else {
            minimumInvestTime = newMinimumTime;
        }
    }
 
    /**
    * @dev Only owner function to open the air drop so users can claim their rewards.
     */
    function openAirDrop() public onlyOwner {
        airDropActive = true;
 
        for (uint i=0; i< airDropUsers.length ; i++){
            userClaimedAirDrop[airDropUsers[i]] = false;
        }
 
        delete airDropUsers;
    }
 
    /**
    * @dev Only owner function to close the current airdrop.
    * Airdrops by default are never closed, this is just here in case it's needed at some point.
     */
    function closeAirDrop() public onlyOwner {
        require(airDropActive, "There currently isn't an air drop to close.");
        airDropActive = false;
    }

    /**
    * @dev Allows a user to claim their air drop rewards.
    * Sends 10% of user's current balance + more depending how long they have been holding their CHES.
     */
    function claimAirDrop() public {
        address claimAddress = msg.sender;
        require(CHES.balanceOf(claimAddress) >= airDropMinimumToInvest, "You need to have more invested to receive rewards from air drops!");
        require(airDropActive, "The air drop is not currently active. You can claim your air drop rewards when an air drop is ongoing.");
        require(!userClaimedAirDrop[claimAddress], "You've already claimed your rewards from this air drop!");
        require(CHES.airDropInvestTime(claimAddress) > 0, "Your investing time needs to be greater than 0.");
        require(CHES.airDropInvestTime(claimAddress) > CHES.initialTimeStamp(), "Your investing time needs to be greater than the timestamp of the contract deployment.");
 
        // The user's investments can't be too recent or people would be encouraged to buy CHES,
        // claim the air drop, and then sell the CHES for quick profits.
        uint256 currTimeStamp = block.timestamp;
        uint256 userTimeStamp = CHES.airDropInvestTime(claimAddress);
        string memory canClaimRewardsIn = "1";
        if (userTimeStamp + minimumInvestTime >= currTimeStamp && (userTimeStamp + minimumInvestTime - currTimeStamp) / 60 / 60 / 24 > 0) {
            canClaimRewardsIn = Strings.toString((userTimeStamp + minimumInvestTime - currTimeStamp) / 60 / 60 / 24);
        }

        require(userTimeStamp <= currTimeStamp - minimumInvestTime, string(abi.encodePacked("Too many of your recent investments were made to close to the air drop time. You can claim your rewards in ", canClaimRewardsIn, " day(s). The air drop will still be open then.")));

        // Initial percentage gained from claiming air drop.
        uint256 initialAmount = (CHES.balanceOf(claimAddress) / 100) * airDropInitialPercent;

        // Determines how much is added on to initial percentage based length tokens were held.
        // If you invest super early, your rewards approaches 2 * intial percent of your current holdings.
        // If you invest super late (close to the current time), your rewards approaches the initial percent of your current holdings but will be slightly greater.
        uint256 finalAmount = initialAmount + (initialAmount * (1 + (((currTimeStamp - userTimeStamp) * currTimeStamp) / (currTimeStamp - CHES.initialTimeStamp())))) / currTimeStamp;

        // The airdrop needs to have the required funds to give to the user.
        // The airdrop funds will be monitored heavily so this should never prevent airdrop reward claiming.
        require(CHES.balanceOf(address(this)) >= finalAmount, "Air drop doesn't have enough funds for this air drop claim.");

        // Add the user as one of the users who has claimed the air drop.
        airDropUsers.push(claimAddress);
        userClaimedAirDrop[claimAddress] = true;

        // Transfers the CHES tokens to the user claiming them.
        CHES.transfer(claimAddress, finalAmount);

        emit AirDropClaimed(claimAddress, currTimeStamp, finalAmount);
   }
}