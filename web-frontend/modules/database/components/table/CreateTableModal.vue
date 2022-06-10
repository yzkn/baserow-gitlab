<template>
  <Modal>
    <h2 class="box__title">{{ $t('createTableModal.title') }}</h2>
    <Error :error="error"></Error>
    <TableForm ref="tableForm" @submitted="submitted">
      <div class="control">
        <label class="control__label">
          {{ $t('createTableModal.importLabel') }}
        </label>
        <div class="control__elements">
          <ul class="choice-items">
            <li>
              <a
                class="choice-items__link"
                :class="{ active: importer === '' }"
                @click="importer = ''"
              >
                <i class="choice-items__icon fas fa-clone"></i>
                {{ $t('createTableModal.newTable') }}
              </a>
            </li>
            <li v-for="importerType in importerTypes" :key="importerType.type">
              <a
                class="choice-items__link"
                :class="{ active: importer === importerType.type }"
                @click="importer = importerType.type"
              >
                <i
                  class="choice-items__icon fas"
                  :class="'fa-' + importerType.iconClass"
                ></i>
                {{ importerType.getName() }}
              </a>
            </li>
          </ul>
        </div>
      </div>
      <component :is="importerComponent" />
      <div class="modal-progress__actions">
        <div v-if="loading" class="modal-progress__loading-bar">
          <div
            class="modal-progress__loading-bar-inner"
            :style="{
              width: `${progressPercentage}%`,
              'transition-duration': [1, 0].includes(progressPercentage)
                ? '0s'
                : '1s',
            }"
          ></div>
          <span class="modal-progress__status-text"
            >{{ `${progressPercentage}%` }}
            {{ humanReadableStateWithUpload }}</span
          >
        </div>
        <div class="align-right">
          <button
            class="button button--large"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
          >
            {{ $t('createTableModal.addButton') }}
          </button>
        </div>
      </div>
    </TableForm>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import jobProgress from '@baserow/modules/core/mixins/jobProgress'

import JobService from '@baserow/modules/core/services/job'
import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'
import TableForm from './TableForm'

export default {
  name: 'CreateTableModal',
  components: { TableForm },
  mixins: [modal, error, jobProgress],
  props: {
    application: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      importer: '',
      uploadProgressPercentage: 0,
      table: null,
    }
  },
  computed: {
    progressPercentage() {
      let progress = 0
      if (this.job === null) {
        progress = this.uploadProgressPercentage / 2
      } else {
        progress = 50 + Math.floor(this.job.progress_percentage / 2)
      }
      return Math.floor(progress)
    },
    importerTypes() {
      return this.$registry.getAll('importer')
    },
    importerComponent() {
      return this.importer === ''
        ? null
        : this.$registry.get('importer', this.importer).getFormComponent()
    },
    humanReadableStateWithUpload() {
      if (this.job === null) {
        return this.$t('createTableModal.uploading')
      } else {
        return this.humanReadableState
      }
    },
  },
  beforeDestroy() {
    this.stopPollIfRunning()
  },
  methods: {
    hide(...args) {
      modal.methods.hide.call(this, ...args)
      this.importer = ''
    },
    /**
     * When the form is submitted we try to extract the initial data and first row
     * header setting from the values. An importer could have added those, but they
     * need to be removed from the values.
     */
    async submitted(values) {
      this.uploadProgressPercentage = 0
      this.loading = true
      this.hideError()

      let firstRowHeader = false
      let data = null

      if (Object.prototype.hasOwnProperty.call(values, 'firstRowHeader')) {
        firstRowHeader = values.firstRowHeader
        delete values.firstRowHeader
      }

      if (Object.prototype.hasOwnProperty.call(values, 'data')) {
        data = JSON.parse(values.data)
        delete values.data
      }

      try {
        const table = await this.$store.dispatch('table/create', {
          database: this.application,
          values,
          initialData: data,
          firstRowHeader,
          onUploadProgress: ({ loaded, total }) =>
            (this.uploadProgressPercentage = (loaded / total) * 100),
        })
        this.table = table

        const jobId = table.import_jobs[0]
        const { data: job } = await JobService(this.$client).get(jobId)
        this.job = job
        this.launchJobPoller()
      } catch (error) {
        this.loading = false
        this.uploadProgressPercentage = 0
        this.stopPollAndHandleError(error, {
          ERROR_MAX_JOB_COUNT_EXCEEDED: new ResponseErrorMessage(
            this.$t('job.errorJobAlreadyRunningTitle'),
            this.$t('job.errorJobAlreadyRunningDescription')
          ),
        })
      }
    },
    onJobDone() {
      // Redirect to the newly created table.
      this.$nuxt.$router.push({
        name: 'database-table',
        params: {
          databaseId: this.application.id,
          tableId: this.job.table_id,
        },
      })
      this.loading = false
      this.uploadProgressPercentage = 0
      this.hide()
    },
    onJobFailure() {
      const error = new ResponseErrorMessage(
        this.$t('createTableModal.importError'),
        this.job.human_readable_error
      )
      this.stopPollAndHandleError(error)
    },
    onJobError(error) {
      this.stopPollAndHandleError(error)
    },
    stopPollAndHandleError(error, specificErrorMap = null) {
      this.loading = false
      this.uploadProgressPercentage = 0
      this.stopPollIfRunning()
      error.handler
        ? this.handleError(error, 'application', specificErrorMap)
        : this.showError(error)
    },
  },
}
</script>
