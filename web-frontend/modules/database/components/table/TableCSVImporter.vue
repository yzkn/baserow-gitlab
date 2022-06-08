<template>
  <div>
    <div class="control">
      <label class="control__label">{{
        $t('tableCSVImporter.chooseFileLabel')
      }}</label>
      <div class="control__description">
        {{ $t('tableCSVImporter.chooseFileDescription') }}
      </div>
      <div class="control__elements">
        <div class="file-upload">
          <input
            v-show="false"
            ref="file"
            type="file"
            accept=".csv"
            @change="select($event)"
          />
          <a
            class="button button--large button--ghost file-upload__button"
            @click.prevent="$refs.file.click($event)"
          >
            <i class="fas fa-cloud-upload-alt"></i>
            {{ $t('tableCSVImporter.chooseFile') }}
          </a>
          <div class="file-upload__file">{{ filename }}</div>
        </div>
        <div v-if="$v.filename.$error" class="error">
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </div>
    <div
      v-if="showLoadingMessage"
      class="alert alert--simple alert--with-shadow alert--has-icon"
    >
      <div class="alert__icon">
        <div class="loading alert__icon-loading"></div>
      </div>
      <div class="alert__title">
        {{ getLoadingStateTitle }}
      </div>
      <p class="alert__content">
        {{
          `${$t('tableCSVImporter.loadingProgress')} ${fileLoadingProgress}`
        }}%
      </p>
    </div>
    <div v-if="filename !== ''" class="row">
      <div class="col col-4">
        <div class="control">
          <label class="control__label">{{
            $t('tableCSVImporter.columnSeparator')
          }}</label>
          <div class="control__elements">
            <Dropdown v-model="columnSeparator" @input="reload()">
              <DropdownItem name="auto detect" value="auto"></DropdownItem>
              <DropdownItem name="," value=","></DropdownItem>
              <DropdownItem name=";" value=";"></DropdownItem>
              <DropdownItem name="|" value="|"></DropdownItem>
              <DropdownItem name="<tab>" value="\t"></DropdownItem>
              <DropdownItem
                :name="$t('tableCSVImporter.recordSeparator') + ' (30)'"
                :value="String.fromCharCode(30)"
              ></DropdownItem>
              <DropdownItem
                :name="$t('tableCSVImporter.unitSeparator') + ' (31)'"
                :value="String.fromCharCode(31)"
              ></DropdownItem>
            </Dropdown>
          </div>
        </div>
      </div>
      <div class="col col-8">
        <div class="control">
          <label class="control__label">{{
            $t('tableCSVImporter.encoding')
          }}</label>
          <div class="control__elements">
            <CharsetDropdown
              v-model="encoding"
              @input="reload()"
            ></CharsetDropdown>
          </div>
        </div>
      </div>
    </div>
    <div v-if="filename !== ''" class="row">
      <div class="col col-6">
        <div class="control">
          <label class="control__label">{{
            $t('tableCSVImporter.firstRowHeader')
          }}</label>
          <div class="control__elements">
            <Checkbox v-model="values.firstRowHeader" @input="reload()">{{
              $t('common.yes')
            }}</Checkbox>
          </div>
        </div>
      </div>
    </div>
    <div
      v-if="error !== ''"
      class="alert alert--error alert--has-icon margin-top-1"
    >
      <div class="alert__icon">
        <i class="fas fa-exclamation"></i>
      </div>
      <div class="alert__title">{{ $t('common.wrong') }}</div>
      <p class="alert__content">
        {{ error }}
      </p>
    </div>
    <TableImporterPreview
      v-if="error === '' && Object.keys(preview).length !== 0"
      :preview="preview"
    ></TableImporterPreview>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'
import flushPromises from 'flush-promises'

import form from '@baserow/modules/core/mixins/form'
import CharsetDropdown from '@baserow/modules/core/components/helpers/CharsetDropdown'
import importer from '@baserow/modules/database/mixins/importer'
import TableImporterPreview from '@baserow/modules/database/components/table/TableImporterPreview'

