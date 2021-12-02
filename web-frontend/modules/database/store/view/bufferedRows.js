import Vue from 'vue'

export default ({
  service,
  populateRow,
  fetchInitialRowsArguments = {},
  fetchedInitialCallback = function () {},
}) => {
  const state = () => ({
    requestSize: 100,
    viewId: -1,
    rows: [],
  })

  const mutations = {
    SET_VIEW_ID(state, viewId) {
      state.viewId = viewId
    },
    SET_ROWS(state, rows) {
      Vue.set(state, 'rows', rows)
    },
  }

  const actions = {
    /**
     * This action fetches the initial set of rows via the provided service.
     */
    async fetchInitial(context, { viewId, fields, primary }) {
      const { commit, getters } = context
      commit('SET_VIEW_ID', viewId)
      const { data } = await service(this.$client).fetchRows({
        viewId,
        offset: 0,
        limit: getters.getRequestSize,
        ...fetchInitialRowsArguments,
      })
      const rows = Array(data.count).fill(null)
      data.results.forEach((row, index) => {
        rows[index] = populateRow(row)
      })
      commit('SET_ROWS', rows)
      fetchedInitialCallback(context, data)
    },
  }

  const getters = {
    getRequestSize(state) {
      return state.requestSize
    },
    getRows(state) {
      return state.rows
    },
  }

  return {
    namespaced: true,
    state,
    getters,
    actions,
    mutations,
  }
}
