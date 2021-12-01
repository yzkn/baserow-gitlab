<template>
  <div ref="gallery" class="gallery-view">
    <a href="#" class="gallery-view__add">
      <i class="fas fa-plus"></i>
    </a>
    <div class="gallery-view__scroll">
      <div
        class="gallery-view__cards"
        :class="`gallery-view__cards--${cardsPerRow}-per-row`"
      >
        <div
          v-for="i in new Array(100)"
          :key="i"
          class="card gallery-view__card"
        >
          <div class="card__field">
            <div class="card__field-name">Text</div>
            <div class="card__field-value">
              <div class="card-text">This is a single line text field</div>
            </div>
          </div>
          <div class="card__field">
            <div class="card__field-name">Long text</div>
            <div class="card__field-value">
              <div class="card-text">
                This is a long text field with a very long content that doesn't
                fit.
              </div>
            </div>
          </div>
          <div class="card__field">
            <div class="card__field-name">Boolean</div>
            <div class="card__field-value">
              <div class="card-boolean">
                <i class="fas fa-check"></i>
              </div>
            </div>
          </div>
          <div class="card__field">
            <div class="card__field-name">Date</div>
            <div class="card__field-value">
              <div class="card-text">2021-01-01</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ResizeObserver from 'resize-observer-polyfill'

export default {
  name: 'GalleryView',
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
  },
  data() {
    return {
      cardsPerRow: 1,
    }
  },
  mounted() {
    this.$el.resizeObserver = new ResizeObserver(this.updateCardsPerRow)
    this.$el.resizeObserver.observe(this.$el)
  },
  beforeDestroy() {
    this.$el.resizeObserver.unobserve(this.$el)
  },
  methods: {
    updateCardsPerRow() {
      this.cardsPerRow = Math.min(
        Math.max(Math.floor(this.$refs.gallery.clientWidth / 280), 1),
        20
      )
    },
    async refresh() {
      await console.log('@TODO refresh')
    },
  },
}
</script>
