const { deleteRowInputFields } = require("../input-fields/creates/delete-row");
const { rowSample } = require("../samples/row");

const DeleteRow = async (z, bundle) => {
    const rowDeleteRequest = await z.request({
        url: `${bundle.authData.apiURL}/api/database/rows/table/${bundle.inputData.tableID}/${bundle.inputData.rowID}/`,
        method: 'DELETE',
        headers: {
            'Accept': 'application/json',
            'Authorization': `TOKEN ${bundle.authData.apiKey}`,
        },
    });

    return rowDeleteRequest.status === 204 ? { message: `Row ${bundle.inputData.rowID} Deleted Successfully` } : { message: `A problem occured during DELETE opeartion.` }
}

module.exports = {
    key: 'deleteRow',
    noun: 'Row',
    display: {
        label: 'Delete Row',
        description: 'Deletes a new row.'
    },
    operation: {
        perform: DeleteRow,
        sample: rowSample,
        inputFields: deleteRowInputFields
    }
}
