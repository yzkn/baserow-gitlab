import UndoRedoService from '@baserow/modules/core/services/undoRedo'
import {
  UNDO_REDO_RESULT_CODES,
  UNDO_REDO_STATES,
} from '@baserow/modules/core/utils/undoRedoConstants'

export const state = () => ({
  undoing: false,
  redoing: false,
  // A stack of objects, each object representing a set of visible action categories.
  // The last object in the stack is the current set of categories which are visible.
  actionCategoriesStack: [{}],
})

export const mutations = {
  SET_UNDOING(state, value) {
    state.undoing = value
  },
  SET_REDOING(state, value) {
    state.redoing = value
  },
  RESET_ACTION_CATEGORY_SET_STACK(state, newCategorySet) {
    state.actionCategoriesStack = [newCategorySet]
  },
  PUSH_NEW_ACTION_CATEGORY_SET(state, newCategorySet) {
    state.actionCategoriesStack.push(newCategorySet)
  },
  POP_CURRENT_ACTION_CATEGORY_SET(state) {
    state.actionCategoriesStack.pop()
  },
  UPDATE_CURRENT_CATEGORY_SET(state, newCategory) {
    const current =
      state.actionCategoriesStack[state.actionCategoriesStack.length - 1]
    Object.assign(current, current, newCategory)
  },
}

let hideTimeout = null

export const actions = {
  async undo({ dispatch }, { showLoadingNotification }) {
    return await dispatch('action', {
      showLoadingNotification,
      serviceMethod: 'undo',
      doingNotificationState: UNDO_REDO_STATES.UNDOING,
      doneNotificationState: UNDO_REDO_STATES.UNDONE,
      nothingToDoNotificationState: UNDO_REDO_STATES.NO_MORE_REDO,
      skippedDueToErrorNotificationState: UNDO_REDO_STATES.ERROR_WITH_REDO,
      commitName: 'SET_UNDOING',
    })
  },
  async redo({ dispatch }, { showLoadingNotification }) {
    return await dispatch('action', {
      showLoadingNotification,
      serviceMethod: 'redo',
      doingNotificationState: UNDO_REDO_STATES.REDOING,
      doneNotificationState: UNDO_REDO_STATES.REDONE,
      nothingToDoNotificationState: UNDO_REDO_STATES.NO_MORE_REDO,
      skippedDueToErrorNotificationState: UNDO_REDO_STATES.ERROR_WITH_REDO,
      commitName: 'SET_REDOING',
    })
  },
  async action(
    { getters, commit, dispatch },
    {
      showLoadingNotification,
      serviceMethod,
      doingNotificationState,
      doneNotificationState,
      nothingToDoNotificationState,
      skippedDueToErrorNotificationState,
      commitName,
    }
  ) {
    if (getters.isUndoing || getters.isRedoing) {
      return
    }

    clearTimeout(hideTimeout)
    commit(commitName, true)
    await dispatch(
      'notification/setUndoRedoState',
      showLoadingNotification
        ? doingNotificationState
        : UNDO_REDO_STATES.HIDDEN,
      { root: true }
    )

    try {
      const { data } = await UndoRedoService(this.$client)[serviceMethod](
        getters.getCurrentScope
      )
      const resultCodeToNotificationState = {
        [UNDO_REDO_RESULT_CODES.SUCCESS]: doneNotificationState,
        [UNDO_REDO_RESULT_CODES.NOTHING_TO_DO]: nothingToDoNotificationState,
        [UNDO_REDO_RESULT_CODES.SKIPPED_DUE_TO_ERROR]:
          skippedDueToErrorNotificationState,
      }
      await dispatch(
        'notification/setUndoRedoState',
        resultCodeToNotificationState[data.result_code],
        {
          root: true,
        }
      )
    } finally {
      hideTimeout = setTimeout(
        () =>
          dispatch('notification/setUndoRedoState', UNDO_REDO_STATES.HIDDEN, {
            root: true,
          }),
        2000
      )
      commit(commitName, false)
    }
  },
  resetCategorySetStack({ commit }, categorySet) {
    // TODO do we need this? Perhaps when switching route entirely?
    commit('RESET_ACTION_CATEGORY_SET_STACK', categorySet)
  },
  pushNewCategorySet({ commit }, categorySet) {
    // For use in modals. A modal will push a new category set when opened restricting
    // the actions available for undo/redo to just those visible from the modal.
    // When the modal closes it should then call popCurrentCategorySet to reset to
    // previous category set.
    commit('PUSH_NEW_ACTION_CATEGORY_SET', categorySet)
  },
  popCurrentCategorySet({ commit }) {
    commit('POP_CURRENT_ACTION_CATEGORY_SET')
  },
  updateCurrentCategorySet({ commit }, category) {
    commit('UPDATE_CURRENT_CATEGORY_SET', category)
  },
}

export const getters = {
  isUndoing(state) {
    return state.undoing
  },
  isRedoing(state) {
    return state.redoing
  },
  getCurrentScope(state) {
    return state.actionCategoriesStack[state.actionCategoriesStack.length - 1]
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
