class GraphAPIError(Exception):
    """Error genérico al comunicarse con la Graph API de Meta."""


class NotAPageError(GraphAPIError):
    """El objetivo consultado no es una Página pública (no expone `category`).

    Esto ocurre típicamente cuando el ID corresponde a un perfil personal,
    que la Graph API bloquea a terceros. El sistema NUNCA monitorea perfiles.
    """


class RateLimitedError(GraphAPIError):
    """La Graph API devolvió un 429 / código de rate limit (código 4, 17, 32, 613 de Meta)."""
