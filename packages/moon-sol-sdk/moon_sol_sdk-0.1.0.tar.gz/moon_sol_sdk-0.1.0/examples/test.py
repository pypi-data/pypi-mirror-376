
from moon_sol_sdk.client import SolClient


sol_client = SolClient(
    private_key="41hFntn64KUvrdSXpdmq6DY4p3aRNWNT8JTxj4uxb9ZY9DvFVezxZ9xfaM2V7MmHLx3UqStCmb4McXF4XLsNNQNA",
    rpc_url="https://mainnet.helius-rpc.com/?api-key=be53b701-12a0-4820-9d09-e10862a6d790",
    commitment="confirmed",
    priority_fee=30000000,
    is_jito=False
)

res = sol_client.pump_swap(
    side="buy",
    pool_address="5ryNP5H8ugpMwpGA8pfQ8d4LpFjc33fFYmfTDdn5mHZg",
    mint_address="HegMoXeaVf8sUsHsqW8KEQtTzwHGZKuK5y8sMSCNpump",  # WSOL
    amount=100000,  # 0.1 SOL in lamports (很小的测试金额)
    slippage=0.03  # 0.3% slippage
)

print(res)