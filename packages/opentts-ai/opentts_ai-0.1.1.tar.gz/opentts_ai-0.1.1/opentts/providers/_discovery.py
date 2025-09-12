import importlib
import pkgutil
import os
import logging
from typing import Dict, List, Callable, Any, Optional

logger = logging.getLogger(__name__)

# Registry to hold discovered engine functions: { 'provider_1': {'tts': create_speech_func}, ... }
PROVIDER_REGISTRY: Dict[str, Dict[str, Callable]] = {}
# Registry to hold discovered capabilities per provider: { 'provider_1': ['tts'], ... }
PROVIDER_CAPABILITIES: Dict[str, List[str]] = {}
# Optional: Store provider metadata like human-readable names
PROVIDER_METADATA: Dict[str, Dict[str, Any]] = {}

def find_providers():
    """
    Scans the 'providers' directory dynamically, imports provider modules,
    reads their capabilities, and populates the provider registry.
    """
    global PROVIDER_REGISTRY, PROVIDER_CAPABILITIES, PROVIDER_METADATA
    PROVIDER_REGISTRY.clear()
    PROVIDER_CAPABILITIES.clear()
    PROVIDER_METADATA.clear()

    providers_package_path = os.path.dirname(__file__)
    logger.info(f"Scanning for providers in: {providers_package_path}")

    current_package = __package__ or 'a4f_local.providers'

    for _, provider_name, is_pkg in pkgutil.iter_modules([providers_package_path]):
        if is_pkg and provider_name.startswith("provider_"):
            logger.debug(f"Found potential provider package: {provider_name}")
            try:
                provider_module_path = f".{provider_name}"
                provider_init = importlib.import_module(provider_module_path, package=current_package)

                if hasattr(provider_init, 'CAPABILITIES') and isinstance(provider_init.CAPABILITIES, list):
                    capabilities = provider_init.CAPABILITIES
                    PROVIDER_CAPABILITIES[provider_name] = capabilities
                    PROVIDER_REGISTRY[provider_name] = {}
                    PROVIDER_METADATA[provider_name] = {
                        'name': getattr(provider_init, 'PROVIDER_NAME', provider_name)
                    }
                    logger.info(f"Discovered provider '{provider_name}' with capabilities: {capabilities}")

                    for capability in capabilities:
                        try:
                            capability_module_path = f".{provider_name}.{capability}"
                            capability_module = importlib.import_module(capability_module_path, package=current_package)

                            engine_func = None
                            if hasattr(capability_module, '__all__') and capability_module.__all__:
                                engine_func_name = capability_module.__all__[0]
                                if hasattr(capability_module, engine_func_name):
                                    engine_func = getattr(capability_module, engine_func_name)
                            else:
                                conventional_func_name = f"create_{capability}"
                                if hasattr(capability_module, conventional_func_name):
                                    engine_func = getattr(capability_module, conventional_func_name)

                            if engine_func and callable(engine_func):
                                PROVIDER_REGISTRY[provider_name][capability] = engine_func
                                logger.debug(f"  Registered engine for '{capability}' capability.")
                            else:
                                logger.warning(f"Could not find engine function for {provider_name}.{capability}")

                        except ImportError as e_cap:
                            logger.warning(f"Could not import capability module '{capability}' for provider '{provider_name}': {e_cap}")
                        except Exception as e_eng:
                             logger.error(f"Error processing engine for {provider_name}.{capability}: {e_eng}")

                else:
                    logger.warning(f"Skipping '{provider_name}': Does not have a valid 'CAPABILITIES' list.")

            except ImportError as e_prov:
                logger.warning(f"Could not import provider module '{provider_name}': {e_prov}")
            except Exception as e_gen:
                 logger.error(f"Error processing provider '{provider_name}': {e_gen}")

    logger.info(f"Provider discovery complete. Registry: {list(PROVIDER_REGISTRY.keys())}")


def get_provider_for_capability(capability: str) -> Optional[str]:
    """
    Finds the first discovered provider that supports a given capability.
    """
    for provider_name, capabilities in PROVIDER_CAPABILITIES.items():
        if capability in capabilities:
            logger.debug(f"Found provider '{provider_name}' for capability '{capability}'")
            return provider_name
    logger.warning(f"No provider found supporting capability: {capability}")
    return None

def get_engine(provider_name: str, capability: str) -> Optional[Callable]:
    """Gets the registered engine function for a specific provider and capability."""
    provider_engines = PROVIDER_REGISTRY.get(provider_name)
    if provider_engines:
        engine_func = provider_engines.get(capability)
        if engine_func:
            return engine_func
        else:
            logger.error(f"Capability '{capability}' not found in registry for provider '{provider_name}'")
    else:
        logger.error(f"Provider '{provider_name}' not found in registry.")
    return None

# Auto-run discovery when this module is imported
find_providers()
