<template>
  <footer
    v-if="$nav.currentLayout !== 'cover'"
    class="absolute bottom-0 left-0 right-0 p-2"
  >
    <small><SlideCurrentNo/>/<SlidesTotal/></small>
  </footer>
</template>
