import UndoRedoService from '@baserow/modules/core/services/undoRedo'

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
// The different types of undo/redo scopes available. Use this functions when
// calling UPDATE_CURRENT_SCOPE.
export const SCOPES = {
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
export const state = () => ({
  undoing: false,
  redoing: false,
  // A stack of scopes. The last being the current scope.
  scopeStack: [{}],
})

export const mutations = {
  SET_UNDOING(state, value) {
    state.undoing = value
  },
  SET_REDOING(state, value) {
    state.redoing = value
  },
  RESET_SCOPE_STACK(state, scope) {
    state.scopeStack = [scope]
  },
  PUSH_NEW_SCOPE(state, scope) {
    state.scopeStack.push(scope)
  },
  POP_CURRENT_SCOPE(state) {
    state.scopeStack.pop()
  },
  UPDATE_CURRENT_SCOPE(state, newScope) {
    const current = state.scopeStack[state.scopeStack.length - 1]
    Object.assign(current, current, newScope)
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
      commitName: 'SET_UNDOING',
    })
  },
  async redo({ dispatch }, { showLoadingNotification }) {
    return await dispatch('action', {
      showLoadingNotification,
      serviceMethod: 'redo',
      doingNotificationState: UNDO_REDO_STATES.REDOING,
      doneNotificationState: UNDO_REDO_STATES.REDONE,
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
      await UndoRedoService(this.$client)[serviceMethod](
        getters.getCurrentScope
      )
      await dispatch('notification/setUndoRedoState', doneNotificationState, {
        root: true,
      })
    } catch (e) {
      const errorCodeToUndoRedoState = {
        ERROR_NO_MORE_ACTIONS_TO_UNDO: UNDO_REDO_STATES.NO_MORE_UNDO,
        ERROR_NO_MORE_ACTIONS_TO_REDO: UNDO_REDO_STATES.NO_MORE_REDO,
        ERROR_SKIPPING_UNDO_BECAUSE_IT_FAILED: UNDO_REDO_STATES.ERROR_WITH_UNDO,
        ERROR_SKIPPING_REDO_BECAUSE_IT_FAILED: UNDO_REDO_STATES.ERROR_WITH_REDO,
      }
      const newUndoRedoState = errorCodeToUndoRedoState[e.handler.code]

      if (newUndoRedoState) {
        await dispatch('notification/setUndoRedoState', newUndoRedoState, {
          root: true,
        })
      } else {
        throw e
      }
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
  resetScopeStack({ commit }, scope) {
    // TODO do we need this? Perhaps when switching route entirely?
    commit('RESET_SCOPE_STACK', scope)
  },
  pushNewScope({ commit }, scope) {
    // For use in modals. A model will push its own brand new scope on and then pop it
    // off after it has closed. By using a stack we can support many nested modals
    // doing this.
    commit('PUSH_NEW_SCOPE', scope)
  },
  popCurrentScope({ commit }) {
    // For use in modals. A model will push its own brand new scope on and then pop it
    // off after it has closed. By using a stack we can support many nested modals
    // doing this.
    commit('POP_CURRENT_SCOPE')
  },
  updateCurrentScope({ commit }, scope) {
    commit('UPDATE_CURRENT_SCOPE', scope)
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
    return state.scopeStack[state.scopeStack.length - 1]
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
