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
  slots.sort((a, b) => {
    if (a.item === null || b.item === null) {
      return 0
    }
    return (
      items.findIndex((item) => item.id === a.item.id) -
      items.findIndex((item) => item.id === b.item.id)
    )
  })
  console.log(items)
  // let moved = true
  // while (moved) {
  //   console.log('loop')
  //   moved = false
  //   for (let i = 0; i < items.length; i++) {
  //     const item = items[i]
  //     if (item !== null) {
  //       const existingIndex = slots.findIndex(
  //         (slot) => slot.item !== null && slot.item.id === item.id
  //       )
  //       if (existingIndex > -1 && i !== existingIndex) {
  //         slots.splice(i, 0, slots.splice(existingIndex, 1)[0])
  //         moved = true
  //         break
  //       }
  //     }
  //   }
  // }

  items.forEach((item, index) => {
    // if (item !== slots[index].item) {
    //   slots[index].item = item
    // }
    const position = getPosition(item, index)
    // if (JSON.stringify(position) === JSON.stringify(slots[index].position) ) {
    //   slots[index].position = position
    // }

    slots[index].item = item
    slots[index].position = position
  })
}
