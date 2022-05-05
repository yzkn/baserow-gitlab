const { rowInputFields } = require("../input-fields/creates/new-row");
const { rowSample } = require("../samples/row");

const createRow = async (z, bundle) => {
    if (bundle.inputData.tableID) {
        const fieldsGetRequest = await z.request({
            url: `${bundle.authData.apiURL}/api/database/fields/table/${bundle.inputData.tableID}/`,
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Token ${bundle.authData.apiKey}`,
            },
        });

        let rowData = {}

        fieldsGetRequest.json.forEach(v => {
            if (v.type === 'formula' || v.type === 'created_on' || v.type === 'last_modified' || v.type === 'lookup' || v.type === 'file') return;
            rowData[`field_${v.id}`] = bundle.inputData[`field_${v.id}`];
        });

        const rowPostRequest = await z.request({
            url: `${bundle.authData.apiURL}/api/database/rows/table/${bundle.inputData.tableID}/`,
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': `Token ${bundle.authData.apiKey}`,
            },
            body: rowData
        });

        return rowPostRequest.json;
    }
}

const inputValues = async (z, bundle) => {
    if (bundle.inputData.tableID) {
        const fieldsGetRequest = await z.request({
            url: `${bundle.authData.apiURL}/api/database/fields/table/${bundle.inputData.tableID}/`,
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Token ${bundle.authData.apiKey}`,
            },
        })

        let values = [];
        values = fieldsGetRequest.json.map(v => {
            let zapType = ''
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
                        choices: singleSelect
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
                label: v.name,
                type: zapType,
            }
        })
      return values;
    }
}

module.exports = {
    key: 'newRow',
    noun: 'Row',
    display: {
        label: 'Create Row',
        description: 'Creates a new row.'
    },
    operation: {
        perform: createRow,
        sample: rowSample,
        inputFields: [...rowInputFields, inputValues]
    }
}
