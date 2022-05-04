const { updateRowInputFields } = require("../input-fields/creates/update-row");
const { rowSample } = require("../samples/row");

const updateRow = async (z, bundle) => {
    if (bundle.inputData.tableID && bundle.inputData.rowID) {
        const fieldsGetRequest = await z.request({
            url: `${bundle.authData.apiURL}/api/database/fields/table/${bundle.inputData.tableID}/`,
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `TOKEN ${bundle.authData.apiKey}`,
            },
        });

        let rowData = { id: bundle.inputData.rowID, order: bundle.inputData.rowID }

        fieldsGetRequest.json.forEach(v => {
            if (v.type === 'formula' || v.type === 'created_on' || v.type === 'last_modified' || v.type === 'lookup'  || v.type === 'file') return;
            rowData[`field_${v.id}`] = bundle.inputData[`field_${v.id}`];
        });

        const rowPatchRequest = await z.request({
            url: `${bundle.authData.apiURL}/api/database/rows/table/${bundle.inputData.tableID}/${bundle.inputData.rowID}/`,
            method: 'PATCH',
            headers: {
                'Accept': 'application/json',
                "Content-Type": "application/json",
                'Authorization': `TOKEN ${bundle.authData.apiKey}`,
            },
            body: rowData
        });

        return rowPatchRequest.json;
    }
}

const inputValues = async (z, bundle) => {
    if (bundle.inputData.tableID && bundle.inputData.rowID) {
        const fieldsGetRequest = await z.request({
            url: `${bundle.authData.apiURL}/api/database/fields/table/${bundle.inputData.tableID}/`,
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `TOKEN ${bundle.authData.apiKey}`,
            },
        })

        const rowGetRequest = await z.request({
            url: `${bundle.authData.apiURL}/api/database/rows/table/${bundle.inputData.tableID}/${bundle.inputData.rowID}/`,
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `TOKEN ${bundle.authData.apiKey}`,
            },
        });

        let values = [];

        values = fieldsGetRequest.json.map(v => {
            let defaultValue = rowGetRequest.json[`field_${v.id}`] || '';
            zapType = ''
            switch (v.type) {
                case 'boolean':
                    zapType = 'boolean'
                    break;
                case 'number':
                case 'phone':
                    zapType = 'integer'
                    break;
                case 'single_select':
                    let singleSelect = {}
                    v.select_options.forEach(el => {
                        singleSelect[`${el.id}`] = el.value;
                    })
                    return {
                        key: `field_${v.id}`,
                        label: v.name,
                        type: 'string',
                        choices: singleSelect,
                        default: defaultValue ? defaultValue.id : ''
                    }
                case 'multiple_select':
                    let multiSelect = {}
                    v.select_options.forEach(el => {
                        multiSelect[`${el.id}`] = el.value;
                    })
                    return {
                        key: `field_${v.id}`,
                        label: v.name,
                        type: 'string',
                        choices: multiSelect,
                        list: true
                    }
                case 'link_row':
                    return {
                        key: `field_${v.id}`,
                        label: v.name,
                        type: 'string',
                        helpText: `Provide row number/numbers that you want to link by using custom field`,
                        list: true
                    }
                case 'date':
                    if (v.date_include_time) {
                        return {
                            key: `field_${v.id}`,
                            label: v.name,
                            type: zapType,
                            helpText: 'the datetime fields accept a date and time in ISO format'
                        }
                    }
                    return {
                        key: `field_${v.id}`,
                        label: v.name,
                        type: zapType,
                        helpText: 'the date fields accept a date in ISO format'
                    }
                case 'last_modified':
                case 'formula':
                case 'created_on':
                case 'lookup':
                case 'file':
                    return;
                default:
                    zapType = 'string'
                    break;
            }
            return {
                key: `field_${v.id}`,
                type: zapType,
                default: defaultValue,
                label: v.name
            }
        })
        return values;
    }
}

module.exports = {
    key: 'updateRow',
    noun: 'Row',
    display: {
        label: 'Update Row',
        description: 'Updates an existing row.'
    },
    operation: {
        perform: updateRow,
        sample: rowSample,
        inputFields: [...updateRowInputFields, inputValues]
    }
}
