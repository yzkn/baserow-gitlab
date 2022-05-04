module.exports = {
    type: 'custom',
    test: {
      url: `{{bundle.authData.apiURL}}/api/database/fields/table/{{bundle.authData.tableID}}/`,
      method: 'GET',
      headers: { 'Authorization': 'TOKEN {{bundle.authData.apiKey}}' },
    },
    fields: [
      {
        computed: false,
        key: 'apiKey',
        required: true,
        label: 'Baserow API token',
        type: 'string',
        helpText:
          'Please enter your Baserow API token. Can be found by clicking on your account in the top left corner -> Settings -> API tokens.',
      },
      {
        computed: false,
        key: 'tableID',
        required: true,
        label: 'Baserow table ID',
        type: 'integer',
        helpText:
          'Please enter your Baserow table ID. Can be found by clicking on your account in the top left corner -> Settings -> API tokens -> your token -> show databases.',
      },
      {
        computed: false,
        key: 'apiURL',
        required: false,
        label: 'Baserow API URL',
        default: 'https://api.baserow.io',
        type: 'string',
        helpText:
          'Please enter your Baserow API URL. If you are using baserow.io, you can leave the default one.',
      },
    ],
    connectionLabel: 'Baserow Account',
    customConfig: {},
  };
