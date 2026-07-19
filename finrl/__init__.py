from __future__ import annotations

try:
    from finrl.test import test
except ImportError:
    pass

try:
    from finrl.trade import trade
except ImportError:
    pass

try:
    from finrl.train import train
except ImportError:
    pass
