# Behaviors only run on the central (left) half
if ((NOT CONFIG_ZMK_SPLIT) OR CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
  target_sources_ifdef(CONFIG_ZMK_BEHAVIOR_RECORDED_MACRO app PRIVATE src/behavior_recorded_macro.c)

  zephyr_include_directories(include)
endif()
