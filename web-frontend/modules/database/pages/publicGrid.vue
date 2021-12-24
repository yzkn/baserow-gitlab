<template>
  <div>
    <Notifications></Notifications>
    <div class="public-view__page">
      <Table
        :database="database"
        :table="table"
        :fields="fields"
        :primary="primary"
        :views="[view]"
        :view="view"
        :read-only="true"
        :table-loading="tableLoading"
        :store-prefix="'page/'"
      ></Table>
    </div>
  </div>
</template>

<script>
import Notifications from '@baserow/modules/core/components/notifications/Notifications'
import { mapState } from 'vuex'
import Table from '@baserow/modules/database/components/table/Table'

import GridService from '@baserow/modules/database/services/view/grid'
import { PUBLIC_PLACEHOLDER_ENTITY_ID } from '@baserow/modules/database/utils/constants'
export default {
  components: { Notifications, Table },
  /**
   * Fetches and prepares all the table, field and view data for the provided
   * public grid view.
   */
  async asyncData({ store, params, error, app }) {
    try {
      const viewSlug = params.slug
      // Fetch and prepare the fields of the given table. The primary field is
      // extracted from the array and moved to a separate object because that is what
      // the `Table` components expects.
      const { data } = await GridService(app.$client).fetchPublic(viewSlug)
      const database = {
        id: PUBLIC_PLACEHOLDER_ENTITY_ID,
        type: 'database',
        tables: [],
      }
      await store.dispatch('page/view/grid/setPublic', true)
      await store.dispatch('application/forceCreate', database)
      const table = { id: PUBLIC_PLACEHOLDER_ENTITY_ID, database }
      await store.dispatch('table/forceCreate', {
        database,
        data: table,
      })
      await store.dispatch('table/forceSelect', {
        databaseId: PUBLIC_PLACEHOLDER_ENTITY_ID,
        tableId: PUBLIC_PLACEHOLDER_ENTITY_ID,
      })
      await store.dispatch('field/forceCreateFields', {
        table,
        fields: data.fields,
      })

      await store.dispatch('view/forceCreate', {
        data: data.view,
      })
      const view = data.view

      await store.dispatch('view/select', view)
      const fields = store.getters['field/getAll']
      const primary = store.getters['field/getPrimary']

      // It might be possible that the view also has some stores that need to be
      // filled with initial data, so we're going to call the fetch function here.
      const type = app.$registry.get('view', view.type)
      await type.fetch({ store }, view, fields, primary, 'page/')
      return {
        primary,
        fields,
        database,
        table,
        view,
      }
    } catch (e) {
      if (e.response && e.response.status === 404) {
        return error({ statusCode: 404, message: 'View not found.' })
      } else {
        console.log(e)
        return error({ statusCode: 500, message: 'Error loading view.' })
      }
    }
  },
  computed: {
    ...mapState({
      tableLoading: (state) => state.table.loading,
    }),
  },
}
</script>
