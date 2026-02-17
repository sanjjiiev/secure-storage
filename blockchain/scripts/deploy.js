/**
 * deploy.js — Smart Contract Deployment Script
 * ================================================
 * Deploys FileRegistry and StorageProof contracts to the
 * Hardhat local network and writes the contract addresses
 * to a shared JSON file for other services to consume.
 */

const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    console.log("=== Deploying Smart Contracts ===\n");

    const [deployer] = await ethers.getSigners();
    console.log("Deployer address:", deployer.address);
    console.log(
        "Deployer balance:",
        ethers.formatEther(await ethers.provider.getBalance(deployer.address)),
        "ETH\n"
    );

    // ── Deploy FileRegistry ──────────────────────────────
    console.log("Deploying FileRegistry...");
    const FileRegistry = await ethers.getContractFactory("FileRegistry");
    const fileRegistry = await FileRegistry.deploy();
    await fileRegistry.waitForDeployment();
    const fileRegistryAddress = await fileRegistry.getAddress();
    console.log("FileRegistry deployed to:", fileRegistryAddress);

    // ── Deploy StorageProof ──────────────────────────────
    console.log("Deploying StorageProof...");
    const StorageProof = await ethers.getContractFactory("StorageProof");
    const storageProof = await StorageProof.deploy();
    await storageProof.waitForDeployment();
    const storageProofAddress = await storageProof.getAddress();
    console.log("StorageProof deployed to:", storageProofAddress);

    // ── Write addresses to shared config ─────────────────
    const addresses = {
        FileRegistry: fileRegistryAddress,
        StorageProof: storageProofAddress,
        deployer: deployer.address,
        network: "localhost",
        chainId: 31337,
        deployedAt: new Date().toISOString(),
    };

    // Write to /shared (Docker volume) and local artifacts
    const sharedPath = "/shared/contract_addresses.json";
    const localPath = path.join(__dirname, "..", "contract_addresses.json");

    const jsonContent = JSON.stringify(addresses, null, 2);

    // Write to shared volume (available in Docker)
    try {
        fs.writeFileSync(sharedPath, jsonContent);
        console.log(`\nContract addresses written to ${sharedPath}`);
    } catch (e) {
        console.log(`\nCould not write to ${sharedPath} (not in Docker?)`);
    }

    // Always write locally
    fs.writeFileSync(localPath, jsonContent);
    console.log(`Contract addresses written to ${localPath}`);

    console.log("\n=== Deployment Complete ===");
    console.log(JSON.stringify(addresses, null, 2));
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("Deployment failed:", error);
        process.exit(1);
    });
