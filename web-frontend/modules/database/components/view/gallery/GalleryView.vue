<template>
  <div class="gallery-view">
    <a href="#" class="gallery-view__add">
      <i class="fas fa-plus"></i>
    </a>
    <div ref="scroll" class="gallery-view__scroll">
      <div
        class="gallery-view__cards"
        :style="{
          height: height + 'px',
        }"
      >
        <RowCard
          v-for="slot in buffer"
          v-show="slot.left != -1"
          :key="'card-' + slot.id"
          :fields="cardFields"
          :row="slot.row === null ? {} : slot.row"
          :loading="slot.row === null"
          class="gallery-view__card"
          :style="{
            width: cardWidth + 'px',
            transform: `translateX(${slot.left}px) translateY(${slot.top}px)`,
          }"
        ></RowCard>

        <!--
        :style="{
            transform: `translateY(${
              slot.position * cardHeight + bufferTop
            }px)`,
          }"
        <template v-for="(row, index) in buffer">
          <RowCard
            v-if="row !== null"
            :key="'card-' + row.id"
            :fields="cardFields"
            :row="row"
            class="gallery-view__card"
          ></RowCard>
          <RowCard
            v-else
            :key="'loading-' + index"
            :fields="cardFields"
            :loading="true"
            class="gallery-view__card"
            :style="{ height: cardHeight + 'px' }"
          >
          </RowCard>
        </template>
        -->
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import ResizeObserver from 'resize-observer-polyfill'
import { getCardHeight } from '@baserow/modules/database/utils/card'
import { maxPossibleOrderValue } from '@baserow/modules/database/viewTypes'
import RowCard from '@baserow/modules/database/components/card/RowCard'

export default {
  name: 'GalleryView',
  components: { RowCard },
  props: {
    primary: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    database: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      height: 0,
      cardWidth: 0,
      cardsPerRow: 1,
      buffer: [],
    }
  },
  computed: {
    firstRows() {
      return this.allRows.slice(0, 200)
    },
    /**
     * In order for the virtual scrolling to work, we need to know what the height of
     * the card is to correctly position it.
     */
    cardHeight() {
      // 10 = margin-bottom of kanban.scss.kanban-view__stack-card
      return getCardHeight(this.cardFields, this.$registry)
    },
    /**
     * Returns the visible field objects in the right order.
     */
    cardFields() {
      return [this.primary]
        .concat(this.fields)
        .filter((field) => {
          const exists = Object.prototype.hasOwnProperty.call(
            this.fieldOptions,
            field.id
          )
          return !exists || (exists && !this.fieldOptions[field.id].hidden)
        })
        .sort((a, b) => {
          const orderA = this.fieldOptions[a.id]
            ? this.fieldOptions[a.id].order
            : maxPossibleOrderValue
          const orderB = this.fieldOptions[b.id]
            ? this.fieldOptions[b.id].order
            : maxPossibleOrderValue

          // First by order.
          if (orderA > orderB) {
            return 1
          } else if (orderA < orderB) {
            return -1
          }

          // Then by id.
          if (a.id < b.id) {
            return -1
          } else if (a.id > b.id) {
            return 1
          } else {
            return 0
          }
        })
    },
  },
  watch: {
    cardHeight() {
      this.$nextTick(() => {
        this.updateBuffer()
      })
    },
    allRows() {
      this.$nextTick(() => {
        this.updateBuffer()
      })
    },
  },
  mounted() {
    this.updateBuffer()
    this.$el.resizeObserver = new ResizeObserver(() => {
      this.updateBuffer()
    })
    this.$el.resizeObserver.observe(this.$el)

    this.$el.scrollEvent = () => {
      this.updateBuffer()
    }
    this.$refs.scroll.addEventListener('scroll', this.$el.scrollEvent)
  },
  beforeDestroy() {
    this.$el.resizeObserver.unobserve(this.$el)
    this.$refs.scroll.removeEventListener('scroll', this.$el.scrollEvent)
  },
  beforeCreate() {
    this.$options.computed = {
      ...(this.$options.computed || {}),
      ...mapGetters({
        allRows: this.$options.propsData.storePrefix + 'view/gallery/getRows',
        fieldOptions:
          this.$options.propsData.storePrefix +
          'view/gallery/getAllFieldOptions',
      }),
    }
  },
  methods: {
    async refresh() {
      await console.log('@TODO refresh')
    },

    /**
     * @TODO make this really virtual
     */
    updateBuffer() {
      const el = this.$refs.scroll

      const gutterSize = 30
      const containerWidth = el.clientWidth
      const containerHeight = el.clientHeight

      const cardsPerRow = Math.min(
        Math.max(Math.floor(containerWidth / 280), 1),
        20
      )
      const cardHeight = this.cardHeight
      const cardWidth = (containerWidth - gutterSize) / cardsPerRow - gutterSize
      const totalRows = Math.ceil(this.allRows.length / cardsPerRow)
      const height = totalRows * cardHeight + gutterSize + gutterSize

      this.cardWidth = cardWidth
      this.height = height

      const scrollTop = el.scrollTop
      const minimumCardsToRender =
        (Math.ceil(containerHeight / (cardHeight + gutterSize)) + 1) *
        cardsPerRow
      const startIndex =
        Math.floor(scrollTop / (cardHeight + gutterSize)) * cardsPerRow
      const endIndex = startIndex + minimumCardsToRender
      const visibleRows = this.allRows.slice(startIndex, endIndex)

      this.buffer = visibleRows.map((row, positionInVisible) => {
        const positionInAll = startIndex + positionInVisible
        const left =
          gutterSize + (positionInAll % cardsPerRow) * (gutterSize + cardWidth)
        const top =
          gutterSize +
          Math.floor(positionInAll / cardsPerRow) * (gutterSize + cardHeight)

        return {
          id: positionInVisible,
          row,
          left,
          top,
        }
      })
    },
  },
}
</script>
