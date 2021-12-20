<template>
  <div>
    <Notifications></Notifications>
    <div class="form-view__page">
      <Table
        v-if="!tableLoading"
        :database="database"
        :table="table"
        :fields="fields"
        :primary="primary"
        :views="[view]"
        :view="view"
        :table-loading="tableLoading"
        :read-only="true"
        :store-prefix="'page/'"
      ></Table>
    </div>
  </div>
</template>

<script>
import Notifications from '@baserow/modules/core/components/notifications/Notifications'
import { mapGetters } from 'vuex'
import Table from '@baserow/modules/database/components/table/Table'

import ViewService from '@baserow/modules/database/services/view'
export default {
  components: { Notifications, Table },
  data() {
    return {
      database: {},
      table: {},
      view: {},
      tableLoading: true,
    }
  },
  computed: {
    ...mapGetters({
      primary: 'field/getPrimary',
      fields: 'field/getAll',
    }),
  },
  mounted() {
    this.$realtime.connect(true, true)
    this.$realtime.subscribe('view', { slug: this.$route.params.slug })
    this.fetchTable()
  },
  beforeDestroy() {
    this.$realtime.disconnect()
  },
  methods: {
    /**
     * Fetches and prepares all the table, field and view data for the provided
     * database and table.
     */
    async fetchTable() {
      const viewSlug = this.$route.params.slug
      this.tableLoading = true
      // Fetch and prepare the fields of the given table. The primary field is
      // extracted from the array and moved to a separate object because that is what
      // the `Table` components expects.
      const { data } = await ViewService(this.$client).fetchPublic(viewSlug)
      this.database = { id: viewSlug, type: 'database', tables: [] }
      await this.$store.dispatch('page/view/grid/setPublic', true)
      await this.$store.dispatch('application/forceCreate', this.database)
      this.table = { id: viewSlug, database: this.database }
      await this.$store.dispatch('table/forceCreate', {
        database: this.database,
        data: this.table,
      })
      await this.$store.dispatch('table/forceSelect', {
        databaseId: viewSlug,
        tableId: viewSlug,
      })
      await this.$store.dispatch('field/forceCreateFields', {
        table: this.table,
        fields: data.fields,
      })

      await this.$store.dispatch('view/forceCreate', {
        data: data.view,
      })
      this.view = data.view

      // After selecting the table, the user expects to see the table data and that is
      // only possible if a view is selected. By calling the `selectView` method
      // without parameters, the first view is selected.
      await this.selectView(data.view)
    },
    /**
     * Selects the view with the given `viewId`. If no `viewId` is provided, then the
     * first view will be selected.
     */
    async selectView(view) {
      this.tableLoading = true

      await this.$store.dispatch('view/select', view)

      // It might be possible that the view also has some stores that need to be
      // filled with initial data, so we're going to call the fetch function here.
      const type = this.$registry.get('view', view.type)
      await type.fetch(
        { store: this.$store },
        view,
        this.fields,
        this.primary,
        'page/'
      )
      this.tableLoading = false
    },
  },
}
</script>
