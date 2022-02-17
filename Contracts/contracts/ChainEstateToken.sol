// SPDX-License-Identifier: MIT
 
pragma solidity >=0.8.0 <0.9.0;
 
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title Chain Estate DAO Token
 * @dev Main contract for Chain Estate DAO
 */
contract ChainEstateToken is ERC20, Ownable {

    // Mapping to exclude some contracts from fees. Transfers are excluded from fees if address in this mapping is recipient or sender.
    mapping (address => bool) public excludedFromFees;

    // Mapping to determine the timestamp of each address' investment. Earlier average investment = better air drop rewards.
    mapping (address => uint256) public airDropInvestTime;

    // Address of the contract responsible for the air dropping mechanism.
    address public airDropContractAddress;

    // Address of the contract for burning CHES tokens.
    address public burnWalletAddress;

    // Real estate wallet address used to collect funds to purchase real estate.
    address public realEstateWalletAddress;

    // Liquidity wallet address used to hold the 30% of CHES tokens for the liquidity pool.
    // After these coins are moved to the DEX, this address will no longer be used.
    address public liquidityWalletAddress;

    // Marketing wallet address used for funding marketing.
    address public marketingWalletAddress;

    // Developer wallet address used for funding the team.
    address public developerWalletAddress;

    // The initial block timestamp of the token contract.
    uint256 public initialTimeStamp;

    // Real estate transaction fee - deployed at 3%.
    uint256 public realEstateTransactionFeePercent = 3;

    // Developer team transaction fee - deployed at 1%.
    uint256 public developerFeePercent = 1;

    // Marketing transaction fee - deployed at 1%.
    uint256 public marketingFeePercent = 1;

    // Initial token distribution:
    // 35% - Air drop contract
    // 30% - Liquidity pool
    // 20% - Burn
    // 10% - Developer coins (6 month lockup period)
    // 5% - Marketing
    constructor(
        uint256 initialSupply, 
        address _airDropContractAddress, 
        address _burnWalletAddress, 
        address _realEstateWalletAddress, 
        address _liquidityWalletAddress,
        address _marketingWalletAddress,
        address _developerWalletAddress) ERC20("ChainEstateToken", "CHES") {
            initialTimeStamp = block.timestamp;
            airDropContractAddress = _airDropContractAddress;
            realEstateWalletAddress = _realEstateWalletAddress;
            liquidityWalletAddress = _liquidityWalletAddress;
            burnWalletAddress = _burnWalletAddress;
            marketingWalletAddress = _marketingWalletAddress;
            developerWalletAddress = _developerWalletAddress;
            excludedFromFees[realEstateWalletAddress] = true;
            excludedFromFees[developerWalletAddress] = true;
            excludedFromFees[marketingWalletAddress] = true;
            excludedFromFees[liquidityWalletAddress] = true;
            excludedFromFees[airDropContractAddress] = true;    // No transaction fees for claiming air drop rewards
            _mint(airDropContractAddress, (initialSupply) * 35 / 100);
            _mint(liquidityWalletAddress, (initialSupply) * 3 / 10);
            _mint(burnWalletAddress, initialSupply / 5);
            _mint(marketingWalletAddress, initialSupply * 5 / 100);
            _mint(developerWalletAddress, initialSupply / 10);
    }

    /**
     * @dev Returns the contract address
     * @return contract address
     */
    function getContractAddress() public view returns (address){
        return address(this);
    }

    /**
    * @dev Adds a user to be excluded from fees.
    * @param user address of the user to be excluded from fees.
     */
    function excludeUserFromFees(address user) public onlyOwner {
        excludedFromFees[user] = true;
    }

    function getCurrentTimestamp() public view returns (uint256) {
        return block.timestamp;
    }

    /**
    * @dev Removes a user from the fee exclusion.
    * @param user address of the user than will now have to pay transaction fees.
     */
    function includeUsersInFees(address user) public onlyOwner {
        excludedFromFees[user] = false;
    }

    /**
     * @dev Overrides the BEP20 transfer function to include transaction fees.
     * @param recipient the recipient of the transfer
     * @param amount the amount to be transfered
     * @return bool representing if the transfer was successful
     */
    function transfer(address recipient, uint256 amount) public override returns (bool) {
        // If the sender or recipient is excluded from fees, perform the default transfer.
        if (excludedFromFees[_msgSender()] || excludedFromFees[recipient]) {
            _transfer(_msgSender(), recipient, amount);
            return true;
        }

        // Real estate transaction fee.
        uint256 realEstateFee = (amount * realEstateTransactionFeePercent) / 100;
        // Marketing team transaction fee.
        uint256 marketingFee = (amount * marketingFeePercent) / 100;
        // Developer team transaction fee.
        uint256 developerFee = (amount * developerFeePercent) / 100;
 
        // Sends the transaction fees to the respective wallets.
        // These fees could be automatically converted to BNB here in the transfer function
        // using the PancakeSwap router, but that would increase the gas cost a lot for each transfer.
        // Instead, there will be a separate script that runs continuously and converts the real estate/marketing/developer
        // tokens to BNB periodically assuming a set threshold is met upon each execution.
        _transfer(_msgSender(), realEstateWalletAddress, realEstateFee);
        _transfer(_msgSender(), marketingWalletAddress, marketingFee);
        _transfer(_msgSender(), developerWalletAddress, developerFee);
 
        // Sends [initial amount] - [fees] to the recipient
        uint256 valueAfterFees = amount - realEstateFee - marketingFee - developerFee;
        _transfer(_msgSender(), recipient, valueAfterFees);
        return true;
    }

    /**
     * @dev After a token transfer, update the recipient address's air drop invest time since they have a later investment now.
     * @param from the sender's address
     * @param to the recipient's address
     * @param value the amount that was transferred
     */
    function _afterTokenTransfer(address from, address to, uint256 value) internal virtual override {
        uint256 userBalance = balanceOf(to);
        airDropInvestTime[to] = (value * block.timestamp + (userBalance - value) * airDropInvestTime[to]) / userBalance;
        super._afterTokenTransfer(from, to, value);
    }
}