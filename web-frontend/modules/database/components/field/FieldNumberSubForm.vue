<template>
  <div>
    <div class="control">
      <label class="control__label control__label--small">{{
        $t('fieldNumberSubForm.decimalPlacesLabel')
      }}</label>
      <div class="control__elements">
        <Dropdown
          v-model="values.number_decimal_places"
          :class="{ 'dropdown--error': $v.values.number_decimal_places.$error }"
          @hide="$v.values.number_decimal_places.$touch()"
        >
          <DropdownItem name="0 (1)" :value="0"></DropdownItem>
          <DropdownItem name="1 (1.0)" :value="1"></DropdownItem>
          <DropdownItem name="2 (1.00)" :value="2"></DropdownItem>
          <DropdownItem name="3 (1.000)" :value="3"></DropdownItem>
          <DropdownItem name="4 (1.0000)" :value="4"></DropdownItem>
          <DropdownItem name="5 (1.00000)" :value="5"></DropdownItem>
        </Dropdown>
      </div>
    </div>
    <div class="control">
      <div class="control__elements">
        <Checkbox v-model="values.number_negative">{{
          $t('fieldNumberSubForm.allowNegative')
        }}</Checkbox>
      </div>
    </div>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'

export default {
  name: 'FieldNumberSubForm',
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['number_decimal_places', 'number_negative'],
      values: {
        number_decimal_places: 0,
        number_negative: false,
      },
    }
  },
  validations: {
    values: {
      number_decimal_places: { required },
    },
  },
}
</script>
