<template>
  <form @submit.prevent="submit">
    <div class="control">
      <label class="control__label">
        <i class="fas fa-font"></i>
        {{ $t('applicationForm.nameLabel') }}
      </label>
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input--error': $v.values.name.$error }"
          type="text"
          class="input input--large"
          @blur="$v.values.name.$touch()"
        />
        <div v-if="$v.values.name.$error" class="error">
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </div>
    <div class="control">
      <label class="control__label">
        {{ $t('databaseForm.importLabel') }}
      </label>
      <div class="control__elements">
        <ul class="choice-items">
          <li>
            <a
              class="choice-items__link"
              :class="{ active: values.import === 'none' }"
              @click="values.import = 'none'"
            >
              <i class="choice-items__icon fas fa-clone"></i>
              {{ $t('databaseForm.emptyLabel') }}
            </a>
          </li>
          <li>
            <a
              class="choice-items__link"
              :class="{ active: values.import === 'airtable' }"
              @click="values.import = 'airtable'"
            >
              <i class="choice-items__icon fas fa-clone"></i>
              {{ $t('databaseForm.airtableLabel') }}
            </a>
          </li>
        </ul>
      </div>
    </div>
    <div v-if="values.import === 'airtable'" class="control">
      <label class="control__label">
        {{ $t('databaseForm.airtableShareLinkTitle') }}
      </label>
      <p class="margin-bottom-2">
        {{ $t('databaseForm.airtableShareLinkDescription') }}
        <br /><br />
        {{ $t('databaseForm.airtableShareLinkBeta') }}
      </p>
      <div class="control__elements">
        <input
          ref="airtableLink"
          v-model="values.airtableLink"
          :class="{ 'input--error': $v.values.airtableLink.$error }"
          type="text"
          class="input input--large"
          :placeholder="$t('databaseForm.airtableShareLinkPaste')"
          @blur="$v.values.airtableLink.$touch()"
        />
        <div v-if="$v.values.airtableLink.$error" class="error">
          @TODO error
        </div>
      </div>
    </div>
    <slot></slot>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'DatabaseForm',
  mixins: [form],
  data() {
    return {
      values: {
        name: '',
        import: 'none',
        airtableLink: '',
      },
    }
  },
  mounted() {
    this.$refs.name.focus()
  },
  validations: {
    values: {
      name: { required },
      import: { required },
      airtableLink: {
        valid() {
          if (this.values.import !== 'airtable') {
            return true
          } else {
            return false
          }
        },
      },
    },
  },
}
</script>
