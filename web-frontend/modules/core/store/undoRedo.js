import UndoService from '@baserow/modules/core/services/undo'

export const state = () => ({
  undoing: false,
  redoing: false,
})

export const mutations = {
  SET_UNDOING(state, value) {
    state.undoing = value
  },
  SET_REDOING(state, value) {
    state.redoing = value
  },
}

let hideTimeout = null

export const actions = {
  async undo({ dispatch }, { showLoadingNotification }) {
    return await dispatch('action', {
      showLoadingNotification,
      serviceMethod: 'undo',
      doingNotificationState: 'undoing',
      doneNotificationState: 'undone',
      commitName: 'SET_UNDOING',
    })
  },
  async redo({ dispatch }, { showLoadingNotification }) {
    return await dispatch('action', {
      showLoadingNotification,
      serviceMethod: 'redo',
      doingNotificationState: 'redoing',
      doneNotificationState: 'redone',
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
      showLoadingNotification ? doingNotificationState : 'hidden',
      { root: true }
    )

    try {
      await UndoService(this.$client)[serviceMethod]('root')
      await dispatch('notification/setUndoRedoState', doneNotificationState, {
        root: true,
      })
    } catch (e) {
      if (['ERROR_NO_MORE_ACTIONS_TO_UNDO'].includes(e.handler.code)) {
        await dispatch('notification/setUndoRedoState', 'no_more_undo', {
          root: true,
        })
      } else if (['ERROR_NO_MORE_ACTIONS_TO_REDO'].includes(e.handler.code)) {
        await dispatch('notification/setUndoRedoState', 'no_more_redo', {
          root: true,
        })
      } else {
        throw e
      }
    } finally {
      hideTimeout = setTimeout(
        () =>
          dispatch('notification/setUndoRedoState', 'hidden', { root: true }),
        2000
      )
      commit(commitName, false)
    }
  },
}

export const getters = {
  isUndoing(state) {
    return state.undoing
  },
  isRedoing(state) {
    return state.redoing
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
