import Vue from 'vue'

export default ({
  service,
  populateRow,
  fetchInitialRowsArguments = {},
  fetchedInitialCallback = function () {},
}) => {
  const state = () => ({
    // If another visible rows action has been dispatched while fetching rows, the
    // requested is temporarily delayed and the parameters are stored here.
    delayedRequest: null,
    // Holds the last requested start and end index of the currently visible rows
    visible: [0, 0],
    requestSize: 100,
    viewId: -1,
    fetching: false,
    rows: [],
  })

  const mutations = {
    SET_DELAYED_REQUEST(state, delayedRequestParameters) {
      state.delayedRequest = delayedRequestParameters
    },
    SET_VISIBLE(state, { startIndex, endIndex }) {
      state.visible[0] = startIndex
      state.visible[1] = endIndex
    },
    SET_VIEW_ID(state, viewId) {
      state.viewId = viewId
    },
    SET_ROWS(state, rows) {
      Vue.set(state, 'rows', rows)
    },
    SET_FETCHING(state, value) {
      state.fetching = value
    },
    UPDATE_ROWS(state, { offset, rows }) {
      for (let i = 0; i < rows.length; i++) {
        const rowStoreIndex = i + offset
        const rowInStore = state.rows[rowStoreIndex]
        const row = rows[i]

        if (rowInStore === undefined || rowInStore === null) {
          // If the row doesn't yet exist in the store, we can populate the provided
          // row and set it.
          state.rows.splice(rowStoreIndex, 1, populateRow(row))
        } else {
          // If the row does exist in the store, we can extend it with the provided
          // data of the provided row so the state won't be lost.
          Object.assign(state.rows[rowStoreIndex], row)
        }
      }
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
    /**
     * Should be called when the different rows are displayed to the user. It will
     * figure out which rows have not been loaded and will make a request with the
     * backend to replace to missing ones.
     *
     * @param startIndex
     * @param endIndex
     */
    async visibleRows({ dispatch, getters, commit }, parameters) {
      const { startIndex, endIndex } = parameters

      // If the store is already fetching a set of pages, we don't want to do
      // anything because when the fetching is complete it's going to check if
      // another set of rows must be fetched.
      if (getters.getFetching) {
        commit('SET_DELAYED_REQUEST', parameters)
        return
      }

      const currentVisible = getters.getVisible

      // Check if the currently visible range isn't to same as the provided one
      // because we don't want to do anything in that case.
      if (currentVisible[0] === startIndex && currentVisible[1] === endIndex) {
        return
      }

      commit('SET_VISIBLE', { startIndex, endIndex })
      const allRows = getters.getRows
      const visibleRows = allRows.slice(startIndex, endIndex + 1)

      // If all of the visible rows have been fetched, we don't have to do anything.
      const firstNullIndex = visibleRows.findIndex((row) => row === null)
      const lastNullIndex = visibleRows.lastIndexOf(null)
      if (firstNullIndex === -1) {
        return
      }

      // Figure out what the request size is. In almost all cases this is going to
      // be the configured request size, but it could be that more rows are visible
      // and in that case we want to fetch enough rows.
      const requestSize = Math.max(
        startIndex - endIndex,
        getters.getRequestSize
      )
      let offset = startIndex + firstNullIndex
      let limit = lastNullIndex - firstNullIndex + 1
      let check = 'next'

      // Because we have an ideal request size and this is often higher than the
      // visible rows, we want to efficiently fetch additional rows that are close
      // to the visible range.
      while (limit < requestSize) {
        const previous = allRows[offset - 1]
        const next = allRows[offset + limit + 1]

        // If both the previous and next item are not `null`, which means there is
        // no un-fetched row before or after the range anymore, we want to stop the for
        // loop because there is nothing to fetch.
        if (previous !== null && next !== null) {
          break
        }

        if (check === 'next') {
          check = 'previous'
          if (next === null) {
            limit += 1
          }
        } else if (check === 'previous') {
          check = 'next'
          if (previous === null) {
            offset -= 1
            limit += 1
          }
        }
      }

      // If the limit is zero, it means that there aren't any rows to fetch, so
      // we will stop immediately.
      if (limit === 0) {
        return
      }

      // We can only make one request at the same time, so when we're going to make
      // a request, to set the fetching state to `true` to prevent multiple requests
      // being fired simultaneously.
      commit('SET_FETCHING', true)

      const viewId = getters.getViewId
      const { data } = await service(this.$client).fetchRows({
        viewId,
        offset,
        limit,
      })
      commit('UPDATE_ROWS', {
        offset,
        rows: data.results,
      })

      // Check if another `visibleRows` action has been dispatched while we're
      // fetching the rows. If so, we need to dispatch the same action again with
      // the new parameters. Nothing will be done if the visible start and index
      // haven't changed.
      commit('SET_FETCHING', false)
      const delayedRequestParameters = getters.getDelayedRequest
      if (delayedRequestParameters !== null) {
        commit('SET_DELAYED_REQUEST', null)
        await dispatch('visibleRows', delayedRequestParameters)
      }
    },
  }

  const getters = {
    getDelayedRequest(state) {
      return state.delayedRequest
    },
    getVisible(state) {
      return state.visible
    },
    getRequestSize(state) {
      return state.requestSize
    },
    getFetching(state) {
      return state.fetching
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
