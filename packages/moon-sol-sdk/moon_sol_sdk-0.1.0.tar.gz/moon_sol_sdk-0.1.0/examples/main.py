import moon_sol_sdk_rust  # noqa
import sys

try:
    # 使用默认的公共RPC节点进行测试
    swqos_config = moon_sol_sdk_rust.PySwqosConfig("default", None, None, "https://mainnet.helius-rpc.com/?api-key=be53b701-12a0-4820-9d09-e10862a6d790")
    # swqos_config = moon_sol_sdk.PySwqosConfig(
    #             "jito",
    #             "",
    #             "frankfurt",
    #             "https://frankfurt.mainnet.block-engine.jito.wtf"
    #         )
    priority_fee = moon_sol_sdk_rust.PyPriorityFee(30000000, [0.001], [0.001])  # 降低费用
    trade_config = moon_sol_sdk_rust.PyTradeConfig(
        "https://mainnet.helius-rpc.com/?api-key=be53b701-12a0-4820-9d09-e10862a6d790",
        "confirmed",
        priority_fee,
        [swqos_config]
    )
    
    # 生成一个新的测试钱包（注意：这只是测试用，不包含真实资金）
    print("Creating test client...")
    # 注意：这里需要一个有效的私钥，如果没有请生成一个测试用的
    test_private_key = "41hFntn64KUvrdSXpdmq6DY4p3aRNWNT8JTxj4uxb9ZY9DvFVezxZ9xfaM2V7MmHLx3UqStCmb4McXF4XLsNNQNA"  # 这是一个示例，需要替换为真实密钥
    
    try:
        client = moon_sol_sdk_rust.PySolanaTrade(test_private_key, trade_config)
        print(f"Client created successfully. Wallet: {client.get_public_key()}")
    except Exception as e:
        print(f"Failed to create client: {e}")
        print("Please ensure you have a valid private key")
        sys.exit(1)
    
    # 获取池参数
    print("Fetching pool parameters...")
    try:
        params = moon_sol_sdk_rust.PyPumpSwapParams.from_pool_address(
            "https://mainnet.helius-rpc.com/?api-key=be53b701-12a0-4820-9d09-e10862a6d790",
            "5ryNP5H8ugpMwpGA8pfQ8d4LpFjc33fFYmfTDdn5mHZg"  # 使用一个更常见的池地址
        )
        print("Pool parameters fetched successfully")
    except Exception as e:
        print(f"Failed to fetch pool parameters: {e}")
        # 使用手动配置的参数作为fallback
        print("Using manual pool parameters...")
        params = moon_sol_sdk_rust.PyPumpSwapParams(
            pool="5Ki2npFzPtBPLPersmSgJMuvU787wZjYbJjpNJcHEk82",
            base_mint="So11111111111111111111111111111111111111112",  # WSOL
            quote_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            pool_base_token_account="5Ki2npFzPtBPLPersmSgJMuvU787wZjYbJjpNJcHEk82",
            pool_quote_token_account="5Ki2npFzPtBPLPersmSgJMuvU787wZjYbJjpNJcHEk82",
            pool_base_token_reserves=1000000000,
            pool_quote_token_reserves=1000000000,
            coin_creator_vault_ata="5Ki2npFzPtBPLPersmSgJMuvU787wZjYbJjpNJcHEk82",
            coin_creator_vault_authority="5Ki2npFzPtBPLPersmSgJMuvU787wZjYbJjpNJcHEk82",
            base_token_program="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            quote_token_program="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        )
    
    # 执行交易（使用很小的金额进行测试）
    print("Executing swap...")
    result = moon_sol_sdk_rust.pump_swap(
        action="buy",
        client=client,
        mint_address="HegMoXeaVf8sUsHsqW8KEQtTzwHGZKuK5y8sMSCNpump",  # WSOL
        amount=100000,  # 0.1 SOL in lamports (很小的测试金额)
        slippage_bps=300,  # 3% slippage
        params=params,
        with_tip=True  # 关闭tip以简化测试
    )
    print("Swap result:", result)

except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()