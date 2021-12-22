export const recycleSlots = (slots, items, getPosition) => {
  // First fill up the buffer with the minimum amount of slots.
  for (let i = slots.length; i < items.length; i++) {
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

  // @TODO docs
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
      if (existingIndex < i) {
        // Swap
        slots.splice(i, 0, slots.splice(existingIndex, 1)[0])
        slots.splice(existingIndex, 0, slots.splice(i - 1, 1)[0])
        i++
      } else if (existingIndex > i) {
        // Move
        slots.splice(existingIndex - 1, 0, slots.splice(existingIndex, 1)[0])
      }
    } else {
      i++
    }
  }

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
