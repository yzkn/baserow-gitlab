const { getSingleRowInputFields } = require("../input-fields/searches/get-single-row");
const { rowSample } = require("../samples/row");

const getSingleRow = async (z, bundle) => {
    if (bundle.inputData.tableID && bundle.inputData.rowID) {
        const rowGetRequest = await z.request({
            url: `${bundle.authData.apiURL}/api/database/rows/table/${bundle.inputData.tableID}/${bundle.inputData.rowID}/${bundle.inputData.userFieldNames === true ? '?user_field_names=true' : ''}`,
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `TOKEN ${bundle.authData.apiKey}`,
            },
        });

        return [rowGetRequest.json];
    }
}

module.exports = {
    key: 'getSingleRow',
    noun: 'Row',
    display: {
        label: 'Get Single Row',
        description: 'Finds a single row in a given table.'
    },
    operation: {
        perform: getSingleRow,
        sample: rowSample,
        inputFields: getSingleRowInputFields
    }
}
