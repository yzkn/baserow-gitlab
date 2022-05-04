const { listRowsInputFields } = require("../input-fields/searches/list-rows");
const { rowSample } = require("../samples/row");

const listRows = async (z, bundle) => {
    if (bundle.inputData.tableID) {
        // set params
        let params = {
            'size': bundle.inputData.size,
            'page': bundle.inputData.page,
            'user_field_names': bundle.inputData.userFieldNames
        }
        // make operations on inputData
        for (const [key, value] of Object.entries(bundle.inputData)) {
            // push search to params unless it's empty
            if (key === 'search' && value !== '' && value !== undefined && value !== null) {
                params['search'] = value;
            }
        }

        // get rows in a given condition
        const rowGetRequest = await z.request({
            url: `${bundle.authData.apiURL}/api/database/rows/table/${bundle.inputData.tableID}`,
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `TOKEN ${bundle.authData.apiKey}`,
            },
            params
        });
        let data = {}

        // modify data to be array of objects, so it will display as 'row4-field32555'
        // keep in mind that search actions needs to be array of object(with only 1 object, others are not displaying in UI)
        rowGetRequest.json.results.forEach((el,index) => {
            for (const [key, value] of Object.entries(el)) {
                if (value !== '' && value !== undefined && value !== null && key !== 'id' && key !== 'order') {
                    data[`row${el.id}-${key}`] = value;
                }
            }
        });

        // return data object inside of array brackets.
        return [data];
    }
}

module.exports = {
    key: 'listRows',
    noun: 'Row',
    display: {
        label: 'List Rows',
        description: 'Finds all rows in a given table.'
    },
    operation: {
        perform: listRows,
        sample: rowSample,
        inputFields: listRowsInputFields
    }
}