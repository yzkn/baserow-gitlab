import bufferedRows from '@baserow/modules/database/store/view/bufferedRows'
import fieldOptions from '@baserow/modules/database/store/view/fieldOptions'
import GalleryService from '@baserow/modules/database/services/view/gallery'

export function populateRow(row) {
  row._ = {}
  return row
}

const galleryBufferedRows = bufferedRows({
  service: GalleryService,
  populateRow,
  fetchInitialRowsArguments: { includeFieldOptions: true },
  fetchedInitialCallback({ commit }, data) {
    commit('REPLACE_ALL_FIELD_OPTIONS', data.field_options)
  },
})

const galleryFieldOptions = fieldOptions()

export const state = () => ({
  ...galleryBufferedRows.state(),
  ...galleryFieldOptions.state(),
})

export const mutations = {
  ...galleryBufferedRows.mutations,
  ...galleryFieldOptions.mutations,
}

export const actions = {
  ...galleryBufferedRows.actions,
  ...galleryFieldOptions.actions,
}

export const getters = {
  ...galleryBufferedRows.getters,
  ...galleryFieldOptions.getters,
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
