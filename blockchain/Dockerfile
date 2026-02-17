# =====================================================
# Dockerfile - Hardhat Ethereum Node
# =====================================================
# Builds and runs a local Hardhat network, then deploys
# the smart contracts automatically on startup.
# =====================================================

FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json ./
RUN npm install

# Copy contract source and config
COPY hardhat.config.js ./
COPY contracts/ ./contracts/
COPY scripts/ ./scripts/

# Compile contracts
RUN npx hardhat compile

# Create shared volume mount point
RUN mkdir -p /shared

# Startup script: launch Hardhat node, wait, then deploy
COPY <<'EOF' /app/start.sh
#!/bin/sh
set -e

echo "[hardhat] Starting Hardhat node..."
npx hardhat node --hostname 0.0.0.0 &
HARDHAT_PID=$!

# Wait for the node to be ready
echo "[hardhat] Waiting for node to be ready..."
for i in $(seq 1 30); do
  if wget -q -O /dev/null http://localhost:8545 2>/dev/null; then
    echo "[hardhat] Node is ready!"
    break
  fi
  sleep 1
done

# Deploy contracts
echo "[hardhat] Deploying contracts..."
npx hardhat run scripts/deploy.js --network localhost

echo "[hardhat] Deployment complete. Node running with PID $HARDHAT_PID"
wait $HARDHAT_PID
EOF

RUN chmod +x /app/start.sh

EXPOSE 8545

CMD ["/bin/sh", "/app/start.sh"]
