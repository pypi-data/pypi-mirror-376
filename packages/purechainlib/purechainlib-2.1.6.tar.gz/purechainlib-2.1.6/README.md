<div align="left">
  
  # PureChain Python Library

  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Version](https://img.shields.io/badge/version-2.1.4-green)](https://pypi.org/project/purechainlib/)

  **Zero Gas Cost Blockchain Development in Python**

  Python SDK for PureChain EVM network with **completely FREE transactions**. Deploy contracts, send tokens, and interact with smart contracts without any gas fees!
  
  ## 📖 Korean Documentation / 한국어 문서
  
  Korean documentation is included in this package. After installation, you can find `README_ko.md` in your package directory.
  
  한국어 문서가 패키지에 포함되어 있습니다. 설치 후 패키지 디렉토리에서 `README_ko.md` 파일을 찾을 수 있습니다.
  
  ```python
  # How to access Korean README after installation:
  import purechainlib
  import os
  korean_readme_path = os.path.join(os.path.dirname(purechainlib.__file__), '..', 'README_ko.md')
  print(f"Korean README location: {korean_readme_path}")
  ```
</div>

## 🆕 What's New in v2.1.4

### Performance Improvements
- Significantly improved dependency resolution speed
- Fixed eth-abi and parsimonious compatibility issues
- Made mythril optional to avoid dependency conflicts

### Bug Fixes (v2.1.1-2.1.3)
- Fixed security audit results display issue
- Resolved dependency version conflicts

## Previous Updates (v2.1.0)

### 🔒 Smart Contract Security Auditing
- **Built-in security tools** - Slither bundled, Mythril optional
- **Auto-installation** - Tools install automatically on first use
- **One-liner audits** - `await pcl.audit("contract code")`
- **Multiple tools** - Choose Slither, Mythril (if installed), or run ALL
- **Comprehensive logging** - Perfect for LLM integration
- **Export reports** - JSON, Markdown, HTML formats
- **Note**: Mythril can be installed separately with `pip install mythril==0.24.8`

### 📚 Documentation Updates
- Removed private GitHub repository links
- Improved Korean documentation access instructions
- Package now fully self-contained with both English and Korean docs
<!-- - Added comprehensive help system (hint: try `pc.help.` and explore!) -->

## Previous Updates

### v2.0.8 - Korean Language Support
- Complete Korean documentation now available
- Korean README included in the package (README_ko.md)
- Optimized examples for Korean developers

### v2.0.7

### 🌱 Carbon Footprint Tracking
- **Scientific measurements** of energy consumption (Joules) and CO2 emissions
- **ESG compliance** reporting for environmental impact
- **Regional grid intensity** support (US, EU, Asia, etc.)
- Compare efficiency with other blockchains (99.99999% less CO2 than Ethereum!)

### 🔧 Automatic Web3 Middleware
- No more manual `web3.middleware` imports needed
- Automatic compatibility with all Web3 versions
- Just `from purechainlib import PureChain` and you're ready!

### 📊 Energy Measurements
- **0.029 Joules** per transaction (scientifically measured)
- **63 billion times** more efficient than Bitcoin
- Based on actual CPU power monitoring, not estimates

<!-- [See full carbon tracking documentation](#-carbon-footprint-tracking) -->

## 🚀 Quick Start

```bash
pip install purechainlib
```

**Note:** Version 2.1.4+ has optimized dependencies for fast installation. Security tools like Mythril can be installed separately if needed.

```python
import asyncio
from purechainlib import PureChain
# No need for web3.middleware imports - handled automatically!

async def main():
    # Initialize PureChain
    pc = PureChain('testnet')
    
    # Connect your wallet
    pc.connect('your_private_key_here')
    
    # Check balance (FREE!)
    balance = await pc.balance()
    print(f"Balance: {balance} PURE")
    
    # Deploy a contract (FREE!)
    contract_source = """
    pragma solidity ^0.8.19;
    contract Hello {
        string public message = "Hello PureChain!";
        function setMessage(string memory _msg) public {
            message = _msg;
        }
    }
    """
    
    factory = await pc.contract(contract_source)
    contract = await factory.deploy()  # No gas fees!
    print(f"Contract deployed: {contract.address}")

asyncio.run(main())
```

## ✨ Features

- **Zero Gas Costs** - All operations are completely FREE
- **Security Auditing** - Built-in smart contract vulnerability scanning
- **Easy to Use** - Simple, intuitive API
- **Full EVM Support** - Deploy any Solidity contract
- **Pythonic** - Clean, readable Python code
- **Secure** - Industry-standard cryptography
- **Complete** - Account management, compilation, deployment, auditing

## 📚 Quick Reference

### All Available Functions

| Function | Description | Example |
|----------|-------------|---------|
| `PureChain(network, private_key?)` | Initialize connection | `pc = PureChain('testnet')` |
| `connect(private_key)` | Connect wallet | `pc.connect('your_private_key')` |
| `account()` | Create new account | `acc = pc.account()` |
| `balance(address?)` | Get balance | `bal = await pc.balance()` |
| `bal(address?)` | Get balance (short) | `bal = await pc.bal()` |
| `send(to, value?)` | Send PURE tokens | `await pc.send('0x...', '1.0')` |
| `contract(source)` | Compile contract | `factory = await pc.contract(code)` |
| `factory.deploy(*args)` | Deploy contract | `contract = await factory.deploy()` |
| `call(contract, method, *args)` | Read from contract | `result = await pc.call(contract, 'balances', addr)` |
| `execute(contract, method, *args)` | Write to contract | `await pc.execute(contract, 'mint', 1000)` |
| `block(number?)` | Get block info | `block = await pc.block()` |
| `transaction(hash)` | Get transaction | `tx = await pc.transaction('0x...')` |
| `gasPrice()` | Get gas price (always 0) | `price = await pc.gasPrice()` |
| `address(addr?)` | Get address info | `info = await pc.address()` |
| `isContract(address)` | Check if contract | `is_contract = await pc.isContract('0x...')` |
| `events(contract, blocks?)` | Get contract events | `events = await pc.events(addr, 10)` |
| `status()` | Get network status | `status = await pc.status()` |
| `tx(hash?)` | Get transaction (alias) | `tx = await pc.tx('0x...')` |
| `testTPS(duration?, target?, mode?)` | Test TPS performance | `results = await pc.testTPS(30, 100, 'full')` |
| `measureLatency(operations?)` | Measure operation latency | `latency = await pc.measureLatency(100)` |
| `benchmarkThroughput(duration?)` | Test blockchain throughput (TPS) | `throughput = await pc.benchmarkThroughput(60)` |
| `runPerformanceTest(quick?)` | Full performance suite | `results = await pc.runPerformanceTest()` |
| `enableCarbonTracking(region?)` | Enable carbon footprint tracking | `pc.enableCarbonTracking('us')` |
| `disableCarbonTracking()` | Disable carbon tracking | `pc.disableCarbonTracking()` |
| `getCarbonReport()` | Get carbon emissions report | `report = await pc.getCarbonReport()` |
| `getCarbonESGMetrics()` | Get ESG compliance metrics | `esg = await pc.getCarbonESGMetrics()` |
| `exportCarbonReport()` | Export full carbon report as JSON | `json_report = await pc.exportCarbonReport()` |
| **SECURITY AUDITING** | | |
| `audit(contract, **kwargs)` | One-liner security audit | `await pc.audit(code)` |
| `auditContract(contract, tool?)` | Full security audit | `await pc.auditContract(code, tool=SecurityTool.SLITHER)` |
| `auditAndDeploy(contract, ...)` | Audit then deploy if safe | `await pc.auditAndDeploy(code, require_pass=True)` |
| `runSecurityLoop(contract, max?)` | Iterative security fixing | `await pc.runSecurityLoop(code, max_iterations=5)` |
| `enableAutoAudit(tool?)` | Auto-audit before deployments | `pc.enableAutoAudit()` |
| `checkSecurityTools()` | Check installed tools | `pc.checkSecurityTools()` |
| `getSecurityLogs()` | Get all audit logs | `logs = pc.getSecurityLogs()` |

### Function Categories

#### 🔐 **Account & Wallet Management**
```python
# Initialize and connect
pc = PureChain('testnet', 'optional_private_key')
pc.connect('your_private_key_without_0x')

# Create new account
new_account = pc.account()
# Returns: {'address': '0x...', 'privateKey': '...'}

# Get current signer address
address = pc.signer.address
```

#### 💰 **Balance & Transactions**
```python
# Check balances
my_balance = await pc.balance()           # Your balance
other_balance = await pc.balance('0x...')  # Specific address
quick_balance = await pc.bal()            # Shorthand

# Send PURE tokens (FREE!)
await pc.send('0x...recipient', '10.5')

# Send with transaction object
await pc.send({
    'to': '0x...address',
    'value': '1.0',
    'data': '0x...'  # Optional
})
```

#### 📄 **Smart Contracts**
```python
# Compile and deploy
contract_source = "pragma solidity ^0.8.19; contract Test { ... }"
factory = await pc.contract(contract_source)
deployed_contract = await factory.deploy(constructor_args)

# Attach to existing contract
existing_contract = factory.attach('0x...contract_address')

# Read from contract (view functions)
result = await pc.call(contract, 'balances', user_address)
name = await pc.call(contract, 'name')  # No arguments

# Write to contract (transaction functions)
await pc.execute(contract, 'mint', recipient, 1000)
await pc.execute(contract, 'setMessage', "Hello World")
```

#### 🔍 **Blockchain Information**
```python
# Block information
latest_block = await pc.block()           # Latest block
specific_block = await pc.block(12345)    # Specific block number

# Transaction information
tx_info = await pc.transaction('0x...hash')
tx_alias = await pc.tx('0x...hash')      # Same as above

# Address information
addr_info = await pc.address()           # Your address info
other_info = await pc.address('0x...')   # Specific address
# Returns: {'balance': '...', 'isContract': bool, 'address': '...'}

# Check if address is contract
is_contract = await pc.isContract('0x...address')

# Gas price (always 0 on PureChain)
gas_price = await pc.gasPrice()  # Returns 0

# Network status
status = await pc.status()
# Returns: {'chainId': 900520900520, 'gasPrice': 0, 'blockNumber': ...}
```

#### 📊 **Events & Monitoring**
```python
# Get contract events
events = await pc.events(contract_address)      # All events
recent_events = await pc.events(contract_address, 10)  # Last 10 blocks
```

#### ⚡ **Performance Testing**
```python
# Test Transactions Per Second (TPS) with different measurement modes
# Mode options: 'full' (default), 'send', 'parallel'
tps_full = await pc.testTPS(duration=30, target_tps=100, measure_mode='full')  # Measure full lifecycle
tps_send = await pc.testTPS(duration=30, target_tps=100, measure_mode='send')  # Measure send time only
tps_parallel = await pc.testTPS(duration=30, target_tps=100, measure_mode='parallel')  # Parallel execution

print(f"Full Mode TPS: {tps_full['actual_tps']}")
print(f"Send-only TPS: {tps_send['actual_tps']}")
print(f"Parallel TPS: {tps_parallel['actual_tps']}")

# Measure operation latency
latency_results = await pc.measureLatency(operations=100)
print(f"Average latency: {latency_results['balance_check']['avg_ms']}ms")

# Benchmark blockchain throughput (mixed operations TPS)
throughput_results = await pc.benchmarkThroughput(test_duration=60)
print(f"Throughput: {throughput_results['throughput_tps']} TPS")

# Run complete performance suite
performance = await pc.runPerformanceTest(quick=True)  # Quick test
full_performance = await pc.runPerformanceTest(quick=False)  # Full test
```

## 📚 Detailed API Reference

### Initialization

```python
from purechainlib import PureChain

# Connect to testnet (default)
pc = PureChain('testnet')

# Or mainnet
pc = PureChain('mainnet')

# Connect with private key immediately
pc = PureChain('testnet', 'your_private_key')
```

### Account Management

```python
# Connect wallet
pc.connect('your_private_key_without_0x_prefix')

# Create new account
account = pc.account()
print(f"Address: {account['address']}")
print(f"Private Key: {account['privateKey']}")

# Check balance
balance = await pc.balance()  # Your balance
balance = await pc.balance('0x...address')  # Specific address
```

### Contract Operations

```python
# Deploy contract from source
contract_source = """
pragma solidity ^0.8.19;
contract Token {
    mapping(address => uint256) public balances;
    
    function mint(uint256 amount) public {
        balances[msg.sender] += amount;
    }
}
"""

# Compile and deploy (FREE!)
factory = await pc.contract(contract_source)
contract = await factory.deploy()

# Read from contract (FREE!)
balance = await pc.call(contract, 'balances', user_address)

# Write to contract (FREE!)
await pc.execute(contract, 'mint', 1000)
```

### Transactions

```python
# Send PURE tokens (FREE!)
await pc.send('0x...recipient_address', '10.5')

# Send with transaction object
await pc.send({
    'to': '0x...address',
    'value': '1.0',
    'data': '0x...'  # Optional contract data
})
```

### Blockchain Information

```python
# Get latest block
block = await pc.block()
print(f"Block #{block['number']}")

# Get transaction info
tx = await pc.transaction('0x...transaction_hash')

# Network status
status = await pc.status()
print(f"Chain ID: {status['chainId']}")
print(f"Gas Price: {status['gasPrice']}") # Always 0!

# Gas price (always returns 0)
gas_price = await pc.gasPrice()
```

### Pythonic Shortcuts

```python
# Quick balance check
balance = await pc.bal()

# Address information
info = await pc.address()
print(f"Balance: {info['balance']}")
print(f"Is Contract: {info['isContract']}")

# Check if address is a contract
is_contract = await pc.isContract('0x...address')
```

## 📝 Complete Examples

### Deploy and Interact with Token Contract

```python
import asyncio
from purechainlib import PureChain

async def token_example():
    pc = PureChain('testnet')
    pc.connect('your_private_key')
    
    # Token contract
    token_source = """
    pragma solidity ^0.8.19;
    
    contract SimpleToken {
        mapping(address => uint256) public balances;
        uint256 public totalSupply;
        string public name = "PureToken";
        
        function mint(address to, uint256 amount) public {
            balances[to] += amount;
            totalSupply += amount;
        }
        
        function transfer(address to, uint256 amount) public {
            require(balances[msg.sender] >= amount);
            balances[msg.sender] -= amount;
            balances[to] += amount;
        }
    }
    """
    
    # Deploy token (FREE!)
    factory = await pc.contract(token_source)
    token = await factory.deploy()
    print(f"Token deployed at: {token.address}")
    
    # Mint tokens (FREE!)
    await pc.execute(token, 'mint', pc.signer.address, 1000000)
    
    # Check balance (FREE!)
    balance = await pc.call(token, 'balances', pc.signer.address)
    print(f"Token balance: {balance}")
    
    # Transfer tokens (FREE!)
    recipient = "0xc8bfbC0C75C0111f7cAdB1DF4E0BC3bC45078f9d"
    await pc.execute(token, 'transfer', recipient, 100)
    print("Tokens transferred!")

asyncio.run(token_example())
```

### Create and Fund Multiple Accounts

```python
import asyncio
from purechainlib import PureChain

async def multi_account_example():
    pc = PureChain('testnet')
    pc.connect('your_private_key')
    
    # Create 3 new accounts
    accounts = []
    for i in range(3):
        account = pc.account()
        accounts.append(account)
        print(f"Account {i+1}: {account['address']}")
    
    # Fund each account (FREE transactions!)
    for i, account in enumerate(accounts):
        await pc.send(account['address'], f"{i+1}.0")  # Send 1, 2, 3 PURE
        print(f"Sent {i+1} PURE to account {i+1}")
    
    # Check all balances
    for i, account in enumerate(accounts):
        balance = await pc.balance(account['address'])
        print(f"Account {i+1} balance: {balance} PURE")

asyncio.run(multi_account_example())
```

### Contract Event Monitoring

```python
import asyncio
from purechainlib import PureChain

async def event_example():
    pc = PureChain('testnet')
    pc.connect('your_private_key')
    
    # Contract with events
    contract_source = """
    pragma solidity ^0.8.19;
    
    contract EventExample {
        event MessageSet(address indexed user, string message);
        
        string public message;
        
        function setMessage(string memory _message) public {
            message = _message;
            emit MessageSet(msg.sender, _message);
        }
    }
    """
    
    # Deploy and interact
    factory = await pc.contract(contract_source)
    contract = await factory.deploy()
    
    # Set message (creates event)
    await pc.execute(contract, 'setMessage', "Hello Events!")
    
    # Get events from last 10 blocks
    events = await pc.events(contract.address, 10)
    print(f"Found {len(events)} events")

asyncio.run(event_example())
```

### Performance Testing & Benchmarking

```python
import asyncio
from purechainlib import PureChain

async def performance_testing():
    pc = PureChain('testnet')
    pc.connect('your_private_key')
    
    print("🚀 Starting Performance Tests...")
    
    # 1. TPS (Transactions Per Second) Test
    print("\n1️⃣ TPS Test - Measure transaction throughput")
    tps_results = await pc.testTPS(duration=30, target_tps=50)
    
    print(f"Target TPS: {tps_results['target_tps']}")
    print(f"Achieved TPS: {tps_results['actual_tps']}")
    print(f"Efficiency: {tps_results['efficiency']}%")
    print(f"Average Latency: {tps_results['avg_latency_ms']}ms")
    
    # 2. Latency Test - Measure operation response times
    print(f"\n2️⃣ Latency Test - Measure response times")
    latency_results = await pc.measureLatency(operations=50)
    
    for operation, stats in latency_results.items():
        print(f"{operation}: {stats['avg_ms']}ms (min: {stats['min_ms']}, max: {stats['max_ms']})")
    
    # 3. Throughput Test - Measure data transfer rates
    print(f"\n3️⃣ Throughput Test - Measure data transfer")
    throughput_results = await pc.benchmarkThroughput(test_duration=45)
    
    print(f"Total TPS: {throughput_results['throughput_tps']}")
    print(f"Data Transfer: {throughput_results['kb_per_second']} KB/s")
    print(f"Success Rate: {throughput_results['success_rate']}%")
    
    # 4. Complete Performance Suite
    print(f"\n4️⃣ Complete Performance Suite")
    full_results = await pc.runPerformanceTest(quick=False)
    
    print(f"📊 Performance Summary:")
    print(f"Network: {full_results['network']['networkName']}")
    print(f"Block: #{full_results['network']['blockNumber']}")
    print(f"Latency: {full_results['latency']['balance_check']['avg_ms']}ms")
    print(f"TPS: {full_results['tps']['actual_tps']}")
    print(f"Throughput: {full_results['throughput']['throughput_tps']} TPS")

asyncio.run(performance_testing())
```

### Quick Performance Check

```python
import asyncio
from purechainlib import PureChain

async def quick_performance_check():
    pc = PureChain('testnet')
    pc.connect('your_private_key')
    
    # Quick 15-second test suite
    results = await pc.runPerformanceTest(quick=True)
    
    print("⚡ Quick Performance Results:")
    print(f"TPS: {results['tps']['actual_tps']}")
    print(f"Latency: {results['latency']['balance_check']['avg_ms']}ms")
    print(f"Throughput: {results['throughput']['throughput_tps']} TPS")

asyncio.run(quick_performance_check())
```

## 🌐 Network Information

| Network | RPC URL | Chain ID | Gas Price |
|---------|---------|----------|-----------|
| **Testnet** | `https://purechainnode.com:8547` | `900520900520` | `0` (FREE!) |
| **Mainnet** | `https://purechainnode.com:8547` | `900520900520` | `0` (FREE!) |

## ⚡ Performance Metrics Guide

### Understanding Performance Results

When you run performance tests, here's what each metric means:

#### 🚀 **TPS (Transactions Per Second)**
- **Target TPS**: The rate you want to achieve
- **Actual TPS**: The rate PureChain actually delivered
- **Efficiency**: How close you got to your target (%)
- **Measurement Modes**:
  - **`full`**: Measures complete transaction lifecycle (send + wait for confirmation)
  - **`send`**: Measures only sending time (doesn't wait for confirmation)
  - **`parallel`**: Sends transactions concurrently and measures both phases

**Timing Breakdown:**
- **Send Time**: Time to build, sign, and broadcast transaction to network
- **Confirmation Time**: Time from broadcast to mining/confirmation
- **Total Latency**: Send Time + Confirmation Time

```python
# Example TPS results
{
    'duration': 30.0,
    'successful_transactions': 1487,
    'failed_transactions': 0,
    'actual_tps': 49.57,
    'target_tps': 50,
    'efficiency': 99.14,
    'avg_latency_ms': 523.2,
    'contract_address': '0x...'
}
```

#### 📊 **Latency Measurements**
- **Balance Check**: Time to query account balance
- **Block Fetch**: Time to get latest block info
- **Contract Call**: Time to read from smart contract
- **Transaction Send**: Time to send and confirm transaction

```python
# Example latency results
{
    'balance_check': {'avg_ms': 21.45, 'min_ms': 12.3, 'max_ms': 45.2},
    'block_fetch': {'avg_ms': 19.8, 'min_ms': 11.1, 'max_ms': 38.9},
    'contract_call': {'avg_ms': 23.1, 'min_ms': 14.5, 'max_ms': 52.3},
    'transaction_send': {'avg_ms': 487.3, 'min_ms': 234.1, 'max_ms': 892.1}
}
```

#### ⚡ **Throughput Metrics**
- **Throughput TPS**: Mixed operations per second (writes + reads)
- **Write TPS**: Write transactions per second
- **Read TPS**: Read operations per second  
- **Data Transfer**: Secondary metric showing KB/s of data moved
- **Success Rate**: Percentage of operations that completed successfully

### Performance Best Practices

#### 🎯 **Optimize Your Applications**

```python
# 1. Batch operations when possible
async def batch_operations():
    pc = PureChain('testnet')
    pc.connect('your_key')
    
    # Instead of multiple single calls
    # for user in users:
    #     balance = await pc.balance(user)
    
    # Use concurrent execution
    import asyncio
    balances = await asyncio.gather(*[
        pc.balance(user) for user in users
    ])

# 2. Use read operations efficiently
async def efficient_reads():
    pc = PureChain('testnet')
    
    # Cache frequently accessed data
    latest_block = await pc.block()
    
    # Use the block number for multiple queries
    for contract in contracts:
        # Process using cached block data
        pass

# 3. Monitor performance in production
async def production_monitoring():
    pc = PureChain('mainnet')
    pc.connect('production_key')
    
    # Run quick performance checks periodically
    health_check = await pc.runPerformanceTest(quick=True)
    
    if health_check['tps']['actual_tps'] < 20:
        # Alert: Performance degradation detected
        send_alert("PureChain performance below threshold")
```

<!-- #### 📈 **Expected Performance Ranges**

Based on our testing, here are typical performance ranges for PureChain:

| Metric | Typical Range | Excellent |
|--------|---------------|-----------|
| **Latency (reads)** | 15-50ms | <20ms |
| **Latency (writes)** | 200-800ms | <400ms |
| **TPS (single client)** | 30-100 | 80+ |
| **Throughput (mixed TPS)** | 50-150 | 120+ |
| **Data Transfer** | 10-100 KB/s | >50 KB/s | -->

### Performance Testing Tips

```python
# 1. Warm up the network first
async def performance_with_warmup():
    pc = PureChain('testnet')
    pc.connect('your_key')
    
    # Warm up - send a few transactions first
    print("🔥 Warming up network...")
    for _ in range(5):
        await pc.balance()
    
    # Now run actual performance test
    results = await pc.testTPS(30, 50)

# 2. Test different times of day
# Network performance may vary based on usage

# 3. Compare mainnet vs testnet
testnet_results = await PureChain('testnet').runPerformanceTest()
mainnet_results = await PureChain('mainnet').runPerformanceTest()

# 4. Monitor over time
performance_history = []
for day in range(7):
    daily_results = await pc.runPerformanceTest(quick=True)
    performance_history.append(daily_results)
```

## 🔒 Smart Contract Security Auditing (NEW!)

**One-liner security audits with built-in tools!** No setup required - tools auto-install on first use.

### Quick Start - Pythonic One-Liners

```python
# SIMPLEST: One-liner audit
import purechainlib as pcl
result = await pcl.audit("contract code here")

# That's it! Security audit complete! 🎉
```

### Security Audit Examples

```python
import asyncio
from purechainlib import PureChain

async def security_examples():
    pc = PureChain('testnet')
    
    # 1. Simple audit (Pythonic!)
    result = await pc.audit(contract_code)
    if result['summary']['critical'] == 0:
        print("✅ Contract is safe!")
    
    # 2. Choose your tool
    await pc.audit(contract_code, tool="slither")   # Fast static analysis
    await pc.audit(contract_code, tool="mythril")   # Deep symbolic execution
    await pc.audit(contract_code, tool="all")       # Run everything!
    
    # 3. Audit & Deploy (only deploys if safe)
    safe_contract = await pc.auditAndDeploy(
        contract_code,
        require_pass=True  # Won't deploy if vulnerabilities found
    )
    
    # 4. Auto-audit all deployments
    pc.enableAutoAudit()  # Every deployment is now audited first!
    
    # 5. Security loop for LLM integration
    result = await pc.runSecurityLoop(
        vulnerable_contract,
        max_iterations=5  # Keep trying until secure
    )
    
    # 6. Export logs for analysis
    logs = pc.getSecurityLogs()  # Get all audit history
    pc.exportSecurityLogs('audit_logs.json')  # For LLM processing

asyncio.run(security_examples())
```
<!-- 
### LLM Integration Pattern

```python
# Perfect for automated security fixing with LLMs!
async def llm_security_loop():
    pc = PureChain('testnet')
    
    # Run security loop
    result = await pc.runSecurityLoop(contract_code, max_iterations=5)
    
    # Get detailed logs for LLM
    logs = pc.getSecurityLogs()
    
    # Feed to your LLM
    prompt = f"Fix these vulnerabilities: {json.dumps(logs)}"
    # fixed_code = llm.generate(prompt)
    
    # Audit the fixed code
    final_audit = await pc.audit(fixed_code)
    
    # Deploy if safe
    if final_audit['summary']['critical'] == 0:
        contract = await factory.deploy()
``` -->

### Available Security Tools

| Tool | Type | Speed | Detection |
|------|------|-------|-----------|
| **Slither** | Static Analysis | Fast | 80+ vulnerability patterns |
| **Mythril** | Symbolic Execution | Slower | Deep analysis, finds edge cases |
| **Solhint** | Linter | Very Fast | Code quality & best practices |
| **ALL** | Combined | Slowest | Most comprehensive |

### Security Report Formats

```python
# Export in different formats
await pc.auditContract(code, export_report=True, report_format='json')     # For APIs
await pc.auditContract(code, export_report=True, report_format='markdown') # For docs
await pc.auditContract(code, export_report=True, report_format='html')     # For web
```

## 🌱 Carbon Footprint Tracking

PureChain SDK includes **Carbon footprint tracking**

### Why Carbon Tracking?

Even though PureChain uses **zero gas fees** and is extremely efficient, every computational operation still has an environmental impact. We provide transparent, scientific measurements to help you:
- Track environmental impact for ESG reporting
- Compare efficiency with other blockchains
- Make informed decisions about blockchain usage
- Generate compliance reports

### How to Use Carbon Tracking

```python
# Enable carbon tracking for your region
pc = PureChain('testnet')
pc.enableCarbonTracking('us')  # Options: 'global', 'us', 'eu', 'asia', 'renewable'

# Send transaction with carbon data
result = await pc.send(address, amount, include_carbon=True)
print(f"Carbon footprint: {result['carbon_footprint']['carbon']['gCO2']} gCO2")

# Deploy contract with carbon tracking
contract = await factory.deploy(track_carbon=True)

# Get carbon report
report = await pc.getCarbonReport()
print(f"Total emissions: {report['total_emissions']['kgCO2']} kg CO2")

# Get ESG metrics for reporting
esg = await pc.getCarbonESGMetrics()
print(f"Environmental metrics: {esg['environmental']}")

# Export full report
json_report = await pc.exportCarbonReport()
```

### 🔬 Scientific Methodology

Our carbon calculations are based on **actual measurements**, not estimates:

#### Energy Measurement
- **Direct CPU power monitoring** using Intel PowerTOP and turbostat
- **Measured on**: Intel Xeon E5-2686 v4 @ 2.30GHz (typical cloud server)
- **Energy per transaction**: ~0.029 Joules (8.1 × 10⁻⁹ kWh)
- **Accuracy**: ±5% based on measurement variance

#### Carbon Calculation
```
Carbon (gCO2) = Energy (kWh) × Grid Carbon Intensity (gCO2/kWh)
```

**Grid Carbon Intensity Sources:**
- US: EPA eGRID 2023 (420 gCO2/kWh average)
- EU: EEA 2023 (295 gCO2/kWh average)
- Global: IEA 2023 (475 gCO2/kWh average)

### 📊 Measured Performance

| Operation | Energy (Joules) | Carbon (gCO2) | vs Ethereum |
|-----------|-----------------|---------------|-------------|
| Transaction | 0.029 | 0.000003 | 99.99999% less |
| Contract Deploy | 0.517 | 0.000054 | 99.9998% less |
| Contract Execute | 0.010 | 0.000001 | 99.99999% less |

### Comparison with Other Blockchains

```python
# PureChain measurements (per transaction)
{
    'purechain': {
        'energy_kwh': 0.000000008,
        'co2_g': 0.000003,
        'comparison': 'Baseline'
    },
    'ethereum_pow': {
        'energy_kwh': 30,
        'co2_g': 30000,
        'times_worse': 3750000000  # 3.75 billion times
    },
    'ethereum_pos': {
        'energy_kwh': 0.01,
        'co2_g': 10,
        'times_worse': 1250000  # 1.25 million times
    },
    'bitcoin': {
        'energy_kwh': 511,
        'co2_g': 500000,
        'times_worse': 63875000000  # 63.9 billion times
    }
}
```

### Carbon Tracking API Reference

#### Enable/Disable Tracking
```python
# Enable with specific region
pc.enableCarbonTracking('us')  # US grid intensity
pc.enableCarbonTracking('eu')  # EU grid intensity
pc.enableCarbonTracking('renewable')  # Renewable energy

# Disable tracking
pc.disableCarbonTracking()
```

#### Transaction Carbon Data
```python
# Include carbon in transaction
result = await pc.send(to, value, include_carbon=True)

# Carbon data structure
{
    'carbon': {
        'gCO2': 0.000003,        # Grams of CO2
        'kgCO2': 0.000000003,    # Kilograms
        'tonnesCO2': 3e-12       # Metric tonnes
    },
    'comparison': {
        'vs_ethereum': '0.00001%',
        'savings_kg': 30.0
    },
    'environmental': {
        'trees_equivalent': 0.0000001
    },
    'offset': {
        'cost_usd': 0.00000003
    }
}
```

#### ESG Reporting
```python
# Get ESG-compliant metrics
esg = await pc.getCarbonESGMetrics()

# Returns
{
    'environmental': {
        'total_emissions_kg_co2': 0.000001,
        'emissions_per_transaction_g_co2': 0.000003,
        'carbon_efficiency_vs_ethereum': '99.99%+ reduction',
        'renewable_energy_compatible': True
    },
    'sustainability': {
        'zero_gas_operations': True,
        'energy_efficient': True
    },
    'reporting': {
        'methodology': 'ISO 14064-1 compatible',
        'verification': 'Automated tracking with PureChain SDK'
    }
}
```

### 🌍 Environmental Impact

Using PureChain instead of Ethereum for 1,000 transactions saves:
- **Energy**: 30 kWh (enough to power a home for 1 day)
- **Carbon**: 30 kg CO2 (equivalent to 1.4 trees for a year)
- **Cost**: $3.60 in electricity

### References

1. Sedlmeir et al. (2020): "The Energy Consumption of Blockchain Technology"
2. Cambridge Bitcoin Electricity Consumption Index (2023)
3. EPA eGRID Power Profiler (2023)
4. IEA Global Energy & CO2 Status Report (2023)

## ❓ FAQ

**Q: Are transactions really free?**  
A: Yes! PureChain has zero gas costs. All operations cost 0 PURE.

**Q: Can I deploy any Solidity contract?**  
A: Yes! PureChain is fully EVM compatible.

<!-- **Q: How do I get PURE tokens?**  
A: Contact the PureChain team or use the testnet faucet. -->

**Q: Is this compatible with Web3?**  
A: Yes! Built on Web3.py with PureChain-specific optimizations.

## 🔗 Links

- **NPM Package**: https://www.npmjs.com/package/purechainlib
<!-- - **GitHub**: https://github.com/purechainlib/purechainlib-python -->
<!-- - **Documentation**: https://docs.purechain.network -->

## 📄 License

MIT License - Free to use in any project!

---

**Zero Gas. Full EVM. Pure Innovation.** 🚀

*Built for the PureChain ecosystem - where blockchain development costs nothing!*