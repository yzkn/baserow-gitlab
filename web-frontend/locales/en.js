export default {
  action: {
    upload: 'Upload',
    back: 'Back',
    backToLogin: 'Back to login',
    signUp: 'Sign up',
    signIn: 'Sign in',
    createNew: 'Create new',
    create: 'Create',
    change: 'Change',
    delete: 'Delete',
    rename: 'Rename',
    add: 'Add',
    makeChoice: 'Make a choice',
    cancel: 'Cancel',
    save: 'Save',
    retry: 'Retry',
  },
  adminType: {
    settings: 'Settings',
  },
  applicationType: {
    database: 'Database',
  },
  settingType: {
    password: 'Password',
    tokens: 'API Tokens',
  },
  userFileUploadType: {
    file: 'my device',
    url: 'a URL',
  },
  field: {
    emailAddress: 'E-mail address',
  },
  error: {
    invalidEmail: 'Please enter a valid e-mail address.',
    notMatchingPassword: 'This field must match your password field.',
    minLength: 'A minimum of {min} characters is required here.',
    maxLength: 'A maximum of {max} characters is allowed here.',
    minMaxLength:
      'A minimum of {min} and a maximum of {max} characters is allowed here.',
    requiredField: 'This field is required.',
  },
  permission: {
    admin: 'Admin',
    adminDescription: 'Can fully configure and edit groups and applications.',
    member: 'Member',
    memberDescription: 'Can fully configure and edit applications.',
  },
  fieldType: {
    singleLineText: 'Single line text',
    longText: 'Long text',
    linkToTable: 'Link to table',
    number: 'Number',
    boolean: 'Boolean',
    date: 'Date',
    lastModified: 'Last modified',
    createdOn: 'Created on',
    url: 'URL',
    email: 'Email',
    file: 'File',
    singleSelect: 'Single select',
    phoneNumber: 'Phone number',
    formula: 'Formula',
  },
  viewFilter: {
    contains: 'contains',
    containsNot: 'contains not',
    filenameContains: 'filename contains',
    has: 'has',
    hasNot: 'has not',
    higherThan: 'higher than',
    is: 'is',
    isNot: 'is not',
    isEmpty: 'is empty',
    isNotEmpty: 'is not empty',
    isDate: 'is date',
    isBeforeDate: 'is before date',
    isAfterDate: 'is after date',
    isNotDate: 'is not date',
    isToday: 'is today',
    inThisMonth: 'in this month',
    inThisYear: 'in this year',
    lowerThan: 'lower than',
  },
  viewType: {
    grid: 'Grid',
    form: 'Form',
  },
  trashType: {
    group: 'group',
    application: 'application',
    table: 'table',
    field: 'field',
    row: 'row',
  },
  webhook: {
    request: 'Request',
    response: 'Response',
    status: {
      noStatus: 'NO STATUS',
      statusOK: 'OK',
      statusNotOK: 'NOT OK',
    },
    events: {
      rowCreated: 'When a row is created',
      rowUpdated: 'When a row is updated',
      rowDeleted: 'When a row is deleted',
    },
  },
}