export default {
  name: 'TableCSVImporter',
  components: { TableImporterPreview, CharsetDropdown },
  mixins: [form, importer],
  data() {
    return {
      values: {
        data: '',
        firstRowHeader: true,
      },
      filename: '',
      columnSeparator: 'auto',
      encoding: 'utf-8',
      error: '',
      rawData: null,
      preview: {},
      fileLoadingProgress: 0,
      parsing: false,
      state: null,
    }
  },
  validations: {
    values: {
      data: { required },
    },
    filename: { required },
  },
  computed: {
    showLoadingMessage() {
      return this.state === 'loading' || this.state === 'parsing'
    },
    getLoadingStateTitle() {
      return this.$t(`tableCSVImporter.${this.state}`)
    },
  },
  methods: {
    async ensureRender() {
      await this.$nextTick()
      // Wait for the browser had a chance to repaint the UI
      await new Promise((resolve) => requestAnimationFrame(resolve))
      await flushPromises()
    },
    /**
     * Method that is called when a file has been chosen. It will check if the file is
     * not larger than 15MB. Otherwise it will take a long time and possibly a crash
     * if so many entries have to be loaded into memory. If the file is valid, the
     * contents will be loaded into memory and the reload method will be called which
     * parses the content.
     */
    select(event) {
      if (event.target.files.length === 0) {
        return
      }

      const file = event.target.files[0]
      let maxSize = 1024 * 1024 * 15 // 15MB
      if (this.$featureFlags.includes('async_import')) {
        maxSize = 1024 * 1024 * 1024 // 1Gb
      }

      if (file.size > maxSize) {
        this.filename = ''
        this.values.data = ''
        this.error = this.$t('tableCSVImporter.limitFileSize', {
          limit: 15,
        })
        this.preview = {}
        this.$emit('input', this.value)
      } else {
        this.filename = file.name
        const reader = new FileReader()
        this.state = 'loading'
        reader.addEventListener('progress', (event) => {
          this.fileLoadingProgress = Math.floor(
            (event.loaded / event.total) * 100
          )
        })
        reader.addEventListener('load', async (event) => {
          this.rawData = event.target.result
          this.fileLoadingProgress = 100
          this.state = 'parsing'
          await this.ensureRender()
          this.reload()
        })
        reader.readAsArrayBuffer(event.target.files[0])
      }
    },
    /**
     * Parses the raw data with the user configured delimiter. If all looks good the
     * data is stored as a string because all the entries don't have to be reactive.
     * Also a small preview will be generated. If something goes wrong, for example
     * when the CSV doesn't have any entries the appropriate error will be shown.
     */
    async reload() {
      const decoder = new TextDecoder(this.encoding)
      const decodedData = decoder.decode(this.rawData)
      const limit = this.$env.INITIAL_TABLE_DATA_LIMIT
      const count = decodedData.split(/\r\n|\r|\n/).length
      if (limit !== null && count > limit) {
        this.values.data = ''
        this.error = this.$t('tableCSVImporter.limitError', {
          limit,
        })
        this.preview = {}
        return
      }

      // Step 1: Parse first 5 rows to show the preview table
      this.$papa.parse(decodedData, {
        preview: 3,
        delimiter: this.columnSeparator === 'auto' ? '' : this.columnSeparator,
        complete: (data) => {
          if (data.data.length === 0) {
            // We need at least a single entry otherwise the user has probably chosen
            // a wrong file.
            this.values.data = ''
            this.error = this.$t('tableCSVImporter.emptyCSV')
            this.preview = {}
          } else {
            // If parsed successfully and it is not empty then the initial data can be
            // prepared for creating the table. We store the data stringified because
            // it doesn't need to be reactive.
            const dataWithHeader = this.ensureHeaderExistsAndIsValid(
              data.data,
              this.values.firstRowHeader
            )
            this.error = ''
            this.preview = this.getPreview(dataWithHeader)
            this.state = null
            this.parsing = false
            this.fileLoadingProgress = 0
          }
        },
        error(error) {
          // Papa parse has resulted in an error which we need to display to the user.
          // All previously loaded data will be removed.
          this.values.data = ''
          this.error = error.errors[0].message
          this.preview = {}
          this.state = null
          this.parsing = false
          this.fileLoadingProgress = 0
        },
      })

      await this.ensureRender()

      // Step 2: If step 1 hasn't failed, parse the rest of the data
      if (this.error === '') {
        this.$papa.parse(decodedData, {
          delimiter:
            this.columnSeparator === 'auto' ? '' : this.columnSeparator,
          complete: (data) => {
            if (this.values.firstRowHeader) {
              // Only run ensureHeaderExistsAndIsValid on the first row
              // as it can't handle too many rows.
              const dataWithHeader = this.ensureHeaderExistsAndIsValid(
                data.data.slice(0, 1),
                this.values.firstRowHeader
              )
              // Update the header row with the valid header names
              data.data[0] = dataWithHeader[0]
            }
            this.values.data = data.data
          },
          error(error) {
            this.values.data = ''
            this.error = error.errors[0].message
          },
        })
      }
    },
  },
}
</script>
