class YouTubeError(Exception):
    """Error genérico al comunicarse con la YouTube Data API."""


class ChannelNotFoundError(YouTubeError):
    """No se pudo resolver el canal público a partir de la referencia dada (ID, handle o URL)."""
