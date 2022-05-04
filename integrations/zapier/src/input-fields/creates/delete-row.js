const deleteRowInputFields = [
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
        required: true
    },
]
module.exports = { deleteRowInputFields }