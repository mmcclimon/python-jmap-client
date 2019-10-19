class ConfigurationError(RuntimeError):
    """The kind of error you get when you try to call something and have not
    configured the client correctly."""


class SentenceError(AssertionError):
    """The kind of error you get when you try to do a nonsensical sentence-related thing"""
