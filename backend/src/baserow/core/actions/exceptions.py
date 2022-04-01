class NoMoreActionsToUndoException(Exception):
    pass


class NoMoreActionsToRedoException(Exception):
    pass


class SkippingUndoBecauseItFailedException(Exception):
    pass


class SkippingRedoBecauseItFailedException(Exception):
    pass
