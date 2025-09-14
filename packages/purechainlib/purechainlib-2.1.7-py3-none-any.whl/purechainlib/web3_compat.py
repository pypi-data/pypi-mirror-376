"""
Web3 compatibility layer for PureChainLib
Handles web3.py import with graceful fallback for Windows systems
"""
import sys
import platform
import warnings

# Track if we have full web3 support
HAS_FULL_WEB3 = False
WEB3_IMPORT_ERROR = None

try:
    # Try importing full web3 with all features
    from web3 import Web3, HTTPProvider
    from web3.contract import Contract
    from web3.types import TxParams, Wei

    # Try importing websocket support
    try:
        from web3 import WebsocketProvider
    except ImportError:
        try:
            from web3 import WebSocketProvider as WebsocketProvider
        except ImportError:
            WebsocketProvider = None

    HAS_FULL_WEB3 = True

except ImportError as e:
    WEB3_IMPORT_ERROR = str(e)

    # Fallback: Try importing web3 without blob transaction support
    try:
        # Import core web3 components
        import sys
        import importlib

        # Monkey-patch to skip ckzg import
        # Handle both dict and module forms of builtins
        import builtins
        original_import = builtins.__import__

        def custom_import(name, *args, **kwargs):
            if 'ckzg' in name:
                # Return a dummy module for ckzg
                class DummyModule:
                    def __getattr__(self, name):
                        raise NotImplementedError(
                            f"Blob transaction support not available: {name} from ckzg not implemented"
                        )
                return DummyModule()
            return original_import(name, *args, **kwargs)

        builtins.__import__ = custom_import

        from web3 import Web3, HTTPProvider
        from web3.contract import Contract
        from web3.types import TxParams, Wei

        try:
            from web3 import WebsocketProvider
        except ImportError:
            try:
                from web3 import WebSocketProvider as WebsocketProvider
            except ImportError:
                WebsocketProvider = None

        # Restore original import
        builtins.__import__ = original_import

        warnings.warn(
            "Web3 loaded without blob transaction support. "
            "This is fine for PureChain as it doesn't use EIP-4844 features.",
            UserWarning
        )

    except Exception as fallback_error:
        # Complete failure - provide helpful error message
        error_msg = f"""
Failed to import web3.py.

Original error: {WEB3_IMPORT_ERROR}
Fallback error: {fallback_error}

For Windows users, please try one of these solutions:

1. Install Microsoft C++ Build Tools:
   https://visualstudio.microsoft.com/visual-cpp-build-tools/
   Then: pip install purechainlib

2. Use pre-built wheels:
   pip install --only-binary :all: web3==6.20.3
   pip install purechainlib

3. Use Windows Subsystem for Linux (WSL):
   wsl --install
   Then install in WSL environment

4. Manual installation without blob support:
   python setup_windows.py
"""
        raise ImportError(error_msg)

def check_web3_features():
    """Check which web3 features are available"""
    features = {
        'basic': False,
        'websockets': False,
        'blob_transactions': False,
        'full_support': HAS_FULL_WEB3
    }

    try:
        # Check basic functionality
        w3 = Web3()
        features['basic'] = True
    except:
        pass

    # Check websocket support
    features['websockets'] = WebsocketProvider is not None

    # Check blob transaction support (requires ckzg)
    try:
        import ckzg
        features['blob_transactions'] = True
    except ImportError:
        features['blob_transactions'] = False

    return features

# Export the imported components
__all__ = [
    'Web3',
    'HTTPProvider',
    'WebsocketProvider',
    'Contract',
    'TxParams',
    'Wei',
    'check_web3_features',
    'HAS_FULL_WEB3'
]