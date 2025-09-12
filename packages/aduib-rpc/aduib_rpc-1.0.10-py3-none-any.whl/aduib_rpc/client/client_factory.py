import logging
from collections.abc import Callable

import grpc
import httpx
from grpc import Compression

from aduib_rpc.client import ClientRequestInterceptor
from aduib_rpc.client.base_client import ClientConfig, AduibRpcClient, BaseAduibRpcClient
from aduib_rpc.client.transports.base import ClientTransport
from aduib_rpc.client.transports.grpc import GrpcTransport
from aduib_rpc.client.transports.jsonrpc import JsonRpcTransport
from aduib_rpc.client.transports.rest import RestTransport
from aduib_rpc.utils.constant import TransportSchemes

TransportProducer = Callable[
    [str, ClientConfig, list[ClientRequestInterceptor]],
    ClientTransport,
]

logger = logging.getLogger(__name__)


class AduibRpcClientFactory:
    """Factory class for creating AduibRpcClient instances."""

    def __init__(
            self,
            config: ClientConfig,
    ):
        self._config = config
        self._registry: dict[str, TransportProducer] = {}
        self._register_defaults(config.supported_transports)

    def _register_defaults(
            self, supported: list[str | TransportSchemes]
    ) -> None:
        # Empty support list implies JSON-RPC only.
        if TransportSchemes.JSONRPC in supported or not supported:
            self.register(
                TransportSchemes.JSONRPC,
                lambda url, config, interceptors: JsonRpcTransport(
                    config.httpx_client or httpx.AsyncClient(),
                    url,
                    interceptors,
                ),
            )
        if TransportSchemes.HTTP in supported:
            self.register(
                TransportSchemes.HTTP,
                lambda url, config, interceptors: RestTransport(
                    config.httpx_client or httpx.AsyncClient(),
                    url,
                    interceptors,
                ),
            )
        if TransportSchemes.GRPC in supported:
            self.register(
                TransportSchemes.GRPC,
                GrpcTransport.create,
            )

    def register(self, label: str, generator: TransportProducer) -> None:
        """Register a new transport producer for a given transport label."""
        self._registry[label] = generator

    def create(
            self,
            url: str,
            server_preferred: str = TransportSchemes.JSONRPC,
            interceptors: list[ClientRequestInterceptor] | None = None,
    ) -> AduibRpcClient:
        """Create a new `Client` for the provided `AgentCard`.

        Args:
          card: An `AgentCard` defining the characteristics of the agent.
          consumers: A list of `Consumer` methods to pass responses to.
          interceptors: A list of interceptors to use for each request. These
            are used for things like attaching credentials or http headers
            to all outbound requests.

        Returns:
          A `Client` object.

        Raises:
          If there is no valid matching of the client configuration with the
          server configuration, a `ValueError` is raised.
        """
        server_set = {server_preferred: url}
        client_set = self._config.supported_transports or [
            TransportSchemes.JSONRPC
        ]
        transport_protocol = None
        transport_url = None
        for x, url in server_set.items():
            if x in client_set:
                transport_protocol = x
                transport_url = url
                break
        if not transport_protocol or not transport_url:
            raise ValueError('no compatible transports found.')
        if transport_protocol not in self._registry:
            raise ValueError(f'no client available for {transport_protocol}')

        transport = self._registry[transport_protocol](
            transport_url, self._config, interceptors or []
        )

        return BaseAduibRpcClient(
            self._config, transport, interceptors or []
        )

    @classmethod
    def create_client(
            cls,
            url: str,
            stream: bool = False,
            server_preferred: str = TransportSchemes.JSONRPC,
            interceptors: list[ClientRequestInterceptor] | None = None,
    ) -> AduibRpcClient:
        match server_preferred:
            case TransportSchemes.GRPC:
                def create_channel(url: str) -> grpc.aio.Channel:
                    logging.debug(f'Channel URL: {url}')
                    return grpc.aio.insecure_channel(url, options=[
                        ('grpc.max_receive_message_length', 100 * 1024 * 1024),
                        ('grpc.max_send_message_length', 100 * 1024 * 1024),
                    ],compression=Compression.Gzip)

                client_factory = AduibRpcClientFactory(
                    config=ClientConfig(streaming=stream, grpc_channel_factory=create_channel,
                                        supported_transports=[TransportSchemes.GRPC]))
                aduib_rpc_client: AduibRpcClient = client_factory.create(url,
                                                                         server_preferred=TransportSchemes.GRPC,
                                                                         interceptors=interceptors)
                return aduib_rpc_client
            case TransportSchemes.JSONRPC:
                client_factory = AduibRpcClientFactory(
                    config=ClientConfig(streaming=stream,
                                        httpx_client=httpx.AsyncClient(),
                                        supported_transports=[TransportSchemes.JSONRPC]))
                aduib_rpc_client: AduibRpcClient = client_factory.create(url,
                                                                         server_preferred=TransportSchemes.JSONRPC,
                                                                         interceptors=interceptors)
                return aduib_rpc_client
            case TransportSchemes.HTTP:
                client_factory = AduibRpcClientFactory(
                    config=ClientConfig(streaming=stream,
                                        httpx_client=httpx.AsyncClient(),
                                        supported_transports=[TransportSchemes.GRPC, TransportSchemes.JSONRPC,
                                                              TransportSchemes.HTTP]))
                aduib_rpc_client: AduibRpcClient = client_factory.create(url,
                                                                         server_preferred=TransportSchemes.HTTP,
                                                                         interceptors=interceptors)
                return aduib_rpc_client
            case _:
                raise ValueError(f'Unsupported transport scheme: {server_preferred}')
