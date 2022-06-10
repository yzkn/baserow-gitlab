import JobService from '@baserow/modules/core/services/job'

export default {
  data() {
    return {
      job: null,
      pollInterval: null,
    }
  },
  computed: {
    jobHasSucceeded() {
      return this.job?.state === 'finished'
    },
    jobIsRunning() {
      return !['failed', 'finished'].includes(this.job?.state)
    },
    jobHasFailed() {
      return this.job?.state === 'failed'
    },
    humanReadableState() {
      if (this.job === null) {
        return ''
      }
      const translations = {
        pending: this.$t('job.statePending'),
        failed: this.$t('job.stateFailed'),
        finished: this.$t('job.stateFinished'),
      }
      if (translations[this.job.state]) {
        return translations[this.job.state]
      }
      return this.$t(`customJobState.${this.job.type}.${this.job.state}`)
    },
  },
  methods: {
    launchJobPoller() {
      this.pollInterval = setInterval(this.getLatestJobInfo, 2000)
    },
    async getLatestJobInfo() {
      try {
        const { data } = await JobService(this.$client).get(this.job.id)
        this.job = data
        if (this.jobHasFailed) {
          this.stopPollIfRunning()
          await this.onJobFailure()
        } else if (!this.jobIsRunning) {
          this.stopPollIfRunning()
          await this.onJobDone()
        }
      } catch (error) {
        this.onJobError(error)
      } finally {
        this.job = null
      }
    },
    stopPollIfRunning() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval)
      }
    },
  },
}
