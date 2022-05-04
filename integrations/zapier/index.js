/* Authentication */
const authentication = require('./authentication');

/* Creates */
const deleteRowCreate = require('./src/creates/delete-row');
const newRowCreate = require('./src/creates/new-row');
const updateRowCreate = require('./src/creates/update-row');

/* Searches */
const getSingleRowSearch = require('./src/searches/get-single-row');
const listRowsSearch = require('./src/searches/list-rows');

module.exports = {
  // This is just shorthand to reference the installed dependencies you have.
  // Zapier will need to know these before we can upload.
  version: require('./package.json').version,
  platformVersion: require('zapier-platform-core').version,
  authentication: authentication,

  // If you want your trigger to show up, you better include it here!
  triggers: {
  },

  // If you want your searches to show up, you better include it here!
  searches: {
    [getSingleRowSearch.key]: getSingleRowSearch,
    [listRowsSearch.key]: listRowsSearch
  },

  // If you want your creates to show up, you better include it here!
  creates: {
    [newRowCreate.key]: newRowCreate,
    [deleteRowCreate.key]: deleteRowCreate,
    [updateRowCreate.key]: updateRowCreate,
  },

  resources: {},
};
