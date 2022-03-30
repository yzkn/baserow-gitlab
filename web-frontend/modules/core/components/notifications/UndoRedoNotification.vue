<template>
  <div class="alert alert--simple alert--with-shadow alert--has-icon">
    <div class="alert__icon">
      <div
        v-if="stateContent.loading"
        class="loading alert__icon-loading"
      ></div>
      <i
        v-if="!stateContent.loading"
        class="fas"
        :class="stateContent.icon"
      ></i>
    </div>
    <div class="alert__title">{{ stateContent.title }}</div>
    <p class="alert__content">{{ stateContent.content }}</p>
  </div>
</template>

<script>
export default {
  name: 'UndoRedNotification',
  props: {
    state: {
      type: String,
      required: true,
    },
  },
  computed: {
    stateContent() {
      const base = {
        loading: false,
        icon: '',
        title: '',
        content: '',
      }

      if (this.state === 'undoing') {
        base.loading = true
        base.title = this.$t('undoRedoNotification.undoingTitle')
        base.content = this.$t('undoRedoNotification.undoingText')
      } else if (this.state === 'redoing') {
        base.loading = true
        base.title = this.$t('undoRedoNotification.redoingTitle')
        base.content = this.$t('undoRedoNotification.redoingText')
      } else if (this.state === 'undone') {
        base.icon = 'fa-check'
        base.title = this.$t('undoRedoNotification.undoneTitle')
        base.content = this.$t('undoRedoNotification.undoneText')
      } else if (this.state === 'redone') {
        base.icon = 'fa-check'
        base.title = this.$t('undoRedoNotification.redoneTitle')
        base.content = this.$t('undoRedoNotification.redoneText')
      } else if (this.state === 'no_more_undo') {
        base.icon = 'fa-times'
        base.title = this.$t('undoRedoNotification.failed')
        base.content = this.$t('undoRedoNotification.noMoreUndo')
      } else if (this.state === 'no_more_redo') {
        base.icon = 'fa-times'
        base.title = this.$t('undoRedoNotification.failed')
        base.content = this.$t('undoRedoNotification.noMoreRedo')
      }

      return base
    },
  },
}
</script>
