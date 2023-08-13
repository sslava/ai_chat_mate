from baski.telegram import handlers
from .context import Context


__all__ = ['BasicHandler']


class BasicHandler(handlers.LogErrorHandler, handlers.TypedHandler):

    def __init__(self, ctx: Context):
        super().__init__()
        self._ctx = ctx

    @property
    def ctx(self) -> Context:
        return self._ctx
