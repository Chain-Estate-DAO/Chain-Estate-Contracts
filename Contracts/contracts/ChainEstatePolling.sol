// SPDX-License-Identifier: MIT
 
pragma solidity >=0.8.0 <0.9.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import './ChainEstateToken.sol';

/**
 * @title Chain Estate DAO Polling
 * @dev Contract that allows DAO members to vote on properties to purchase through a poll
 */
contract ChainEstatePolling is Ownable {

    // Struct containing all necessary information for a single proposal in a poll.
    struct Proposal {
        string name;
        uint voteCount;
    }

    // Struct containing all necessary information to store past proposals and their results.
    struct PastPoll {
        string title;
        string winningProposal;
        uint numProposals;
        mapping(uint => Proposal) proposals;    // Structs can't have arrays inside of them, so use a mapping like an array.
    }

    // References the deployed Chain Estate token.
    ChainEstateToken public CHES;
 
    // Maps wallet addresses to a bool representing if they already voted in the current poll.
    mapping(address => bool) public voted;

    // List of proposals for the current poll.
    Proposal[] public proposals;

    // The number of polls that have already taken place.
    uint256 public numPastPolls = 0;

    // Mapping that acts as an array to store previous proposal data.
    mapping(uint256 => PastPoll) public pastPolls;

    // The title of the current poll.
    string public currPollTitle;

    // Array of wallet addresses for voters in the current poll.
    address[] public voters;

    // Boolean representing if voting is open for the current poll.
    bool public votingOpen = false;

    // Events for the polling smart contract.
    event PollOpened(string indexed pollTitle, string[] proposalNames);
    event PollClosed(string indexed pollTitle);
    event Vote(address indexed voter, string indexed pollTitle, string indexed proposal, uint numVotes);
 
    // Sets the reference to the contract address for the Chain Estate DAO token with the poll contract is deployed.
    constructor(address CHESTokenAddress) {
        CHES = ChainEstateToken(CHESTokenAddress);
    }
 
    /**
    * @dev Only owner function to create a new poll for the community.
    * @param pollTitle The title of the new poll.
    * @param proposalNames String array containing the names of all proposals for the new poll.
    */
    function createNewPoll(string memory pollTitle, string[] memory proposalNames) public onlyOwner { 
        // All voters have now not voted.
        for (uint256 i = 0; i < voters.length; i++) {
            voted[voters[i]] = false;
        }

        delete voters;
        delete proposals;
 
        // Adds all proposals to the new poll.
        for (uint i = 0; i < proposalNames.length; i++) {
            proposals.push(Proposal({
                name: proposalNames[i],
                voteCount: 0
            }));
        }

        currPollTitle = pollTitle;
        votingOpen = true;

        emit PollOpened(pollTitle, proposalNames);
    }

    /**
    * @dev Only owner function to close the poll and add it to the list of previous polls.
    */
    function closePoll() public onlyOwner {
        require(votingOpen, "There isn't a poll to close currently.");

        votingOpen = false;
        
        string memory currentWinningProposalName = winningProposalName();

        // Creates the PastPoll struct to store the closing poll data.
        PastPoll storage nextPastPoll = pastPolls[numPastPolls++];
        nextPastPoll.title = currPollTitle;
        nextPastPoll.winningProposal = currentWinningProposalName;
        nextPastPoll.numProposals = proposals.length;

        // Adds all closing poll proposals to the PastPoll struct.
        for (uint i = 0; i < proposals.length; i++) {
            nextPastPoll.proposals[i] = Proposal({
                name: proposals[i].name,
                voteCount: proposals[i].voteCount
            });
        }

        emit PollClosed(currPollTitle);
    }

    /**
    * @dev Voting function that allows a user to vote in the current poll.
    * @param proposal The index of the proposal in the poll's proposal array.
    */
    function vote(uint proposal) public {
        require(votingOpen, "There isn't a poll going on currently.");
        require(!voted[msg.sender], "You have already voted in this poll.");
        require(proposal >= 0, "Your proposal number is invalid.");
        require(proposal < proposals.length, "There aren't that many proposals, pick a smaller number.");

        uint256 voterCHESBalance = CHES.balanceOf(msg.sender);
        require(voterCHESBalance > 0, "You need CHES tokens to be able to vote.");
 
        voters.push(msg.sender);
        voted[msg.sender] = true;

        // This might also be updated so that it's one vote per address not one per CHES token the user holds.
        proposals[proposal].voteCount += voterCHESBalance;

        emit Vote(msg.sender, currPollTitle, proposals[proposal].name, voterCHESBalance);
    }
 
    /**
     * @dev Computes the winning proposal taking all previous votes into account.
     * @return winningProposal_ index of winning proposal in the proposals array
     */
    function winningProposal() public view returns (uint winningProposal_) {
        uint winningVoteCount = 0;
        for (uint p = 0; p < proposals.length; p++) {
            if (proposals[p].voteCount > winningVoteCount) {
                winningVoteCount = proposals[p].voteCount;
                winningProposal_ = p;
            }
        }
    }
 
    /**
     * @dev Calls winningProposal() function to get the index of the winner contained in the proposals array and then
     * @return _winningProposalName the name of the winner
    */
    function winningProposalName() public view returns (string memory _winningProposalName) {
        _winningProposalName = proposals[winningProposal()].name;
    }

    /**
     * @dev Gets the number of proposals in the current poll.
     * @return numProposals the number of proposals in the current poll.
    */
    function getNumberOfProposals() public view returns (uint numProposals) {
        return proposals.length;
    }

    /**
     * @dev Gets a single proposal from a previous poll.
     * @param pastPollIndex The index of the previous poll in the pastPolls array.
     * @param proposalIndex The index of the proposal in the previous poll's proposal array.
     * @return proposal the proposal from the previous poll.
    */
    function getPastProposal(uint pastPollIndex, uint proposalIndex) public view returns (Proposal memory proposal) {
        proposal = pastPolls[pastPollIndex].proposals[proposalIndex];
    }
}