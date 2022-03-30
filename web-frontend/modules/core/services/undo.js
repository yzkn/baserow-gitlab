export default (client) => {
  return {
    undo(scope) {
      return client.patch(`/user/undo/`, {
        scope,
      })
    },
    redo(scope) {
      return client.patch(`/user/redo/`, {
        scope,
      })
    },
  }
}
