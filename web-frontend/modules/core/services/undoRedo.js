export default (client) => {
  return {
    undo(categories) {
      return client.patch(`/user/undo/`, {
        categories,
      })
    },
    redo(categories) {
      return client.patch(`/user/redo/`, {
        categories,
      })
    },
  }
}
