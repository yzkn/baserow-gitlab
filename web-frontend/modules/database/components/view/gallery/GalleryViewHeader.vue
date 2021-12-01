<template>
  <ul v-if="!tableLoading" class="header__filter header__filter--full-width">
    <li class="header__filter-item">
      <a
        ref="customizeContextLink"
        class="header__filter-link"
        @click="
          $refs.customizeContext.toggle(
            $refs.customizeContextLink,
            'bottom',
            'left',
            4
          )
        "
      >
        <i class="header__filter-icon fas fa-cog"></i>
        <span class="header__filter-name">Customize cards</span>
      </a>
      <ViewFieldsContext
        ref="customizeContext"
        :fields="allFields"
        :read-only="readOnly"
        :field-options="{}"
      ></ViewFieldsContext>
      <!--
      :field-options="fieldOptions"
      @update-all-field-options="updateAllFieldOptions"
      @update-field-options-of-field="updateFieldOptionsOfField"
      @update-order="orderFieldOptions"
      -->
    </li>
  </ul>
</template>

<script>
import { mapState } from 'vuex'

import ViewFieldsContext from '@baserow/modules/database/components/view/ViewFieldsContext'

export default {
  name: 'GalleryViewHeader',
  components: { ViewFieldsContext },
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    primary: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    allFields() {
      return [this.primary].concat(this.fields)
    },
    ...mapState({
      tableLoading: (state) => state.table.loading,
    }),
  },
  // methods: {
  //   async updateAllFieldOptions({ newFieldOptions, oldFieldOptions }) {
  //     try {
  //       await this.$store.dispatch(
  //         this.storePrefix + 'view/kanban/updateAllFieldOptions',
  //         {
  //           newFieldOptions,
  //           oldFieldOptions,
  //         }
  //       )
  //     } catch (error) {
  //       notifyIf(error, 'view')
  //     }
  //   },
  //   async updateFieldOptionsOfField({ field, values, oldValues }) {
  //     try {
  //       await this.$store.dispatch(
  //         this.storePrefix + 'view/kanban/updateFieldOptionsOfField',
  //         {
  //           field,
  //           values,
  //           oldValues,
  //         }
  //       )
  //     } catch (error) {
  //       notifyIf(error, 'view')
  //     }
  //   },
  //   async orderFieldOptions({ order }) {
  //     try {
  //       await this.$store.dispatch(
  //         this.storePrefix + 'view/kanban/updateFieldOptionsOrder',
  //         {
  //           order,
  //         }
  //       )
  //     } catch (error) {
  //       notifyIf(error, 'view')
  //     }
  //   },
  // },
}
</script>
