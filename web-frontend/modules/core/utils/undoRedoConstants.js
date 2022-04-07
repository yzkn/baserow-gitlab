export const UNDO_REDO_STATES = {
  // The undo has successfully completed
  UNDONE: 'UNDONE',
  // The redo has successfully completed
  REDONE: 'REDONE',
  // The undo action is currently executing
  UNDOING: 'UNDOING',
  // The redo action is currently executing
  REDOING: 'REDOING',
  // An undo was requested but there were no more actions to undo
  NO_MORE_UNDO: 'NO_MORE_UNDO',
  // An redo was requested but there were no more actions to undo
  NO_MORE_REDO: 'NO_MORE_REDO',
  // Something went wrong whilst undoing and so the undo was skipped over
  ERROR_WITH_UNDO: 'ERROR_WITH_UNDO',
  // Something went wrong whilst redoing and so the redo was skipped over
  ERROR_WITH_REDO: 'ERROR_WITH_REDO',
  // There is no recent undo/redo action
  HIDDEN: 'HIDDEN',
}
// The different types of undo/redo categories available. Use this functions when
// calling UPDATE_CURRENT_CATEGORY_SET.
export const ACTION_CATEGORIES = {
  root() {
    return {
      root: true,
    }
  },
  group(groupId) {
    return {
      group: groupId,
    }
  },
  application(applicationId) {
    return {
      application: applicationId,
    }
  },
  // todo move to database module?
  table(tableId) {
    return {
      table: tableId,
    }
  },
}

// Please keep in sync with baserow.api.user.serializers.UndoRedoResponseSerializer
export const UNDO_REDO_RESULT_CODES = {
  NOTHING_TO_DO: 'NOTHING_TO_DO',
  SUCCESS: 'SUCCESS',
  SKIPPED_DUE_TO_ERROR: 'SKIPPED_DUE_TO_ERROR',
}
