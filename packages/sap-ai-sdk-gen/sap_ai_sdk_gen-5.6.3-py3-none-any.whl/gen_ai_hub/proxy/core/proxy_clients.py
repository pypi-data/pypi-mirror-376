from __future__ import annotations

import inspect
import os
import threading
import uuid
from contextlib import contextmanager
from typing import Optional

from .base import BaseProxyClient

THREAD_PROXY_VERSION_OVERWRITE = 'proxy_version_overwrite'
PROXY_VERSION_ENV_VARIABLE = 'LLM_PROXY_VERSION'

no_value = object()


class ProxyClients:

    def __init__(self) -> None:
        self.clients: dict[str, type[BaseProxyClient]] = {}
        self._thread_local = threading.local()
        self.proxy_version = os.environ.get(PROXY_VERSION_ENV_VARIABLE, None)
        self.thread_variable_name = THREAD_PROXY_VERSION_OVERWRITE + str(uuid.uuid4())

    def register(self, name: str):
        """
        Decorator to register a proxy client class.

        Args:
            name (str): The name to register the proxy client class under.

        Returns:
            Callable: A wrapper function.
        """

        def wrapper(proxy_cls: type[BaseProxyClient]) -> type[BaseProxyClient]:
            if not issubclass(proxy_cls, BaseProxyClient):
                raise ValueError('You can only register ProxyClient subclasses')
            self.clients[name] = proxy_cls
            return proxy_cls

        return wrapper

    def get_proxy_cls(self, proxy_version: str | None = None) -> type[BaseProxyClient]:
        """
        Get the proxy client class for the given version.

        Args:
            proxy_version (str | None): The proxy version.

        Returns:
            type[BaseProxyClient]: The proxy client class.
        """
        proxy_version = proxy_version or get_proxy_version()
        return self.clients[proxy_version]

    def get_proxy_cls_name(self, proxy_client_cls: type[BaseProxyClient] | BaseProxyClient) -> str:
        """
        Get the name of the proxy client class.

        Args:
            proxy_client_cls (type[BaseProxyClient] | BaseProxyClient): The proxy client class or instance.

        Returns:
            str: The name of the proxy client class.

        Raises:
            ValueError: If the provided class is not a subclass of BaseProxyClient.
            KeyError: If the class is not registered.
        """
        if not inspect.isclass(proxy_client_cls):
            proxy_client_cls = type(proxy_client_cls)
        if not issubclass(proxy_client_cls, BaseProxyClient):
            raise ValueError("'proxy_client_cls' has to be a ProxyClient class or an instance of an ProxyClient class.")

        for name, cls in self.clients.items():
            if cls is proxy_client_cls:
                return name
        raise KeyError(f'{proxy_client_cls} is not a registered client.')


@contextmanager
def proxy_version_context(proxy_version: str, catalog: Optional[ProxyClients] = None) -> None:
    """
    Context manager to set a thread-local proxy version.

    Args:
        proxy_version (str): The proxy version to set.
        catalog (Optional[ProxyClients]): The catalog for which the proxy version is to be set. If none is provided,
                                      the proxy version is set for the default proxy_clients catalog.

    Raises:
        ValueError: If proxy_version is not a string.
    """
    catalog = catalog or proxy_clients
    if not isinstance(proxy_version, str):
        raise ValueError('proxy_version has to be a string')

    old_value = getattr(catalog._thread_local, catalog.thread_variable_name, no_value)
    setattr(catalog._thread_local, catalog.thread_variable_name, proxy_version.lower())

    try:
        yield
    finally:
        # Restore the original value when exiting the context
        if old_value is no_value:
            delattr(catalog._thread_local, catalog.thread_variable_name)
        else:
            setattr(catalog._thread_local, catalog.thread_variable_name, old_value)


def set_proxy_version(proxy_version: str, catalog: Optional[ProxyClients] = None) -> None:
    """
    Set the global proxy version.

    Args:
        proxy_version (str): The proxy version to set.
        catalog (Optional[ProxyClients]): The catalog for which the proxy version is to be set. If none is provided,
                                      the proxy version is set for the default proxy_clients catalog.

    Raises:
        ValueError: If proxy_version is not a string.
    """
    catalog = catalog or proxy_clients
    if not isinstance(proxy_version, str):
        raise ValueError('proxy_version has to be a string')

    catalog.proxy_version = proxy_version.lower()


def get_proxy_version(catalog: Optional[ProxyClients] = None) -> str:
    """
    Get the current proxy version.
    The version is selected in the following order:
    - thread-local overwrite (set with proxy_version_context)
    - global overwrite (set with set_proxy_version)
    - environment variable (LLM_PROXY_VERSION)
    - first registered proxy version

    Args:
        catalog (Optional[ProxyClients]): An instance of the ProxyClients class. Defaults to None,
                                       in which case the global proxy_clients object is used.

    Returns:
        str: The current proxy version.
    """
    catalog = catalog or proxy_clients
    thread_overwrite = getattr(catalog._thread_local, catalog.thread_variable_name, None)
    env_version = os.environ.get(PROXY_VERSION_ENV_VARIABLE, None)
    fallback_version = [*catalog.clients.keys()][0] if catalog.clients else None
    proxy_version = thread_overwrite or catalog.proxy_version or env_version or fallback_version
    if not proxy_version:
        raise ValueError('No proxy version set. Please use set_proxy_version or proxy_version_context.')
    return proxy_version


def get_proxy_client(proxy_version: str | None = None,
                     catalog: Optional[ProxyClients] = None,
                     **kwargs) -> BaseProxyClient:
    """
    Get a proxy client for the given proxy version.

    Args:
        proxy_version (str | None): The version of the proxy client to retrieve. If not provided, the function will
                                  attempt to retrieve the version using the `get_proxy_version` function.
        catalog (ProxyClients, optional): The catalog from which to retrieve the proxy client.
                                        If not provided, the function will default to the `proxy_clients` catalog.
        **kwargs: Arbitrary keyword arguments that will be passed to the constructor of the proxy client class.

    Returns:
        BaseProxyClient: An instance of the proxy client.
    """
    catalog = catalog or proxy_clients
    proxy_version = proxy_version or get_proxy_version()
    return catalog.get_proxy_cls(proxy_version)(**kwargs)


proxy_clients = ProxyClients()
