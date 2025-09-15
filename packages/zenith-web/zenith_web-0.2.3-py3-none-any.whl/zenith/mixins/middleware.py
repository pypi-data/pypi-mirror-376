"""
Middleware configuration mixin for Zenith applications.

Contains all methods related to adding and configuring middleware.
"""


class MiddlewareMixin:
    """Mixin for middleware configuration methods."""

    def add_middleware(self, middleware_class, **kwargs) -> None:
        """Add middleware to the application."""
        from starlette.middleware import Middleware

        # Check for existing middleware of the same class to prevent duplication
        existing_middleware = [mw.cls for mw in self.middleware]
        if middleware_class in existing_middleware:
            # Replace existing middleware with the same class
            for i, mw in enumerate(self.middleware):
                if mw.cls == middleware_class:
                    self.middleware[i] = Middleware(middleware_class, **kwargs)
                    break
        else:
            # Add new middleware
            self.middleware.append(Middleware(middleware_class, **kwargs))

        # Invalidate cached Starlette app so it gets rebuilt with new middleware
        self._starlette_app = None

    def add_cors(
        self,
        allow_origins: list[str] | None = None,
        allow_credentials: bool = False,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        **kwargs,
    ) -> None:
        """Add CORS middleware with configuration."""
        from zenith.middleware.cors import CORSMiddleware

        self.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins or ["*"],
            allow_credentials=allow_credentials,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
            **kwargs,
        )

    def add_exception_handling(self, debug: bool | None = None, **kwargs) -> None:
        """Add exception handling middleware."""
        from zenith.middleware.exceptions import ExceptionHandlerMiddleware

        self.add_middleware(
            ExceptionHandlerMiddleware,
            debug=debug if debug is not None else self.config.debug,
            **kwargs,
        )

    def add_rate_limiting(
        self, default_limit: int = 1000, window_seconds: int = 3600, **kwargs
    ) -> None:
        """Add rate limiting middleware."""
        from zenith.middleware.rate_limit import RateLimit, RateLimitMiddleware

        # Create default limits from the provided parameters
        default_limits = [
            RateLimit(requests=default_limit, window=window_seconds, per="ip")
        ]

        self.add_middleware(
            RateLimitMiddleware,
            default_limits=default_limits,
            **kwargs,
        )

    def add_security_headers(self, config=None, strict: bool = False, **kwargs) -> None:
        """Add or replace security headers middleware."""
        from zenith.middleware.security import (
            SecurityHeadersMiddleware,
            get_development_security_config,
            get_strict_security_config,
        )

        if config is None:
            if strict:
                config = get_strict_security_config()
            else:
                config = get_development_security_config()

        # Apply any kwargs overrides
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        # Remove existing SecurityHeadersMiddleware if present
        from starlette.middleware import Middleware

        self.middleware = [
            m
            for m in self.middleware
            if not (isinstance(m, Middleware) and m.cls == SecurityHeadersMiddleware)
        ]

        # Add the new one with custom config
        self.add_middleware(SecurityHeadersMiddleware, config=config)

    def add_csrf_protection(
        self,
        secret_key: str | None = None,
        csrf_token_header: str = "X-CSRF-Token",
        exempt_methods: list[str] | None = None,
        **kwargs,
    ) -> None:
        """Add CSRF protection middleware."""
        from zenith.middleware.csrf import CSRFConfig, CSRFMiddleware

        if secret_key is None:
            raise ValueError("CSRF secret key is required")

        config = CSRFConfig(
            secret_key=secret_key,
            header_name=csrf_token_header,
            exempt_methods=set(exempt_methods or ["GET", "HEAD", "OPTIONS", "TRACE"]),
            **kwargs,
        )

        self.add_middleware(CSRFMiddleware, config=config)

    def add_trusted_proxies(self, trusted_proxies: list[str]) -> None:
        """Add trusted proxy middleware."""
        from zenith.middleware.security import TrustedProxyMiddleware

        self.add_middleware(TrustedProxyMiddleware, trusted_proxies=trusted_proxies)
