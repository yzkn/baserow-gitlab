import UndoService from '@baserow/modules/core/services/undo'
import { notifyIf } from '@baserow/modules/core/utils/error'
export default {
  data() {
    return {
      undoLoading: false,
      redoLoading: false,
    }
  },
  methods: {
    async undo(showLoadingPopup = true) {
      if (this.$store.getters['notification/undoRedoState'] !== 'hidden') {
        return
      }

      if (showLoadingPopup) {
        await this.$store.dispatch('notification/setUndoRedoState', 'undoing')
      }
      this.undoLoading = true
      this.redoLoading = false
      try {
        await UndoService(this.$client).undo('root')
        await this.$store.dispatch('notification/setUndoRedoState', 'undone')
      } catch (e) {
        if (['ERROR_NO_MORE_ACTIONS_TO_UNDO'].includes(e.handler.code)) {
          await this.$store.dispatch(
            'notification/setUndoRedoState',
            'no_more_undo'
          )
        } else {
          notifyIf(e, 'application')
        }
      }
      this.undoLoading = false
      setTimeout(() => {
        this.$store.dispatch('notification/setUndoRedoState', 'hidden')
      }, 2000)
    },
    async redo(showLoadingPopup = true) {
      if (this.$store.getters['notification/undoRedoState'] !== 'hidden') {
        return
      }

      if (showLoadingPopup) {
        await this.$store.dispatch('notification/setUndoRedoState', 'redoing')
      }
      this.undoLoading = false
      this.redoLoading = true
      try {
        await UndoService(this.$client).redo('root')
        await this.$store.dispatch('notification/setUndoRedoState', 'redone')
      } catch (e) {
        if (['ERROR_NO_MORE_ACTIONS_TO_REDO'].includes(e.handler.code)) {
          await this.$store.dispatch(
            'notification/setUndoRedoState',
            'no_more_redo'
          )
        } else {
          notifyIf(e, 'application')
        }
      }
      this.redoLoading = false
      setTimeout(() => {
        this.$store.dispatch('notification/setUndoRedoState', 'hidden')
      }, 2000)
    },
  },
}
