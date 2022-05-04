const listRowsInputFields = [
    {
        key: 'tableID',
        label: 'Table ID',
        type: 'integer',
        required: true,
        altersDynamicFields: true,
    },
    {
        key: 'page',
        label: 'page',
        helpText: 'Defines which page of rows should be returned.',
        type: 'string',
        default: '1'
    },
    {
        key: 'size',
        label: 'size',
        helpText: 'Defines how many rows should be returned per page.',
        type: 'string',
        default: '100'
    },
    {
        key: 'userFieldNames',
        label: 'userFieldNames',
        helpText: 'Turn on to get actual names of the fields.',
        type: 'boolean',
        default: 'false'
    },
    {
        key: 'search',
        label: 'search',
        helpText: 'If provided only rows with data that matches the search query are going to be returned.',
        type: 'string',
    },
]
module.exports = { listRowsInputFields }