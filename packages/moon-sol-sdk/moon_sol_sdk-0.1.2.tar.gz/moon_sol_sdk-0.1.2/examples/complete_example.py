#!/usr/bin/env python3
"""
Moon Sol SDK - Complete Trading Example
=====================================

This example demonstrates all major features of the Moon Sol SDK:
- Configuration setup
- PumpSwap trading
- Raydium CPMM trading  
- MEV protection
- Error handling
"""

import sys
import os

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from moon_sol_sdk.client import SolClient


def main():
    """Complete example of Moon Sol SDK usage"""
    
    print("🌙 Moon Sol SDK - Complete Trading Example")
    print("=" * 50)
    
    # ========================================
    # 1. Basic Configuration
    # ========================================
    print("📋 Setting up trading client...")
    
    # IMPORTANT: Replace with your actual credentials
    PRIVATE_KEY = "TEST_KEY"  # Use a real private key for actual trading
    RPC_URL = "https://mainnet.helius-rpc.com/?api-key=YOUR_API_KEY"
    
    # Create client with basic configuration
    client = SolClient(
        private_key=PRIVATE_KEY,
        rpc_url=RPC_URL,
        commitment="confirmed",
        priority_fee=30000000,  # 0.03 SOL priority fee
        is_jito=False  # Set to True for MEV protection
    )
    
    print(f"✅ Client created successfully!")
    print(f"📍 Wallet address: {client.get_public_key()}")
    
    # ========================================
    # 2. PumpSwap Trading Example
    # ========================================
    print("\n🎯 PumpSwap Trading Example")
    print("-" * 30)
    
    # Example pool and token addresses (replace with actual ones)
    pump_pool_address = "5ryNP5H8ugpMwpGA8pfQ8d4LpFjc33fFYmfTDdn5mHZg"
    pump_token_mint = "HegMoXeaVf8sUsHsqW8KEQtTzwHGZKuK5y8sMSCNpump"
    
    try:
        print(f"💰 Attempting to buy tokens on PumpSwap...")
        print(f"   Pool: {pump_pool_address}")
        print(f"   Token: {pump_token_mint}")
        print(f"   Amount: 0.0001 SOL (100,000 lamports)")
        
        result = client.pump_swap(
            side="buy",
            pool_address=pump_pool_address,
            mint_address=pump_token_mint,
            amount=100000,  # 0.0001 SOL in lamports (small test amount)
            slippage=0.01   # 1% slippage
        )
        
        print(f"✅ PumpSwap buy result: {result}")
        
    except Exception as e:
        print(f"❌ PumpSwap buy failed: {e}")
    
    # ========================================
    # 3. Raydium CPMM Trading Example
    # ========================================
    print("\n🌊 Raydium CPMM Trading Example")
    print("-" * 35)
    
    # Example Raydium CPMM pool (replace with actual pool address)
    raydium_pool_address = "EXAMPLE_RAYDIUM_POOL_ADDRESS"
    raydium_token_mint = "EXAMPLE_TOKEN_MINT_ADDRESS"
    
    try:
        print(f"💰 Attempting to buy tokens on Raydium CPMM...")
        print(f"   Pool: {raydium_pool_address}")
        print(f"   Token: {raydium_token_mint}")
        print(f"   Amount: 0.0001 SOL (100,000 lamports)")
        
        # Note: This will fail with example addresses
        result = client.raydium_cpmm_swap(
            side="buy",
            pool_address=raydium_pool_address,
            mint_address=raydium_token_mint,
            amount=100000,  # 0.0001 SOL in lamports
            slippage=0.005  # 0.5% slippage
        )
        
        print(f"✅ Raydium CPMM buy result: {result}")
        
    except Exception as e:
        print(f"❌ Raydium CPMM buy failed: {e}")
        print("   (This is expected with example addresses)")
    
    # ========================================
    # 4. Advanced Configuration Example
    # ========================================
    print("\n⚙️ Advanced Configuration Example")
    print("-" * 40)
    
    print("🛡️ Creating client with MEV protection (Jito)...")
    
    # Client with MEV protection
    jito_client = SolClient(
        private_key=PRIVATE_KEY,
        rpc_url=RPC_URL,
        commitment="confirmed",
        priority_fee=50000000,  # Higher priority fee for MEV protection
        is_jito=True  # Enable Jito MEV protection
    )
    
    print(f"✅ MEV-protected client created!")
    print(f"📍 Wallet address: {jito_client.get_public_key()}")
    
    # ========================================
    # 5. Best Practices and Tips
    # ========================================
    print("\n💡 Best Practices and Tips")
    print("-" * 30)
    
    tips = [
        "🔐 Never commit private keys to version control",
        "🧪 Always test with small amounts first",
        "🛡️ Use MEV protection for production trading",
        "📊 Monitor slippage and adjust as needed",
        "⚡ Use appropriate priority fees for network conditions",
        "🔍 Verify all addresses before trading",
        "📈 Consider implementing proper position sizing",
        "🚨 Implement proper error handling and logging"
    ]
    
    for tip in tips:
        print(f"   {tip}")
    
    print("\n✅ Example completed successfully!")
    print("📚 Check the README.md for more detailed documentation.")


if __name__ == "__main__":
    main()
