#!/usr/bin/env python3
"""
Entry point for running the Scientific Calculator MCP Server.
This module provides the legacy entry point with deprecation warning.
"""


def main():
    """Legacy main function (deprecated)."""
    import warnings
    from calculator.server.app import run_calculator_server
    
    # Issue deprecation warning
    warnings.warn(
        "main is deprecated since version 2.0.0. Use calculator.server.app.run_calculator_server() instead",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Call the new function
    run_calculator_server()


if __name__ == "__main__":
    main()