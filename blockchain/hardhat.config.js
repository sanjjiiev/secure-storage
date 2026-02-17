/**
 * Hardhat Configuration
 * ---------------------
 * Configures the Hardhat development environment for the
 * decentralized file storage smart contracts.
 */

require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
  networks: {
    // Default local Hardhat network
    hardhat: {
      chainId: 31337,
    },
    // Docker-compose Hardhat node
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337,
    },
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
};
