<template>
  <div>
    <Notifications></Notifications>
    <div :class="{ 'layout--collapsed': isCollapsed }" class="layout">
      <div class="layout__col-1">
        <Sidebar></Sidebar>
      </div>
      <div class="layout__col-2">
        <nuxt />
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import Notifications from '@baserow/modules/core/components/notifications/Notifications'
import Sidebar from '@baserow/modules/core/components/sidebar/Sidebar'

export default {
  components: {
    Notifications,
    Sidebar,
  },
  middleware: ['settings', 'authenticated', 'groupsAndApplications'],
  computed: {
    ...mapGetters({
      isCollapsed: 'sidebar/isCollapsed',
    }),
  },
  mounted() {
    // Connect to the web socket so we can start receiving real time updates.
    this.$realtime.connect()
    this.$el.keydownEvent = (event) => this.keyDown(event)
    document.body.addEventListener('keydown', this.$el.keydownEvent)
  },
  beforeDestroy() {
    this.$realtime.disconnect()
    document.body.removeEventListener('keydown', this.$el.keydownEvent)
  },
  methods: {
    keyDown(event) {
      if (
        // Temporarily check if the undo redo is enabled.
        !!this.$env.ENABLE_UNDO_REDO &&
        event.metaKey &&
        event.code === 'KeyZ' &&
        // If the active element is the body, it means that we're not focussing on
        // other (text) inputs that have their own undo action. This will prevent the
        // undo redo functionality while editing a cell directly.
        document.body === document.activeElement
      ) {
        event.shiftKey ? this.redo() : this.undo()
      }
    },
    // The two methods below are temporarily and for demo purposes.
    undo() {
      if (this.$store.getters['notification/undoRedoState'] !== 'hidden') {
        return
      }

      this.$store.dispatch('notification/setUndoRedoState', 'undoing')
      setTimeout(() => {
        const r = Math.floor(Math.random() * 4 + 1)
        if (r === 1) {
          this.$store.dispatch('notification/setUndoRedoState', 'no_more_undo')
        } else {
          this.$store.dispatch('notification/setUndoRedoState', 'undone')
        }
        this.undoLoading = false
        setTimeout(() => {
          this.$store.dispatch('notification/setUndoRedoState', 'hidden')
        }, 2000)
      }, 1000)
    },
    redo() {
      if (this.$store.getters['notification/undoRedoState'] !== 'hidden') {
        return
      }

      this.$store.dispatch('notification/setUndoRedoState', 'redoing')
      setTimeout(() => {
        const r = Math.floor(Math.random() * 4 + 1)
        if (r === 1) {
          this.$store.dispatch('notification/setUndoRedoState', 'no_more_redo')
        } else {
          this.$store.dispatch('notification/setUndoRedoState', 'redone')
        }
        this.redoLoading = false
        setTimeout(() => {
          this.$store.dispatch('notification/setUndoRedoState', 'hidden')
        }, 2000)
      }, 1000)
    },
  },
}
</script>
