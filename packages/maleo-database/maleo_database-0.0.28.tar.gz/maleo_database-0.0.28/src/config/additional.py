from pydantic import BaseModel, Field
from typing import Literal, Optional, TypeVar, Union, overload
from maleo.enums.cache import Origin, Layer
from maleo.enums.expiration import Expiration
from maleo.types.base.string import OptionalString
from maleo.utils.cache import build_namespace as build_namespace_utils


class BaseAdditionalConfig(BaseModel):
    """Base additional configuration class for database."""


AdditionalConfigT = TypeVar("AdditionalConfigT", bound=Optional[BaseAdditionalConfig])


class RedisAdditionalConfig(BaseAdditionalConfig):
    ttl: Union[float, int] = Field(
        Expiration.EXP_15MN.value, description="Time to live"
    )
    base_namespace: str = Field(..., description="Base namespace")

    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_base: Literal[False],
        base: OptionalString = None,
        origin: Literal[Origin.SERVICE],
        layer: Layer,
        sep: str = ":",
    ) -> str: ...
    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_base: Literal[False],
        base: OptionalString = None,
        client: str,
        origin: Literal[Origin.CLIENT],
        layer: Layer,
        sep: str = ":",
    ) -> str: ...
    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_base: Literal[True],
        origin: Literal[Origin.SERVICE],
        layer: Layer,
        sep: str = ":",
    ) -> str: ...
    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_base: Literal[True],
        client: str,
        origin: Literal[Origin.CLIENT],
        layer: Layer,
        sep: str = ":",
    ) -> str: ...
    def build_namespace(
        self,
        *ext: str,
        use_self_base: bool = True,
        base: OptionalString = None,
        client: OptionalString = None,
        origin: Origin,
        layer: Layer,
        sep: str = ":",
    ) -> str:
        if use_self_base:
            final_base = self.base_namespace
        else:
            final_base = base
        base = base or self.base_namespace
        if origin is Origin.CLIENT:
            if client is None:
                raise ValueError(
                    "Argument 'client' can not be None if origin is client"
                )

            # Here Pylance now knows: client is str, origin is Literal[Origin.CLIENT]
            return build_namespace_utils(
                *ext,
                base=final_base,
                client=client,
                origin=origin,
                layer=layer,
                sep=sep,
            )

        # Here Pylance now knows: origin is Literal[Origin.SERVICE]
        return build_namespace_utils(
            *ext,
            base=final_base,
            origin=origin,
            layer=layer,
            sep=sep,
        )
