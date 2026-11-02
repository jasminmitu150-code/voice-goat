"""Decorators for marking vulnerable functions and checking for flags."""

import functools
from typing import Any, Callable

from services.common.logging import get_logger
from services.common.flags.models import FlagCategory, FlagDifficulty

logger = get_logger("vulnerability")


def vulnerable(
    category: str,
    vuln_type: str,
    flag: str,
    difficulty: str = "medium",
    description: str = "",
) -> Callable:
    """
    Decorator to mark a function as intentionally vulnerable.
    
    This is for documentation and auditing purposes. It doesn't
    change the function's behavior but logs vulnerability metadata.
    
    Args:
        category: OWASP LLM category (e.g., "LLM01")
        vuln_type: Type of vulnerability (e.g., "direct_injection")
        flag: Associated flag ID
        difficulty: easy/medium/hard
        description: Description of the vulnerability
        
    Example:
        @vulnerable(
            category="LLM01",
            vuln_type="direct_injection",
            flag="FLAG{LLM01_DIRECT_001}",
            difficulty="easy"
        )
        def process_input(user_input: str) -> str:
            # VULNERABLE: No sanitization
            return llm.invoke(user_input)
    """
    def decorator(func: Callable) -> Callable:
        # Store vulnerability metadata on the function
        func._vulnerability = {
            "category": category,
            "type": vuln_type,
            "flag": flag,
            "difficulty": difficulty,
            "description": description,
            "function": func.__name__,
            "module": func.__module__,
        }
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.debug(
                "Vulnerable function called",
                function=func.__name__,
                category=category,
                vuln_type=vuln_type,
            )
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def check_flag_in_response(user_id: str) -> Callable:
    """
    Decorator to automatically check function responses for leaked flags.
    
    Args:
        user_id: User ID for flag attribution
        
    Example:
        @check_flag_in_response(user_id="test_user")
        def get_account_info(query: str) -> str:
            return llm.invoke(query)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            
            # Check if result is a string response
            if isinstance(result, str):
                from services.common.flags.service import flag_service
                
                captured = flag_service.check_response_for_flags(
                    response=result,
                    user_id=user_id,
                    method=f"response_from_{func.__name__}",
                )
                
                if captured:
                    logger.info(
                        "Flags captured from response",
                        function=func.__name__,
                        flags=captured,
                    )
            
            return result
        
        return wrapper
    return decorator


def get_vulnerable_functions() -> list[dict]:
    """
    Discover all functions marked with @vulnerable decorator.
    
    This is useful for generating documentation and auditing.
    
    Returns:
        List of vulnerability metadata dictionaries
    """
    import importlib
    import pkgutil
    
    vulnerabilities = []
    
    # Scan services package
    import services
    for importer, modname, ispkg in pkgutil.walk_packages(
        services.__path__, 
        prefix="services."
    ):
        try:
            module = importlib.import_module(modname)
            for name in dir(module):
                obj = getattr(module, name)
                if callable(obj) and hasattr(obj, "_vulnerability"):
                    vulnerabilities.append(obj._vulnerability)
        except ImportError:
            pass
    
    return vulnerabilities
