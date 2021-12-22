/**
 * This helper method will create an array of slots, where every entry contains the
 * provided provided `items` entry in the right order. Every slot has a unique `id` and
 * when the order of the the item changes, it will make sure that it will use the same
 * slot ID without recreating the slots array.
 *
 * This is useful when virtual scrolling must be implemented. The `id` of the slot
 * can be used to as `:key="slot.id"` value in the template. Because the id will
 * always match the item id, it will never update or re-render the element. New
 * items will get a recycled slot id so that they don't have to be re-rendered.
 *
 * It is a requirement that every item has an `id` property to make sure the id of
 * the slot is properly recycled.
 *
 * Optionally a `getPosition` can be provided to set the `position` property in each
 * slot. This is typically used by virtual scrolling change the absolute position of
 * the dom element. This could be needed because the elements before are not rendered
 * and are not pushing it into the right position.
 *
 * Example:
 *
 * const slots = recycleSlots(
 *  [],
 *  [
 *    { id: 1, name: "Item 1" },
 *    { id: 2, name: "Item 2" }
 *  ]
 * ) == [
 *   { id: 0, position: undefined, item: { id: 1, name: "Item 1" } },
 *   { id: 1, position: undefined, item: { id: 2, name: "Item 2" } }
 * ]
 *
 * recycleSlots(
 *  slots,
 *  [
 *    { id: 2, name: "Item 2" },
 *    { id: 3, name: "Item 3" }
 *  ]
 * ) == [
 *   { id: 1, position: undefined, item: { id: 2, name: "Item 2" } },
 *   { id: 0, position: undefined, item: { id: 3, name: "Item 3" } }
 * ]
 */
export const recycleSlots = (slots, items, getPosition) => {
  // First fill up the buffer with the minimum amount of slots.
  for (let i = slots.length; i < items.length; i++) {
    // Find the first available id base on the length of the array. This is needed
    // because we don't want to have id outside of the items length range.
    const id = [...Array(items.length).keys()].find(
      (id) => slots.findIndex((slot) => slot.id === id) < 0
    )
    slots.push({
      id,
      position: undefined,
      item: null,
    })
  }

  // Remove not needed slots.
  if (slots.length > items.length) {
    slots.splice(items.length, slots.length)
  }

  // This loop will make sure that the existing items in the slots array are at the
  // right position by moving them. The slots array will not be recreated to prevent
  // re-rendering.
  let i = 0
  while (i < items.length) {
    const item = items[i]

    if (item === null) {
      i++
      continue
    }

    const existingIndex = slots.findIndex(
      (slot) => slot.item !== null && slot.item.id === item.id
    )

    if (existingIndex > -1 && existingIndex !== i) {
      // If the item already exists in the slots array, but the position match yet,
      // we need to move it.
      if (existingIndex < i) {
        // In this case, the existing index is lower than the new index, so in order
        // avoid conflicts with already moved items we just swap them.
        slots.splice(i, 0, slots.splice(existingIndex, 1)[0])
        slots.splice(existingIndex, 0, slots.splice(i - 1, 1)[0])
        i++
      } else if (existingIndex > i) {
        // If the existing index is higher than the expected index, we need to move
        // it one by one to avoid conflicts with already moved items.
        slots.splice(existingIndex - 1, 0, slots.splice(existingIndex, 1)[0])
      }
    } else {
      i++
    }
  }

  // Because the slots are already in the desired order, we can loop over the items
  // and update and position if they have changed. The properties are only updated
  // if they have actually changed to avoid re-renders.
  items.forEach((item, index) => {
    if (slots[index].item !== item) {
      slots[index].item = item
    }
    const position = getPosition(item, index)
    if (JSON.stringify(position) !== JSON.stringify(slots[index].position)) {
      slots[index].position = position
    }
  })
}
