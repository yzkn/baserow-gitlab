import Vue from 'vue'
import axios from 'axios'
import { RefreshCancelledError } from '@baserow/modules/core/errors'
import { clone } from '@baserow/modules/core/utils/object'
import {
  getRowSortFunction,
  matchSearchFilters,
} from '@baserow/modules/database/utils/view'

export default ({
  service,
  populateRow,
  fetchInitialRowsArguments = {},
  fetchedInitialCallback = function () {},
}) => {
  let lastRequestSource = null

  /**
   * This helper function calculates the most optimal `limit` `offset` range of rows
   * that must be fetched. Based on the provided visible `startIndex` and `endIndex`
   * we know which rows must be fetched because those values are `null` in the
   * provided `rows` array. If a request must be made, we want to do so in the most
   * efficient manner, so we want to respect the ideal request size by filling up
   * the request with other before and after the range that must also be fetched.
   * This function checks if there are other `null` rows close to the range and if
   * so, it tries to include them in the range.
   *
   * @param rows        An array containing the rows that we have fetched already.
   * @param requestSize The ideal request when making a request to the server.
   * @param startIndex  The start index of the visible rows.
   * @param endIndex    The end index of the visible rows.
   */
  const getRangeToFetch = (rows, requestSize, startIndex, endIndex) => {
    const visibleRows = rows.slice(startIndex, endIndex + 1)

    const firstNullIndex = visibleRows.findIndex((row) => row === null)
    const lastNullIndex = visibleRows.lastIndexOf(null)

    // If all of the visible rows have been fetched, so none of them are `null`, we
    // don't have to do anything.
    if (firstNullIndex === -1) {
      return
    }

    // Figure out what the request size is. In almost all cases this is going to
    // be the configured request size, but it could be that more rows must be visible
    // and in that case we want to increase it
    const maxRequestSize = Math.max(startIndex - endIndex, requestSize)

    // The initial offset can be the first `null` found in the range.
    let offset = startIndex + firstNullIndex
    let limit = lastNullIndex - firstNullIndex + 1
    let check = 'next'

    // Because we have an ideal request size and this is often higher than the
    // visible rows, we want to efficiently fetch additional rows that are close
    // to the visible range.
    while (limit < maxRequestSize) {
      const previous = rows[offset - 1]
      const next = rows[offset + limit + 1]

      // If both the previous and next item are not `null`, which means there is
      // no un-fetched row before or after the range anymore, we want to stop the for
      // loop because there is nothing to fetch.
      if (previous !== null && next !== null) {
        break
      }

      if (check === 'next') {
        check = 'previous'
        // If the next element is null, we want to include that in the range to be
        // fetched.
        if (next === null) {
          limit += 1
        }
      } else if (check === 'previous') {
        check = 'next'
        // If the previous element is null, we want to include that in the range to
        // be fetched.
        if (previous === null) {
          offset -= 1
          limit += 1
        }
      }
    }

    return { offset, limit }
  }

  const state = () => ({
    // If another visible rows action has been dispatched while fetching rows, the
    // requested is temporarily delayed and the parameters are stored here.
    delayedRequest: null,
    // Holds the last requested start and end index of the currently visible rows
    visible: [0, 0],
    // Contains the ideal size of rows that's being fetched when making a request.
    requestSize: 100,
    // The current view id.
    viewId: -1,
    // Indicates whether the store is currently fetching another batch of rows.
    fetching: false,
    // A list of all the rows in the table. The ones that haven't been fetched yet
    // are `null`.
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
    INSERT_ROW_AT_INDEX(state, { index, row }) {
      state.rows.splice(index, 0, row)
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
     * Should be called when the different rows are displayed to the user. This
     * could for example happen when a user scrolls. It will figure out which rows
     * have not been fetched and will make a request with the backend to replace to
     * missing ones if needed.
     */
    async visibleRows({ dispatch, getters, commit }, parameters) {
      const { startIndex, endIndex } = parameters

      // If the store is already fetching a set of pages, we're temporarily storing
      // the parameters so that this action can be dispatched again with the latest
      // parameters.
      if (getters.getFetching) {
        commit('SET_DELAYED_REQUEST', parameters)
        return
      }

      // Check if the currently visible range isn't to same as the provided one
      // because we don't want to do anything in that case.
      const currentVisible = getters.getVisible
      if (currentVisible[0] === startIndex && currentVisible[1] === endIndex) {
        return
      }

      // Update the last visible range to make sure this action isn't dispatched
      // multiple times.
      commit('SET_VISIBLE', { startIndex, endIndex })

      // Check what the ideal range is to fetch with the backend.
      const rangeToFetch = getRangeToFetch(
        getters.getRows,
        getters.getRequestSize,
        startIndex,
        endIndex
      )

      // If there is no ideal range or if the limit is 0, then there aren't any rows
      // to fetch so we can stop.
      if (rangeToFetch === undefined || rangeToFetch.limit === 0) {
        return
      }

      // We can only make one request at the same time, so we're going to to set the
      // fetching state to `true` to prevent multiple requests being fired
      // simultaneously.
      commit('SET_FETCHING', true)
      lastRequestSource = axios.CancelToken.source()
      try {
        const { data } = await service(this.$client).fetchRows({
          viewId: getters.getViewId,
          offset: rangeToFetch.offset,
          limit: rangeToFetch.limit,
          cancelToken: lastRequestSource.token,
        })
        commit('UPDATE_ROWS', {
          offset: rangeToFetch.offset,
          rows: data.results,
        })
      } catch (error) {
        if (axios.isCancel(error)) {
          throw new RefreshCancelledError()
        } else {
          lastRequestSource = null
          throw error
        }
      } finally {
        // Check if another `visibleRows` action has been dispatched while we were
        // fetching the rows. If so, we need to dispatch the same action again with
        // the latest parameters.
        commit('SET_FETCHING', false)
        const delayedRequestParameters = getters.getDelayedRequest
        if (delayedRequestParameters !== null) {
          commit('SET_DELAYED_REQUEST', null)
          await dispatch('visibleRows', delayedRequestParameters)
        }
      }
    },
    /**
     * Refreshes the current visible page by clearing all the rows in the store and
     * fetching the currently visible rows. This is typically done when a filter has
     * changed and we can't trust what's in the store anymore.
     */
    async refresh(
      { dispatch, commit, getters },
      { fields, primary, includeFieldOptions = false }
    ) {
      // If another refresh or fetch request is currently running, we need to cancel
      // them because the response is most likely going to be outdated and we don't
      // need it anymore.
      if (lastRequestSource !== null) {
        lastRequestSource.cancel('Cancelled in favor of new request')
      }

      lastRequestSource = axios.CancelToken.source()

      try {
        // We first need to fetch the count of all rows because we need to know how
        // many rows there are in total to estimate what are new visible range it
        // going to be.
        commit('SET_FETCHING', true)
        const {
          data: { count },
        } = await service(this.$client).fetchCount({
          viewId: getters.getViewId,
          cancelToken: lastRequestSource.token,
        })

        // Create a new empty array containing un-fetched rows.
        const rows = Array(count).fill(null)
        let startIndex = 0
        let endIndex = 0

        if (count > 0) {
          // Figure out which range was previous visible and see if that still fits
          // within the new set of rows. Otherwise we're going to fall
          const currentVisible = getters.getVisible
          startIndex = currentVisible[0]
          endIndex = currentVisible[1]
          const difference = count - endIndex

          if (difference < 0) {
            startIndex += difference
            endIndex += difference
          }

          // Based on the newly calculated range we can figure out which rows we want
          // to fetch from the backend to populate our store with. These should be the
          // rows that the user is going to look at.
          const rangeToFetch = getRangeToFetch(
            rows,
            getters.getRequestSize,
            startIndex,
            endIndex
          )

          // Only fetch visible rows if there are any.
          const {
            data: { results },
          } = await service(this.$client).fetchRows({
            viewId: getters.getViewId,
            offset: rangeToFetch.offset,
            limit: rangeToFetch.limit,
            includeFieldOptions,
            cancelToken: lastRequestSource.token,
          })

          results.forEach((row, index) => {
            rows[rangeToFetch.offset + index] = populateRow(row)
          })
        }

        commit('SET_ROWS', rows)
        commit('SET_VISIBLE', { startIndex, endIndex })
      } catch (error) {
        if (axios.isCancel(error)) {
          throw new RefreshCancelledError()
        } else {
          lastRequestSource = null
          throw error
        }
      } finally {
        commit('SET_FETCHING', false)
      }
    },
    /**
     * Check if the provided row matches the provided view filters.
     */
    rowMatchesFilters(context, { view, fields, primary, row, overrides = {} }) {
      const values = JSON.parse(JSON.stringify(row))
      Object.assign(values, overrides)

      // The value is always valid if the filters are disabled.
      return view.filters_disabled
        ? true
        : matchSearchFilters(
            this.$registry,
            view.filter_type,
            view.filters,
            primary === null ? fields : [primary, ...fields],
            values
          )
    },
    /**
     * When a new row is created and it doesn't yet in exists in this store, it must
     * be added at the right position. Based on the values of the row we can
     * calculate if the row should be added (matches filters) and at which position
     * (sortings).
     *
     * Because we only fetch the rows from the backend that are actually needed, it
     * could be that we can't figure out what the exact position of the row should
     * be. In that case, we add a `null` in the area that is unknown. The store
     * already has other null values for rows that are un-fetched. So the un-fetched
     * row representations that are `null` in the array will be fetched automatically
     * when the user wants to see them.
     */
    createdNewRow(
      { dispatch, getters, commit },
      { view, fields, primary, values }
    ) {
      let row = clone(values)
      populateRow(row)

      // Check if the row matches the filters. If not, we don't have to do anything.
      if (!dispatch('rowMatchesFilters', { view, fields, primary, row })) {
        return
      }

      const sortFunction = getRowSortFunction(
        this.$registry,
        view.sortings,
        fields,
        primary
      )
      const allRows = getters.getRows
      let newIndex = allRows.findIndex((existingRow) => {
        return existingRow !== null && sortFunction(row, existingRow) < 0
      })

      if (newIndex === -1 && allRows[allRows.length - 1] !== null) {
        // If we don't know where to position the new row and the last row is null, we
        // can safely assume it's the last row because when finding the index we
        // only check if the new row is before an existing row.
        newIndex = allRows.length
      } else if (newIndex === -1) {
        // If we don't know where to position the new row we can assume near the
        // end, but we're not sure where exactly. Because of that we'll add it as
        // null to the end.
        newIndex = allRows.length
        row = null
      } else if (allRows[newIndex - 1] === null) {
        // If the row must inserted at the beginning of a known chunk of fetched
        // rows, we can't know for sure it actually has to be inserted directly before.
        // In that case, we will insert it as null.
        row = null
      }

      commit('INSERT_ROW_AT_INDEX', { index: newIndex, row })
    },
    // updatedExistingRow({}, { view, fields, primary, row, values }) {},
    // deletedExistingRow({}, { view, fields, primary, row }) {},
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
