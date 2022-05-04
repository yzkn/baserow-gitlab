const getSingleRowInputFields = [
    {
        key: 'tableID',
        label: 'Table ID',
        type: 'integer',
        required: true,
        altersDynamicFields: true,
    },
    {
        key: 'rowID',
        label: 'Row ID',
        type: 'integer',
        required: true,
    },
    {
        key: 'userFieldNames',
        label: 'Turn on to get actual names of the fields.',
        type: 'boolean',
    },
]
module.exports = { getSingleRowInputFields }