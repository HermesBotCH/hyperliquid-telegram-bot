from typing import Any, Dict
from hyperliquid.info import Info
from .hyperliquid_ratelimiter import hyperliquid_rate_limiter
from logging_utils import logger


class InfoProxy:
    # Weight definitions for each endpoint
    WEIGHTS: Dict[str, int] = {
        'all_mids': 2,
        'user_state': 2,
        'spot_user_state': 2,
        'spot_meta_and_asset_ctxs': 20,
        'meta_and_asset_ctxs': 20,
        'user_staking_summary': 20,
        'user_fills': 20,
        'user_fills_by_time': 20,
        'user_vault_equities': 20,
        'frontend_open_orders': 20,
        'meta': 20,
        'subscribe': 0,
        'candles_snapshot': 20,
        'funding_history': 20
    }

    def __init__(self, info: Info) -> None:
        self._info = info

    def meta_and_asset_ctxs(self, dex: str = "") -> Any:
        """Fetch perp meta + asset ctxs for a DEX.

        The underlying SDK's ``meta_and_asset_ctxs()`` never forwards a ``dex``
        argument (it only posts ``{"type": "metaAndAssetCtxs"}``), so passing one
        always raised a ``TypeError`` for builder DEXes (e.g. ``xyz``). The
        exchange API *does* accept ``dex`` here, so for non-default DEXes we
        post the DEX directly. Both paths are rate-limited identically.
        """
        if not dex:
            result = self._info.meta_and_asset_ctxs()
        else:
            result = self._info.post("/info", {"type": "metaAndAssetCtxs", "dex": dex})
        hyperliquid_rate_limiter.add_weight(self.WEIGHTS['meta_and_asset_ctxs'])
        return result

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._info, name)
        if callable(attr):
            def wrapped(*args: Any, **kwargs: Any) -> Any:
                result = attr(*args, **kwargs)
                if name in self.WEIGHTS:
                    weight = self.WEIGHTS[name]
                    hyperliquid_rate_limiter.add_weight(weight)
                else:
                    logger.warning(f"InfoProxy: method '{name}' called but not found in WEIGHTS dictionary")
                return result
            return wrapped
        return attr
