/*
 * Record a key sequence at runtime, save it to flash, and play it back.
 *
 *   &rm0 RM_REC   start recording; press again to stop and save
 *   &rm0 RM_PLAY  type out the saved sequence
 *
 * While recording, keys are swallowed (not sent to the computer) unless
 * CONFIG_ZMK_RECORDED_MACRO_PASSTHROUGH is set. Recording an empty sequence
 * erases the slot.
 *
 * SPDX-License-Identifier: MIT
 */

#define DT_DRV_COMPAT zmk_behavior_recorded_macro

#include <string.h>
#include <zephyr/device.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/settings/settings.h>
#include <drivers/behavior.h>

#include <zmk/behavior.h>
#include <zmk/event_manager.h>
#include <zmk/events/keycode_state_changed.h>
#include <dt-bindings/recmac.h>

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

#define MAX_EVENTS CONFIG_ZMK_RECORDED_MACRO_MAX_EVENTS
#define MAX_HELD 16
#define SETTINGS_PREFIX "recmac"

struct rm_event {
    uint16_t usage_page;
    uint16_t keycode;
    uint8_t implicit_modifiers;
    uint8_t explicit_modifiers;
    uint8_t pressed;
    uint8_t reserved;
} __packed;

struct rm_data {
    const struct device *dev;
    struct rm_event events[MAX_EVENTS];
    uint16_t len;
    uint16_t play_pos;
    bool playing;
    struct k_work_delayable play_work;
    struct k_work save_work;
};

// Only one slot records at a time. Keys pressed during recording are tracked so their
// releases are recorded too, and so releases of keys pressed *before* recording started
// still reach the computer.
static struct rm_data *recording;
static struct {
    uint16_t usage_page;
    uint16_t keycode;
} held[MAX_HELD];
static int held_count;

static int held_index(const struct zmk_keycode_state_changed *ev) {
    for (int i = 0; i < held_count; i++) {
        if (held[i].usage_page == ev->usage_page && held[i].keycode == ev->keycode) {
            return i;
        }
    }
    return -1;
}

static void append(struct rm_data *data, uint16_t page, uint16_t keycode, uint8_t implicit,
                   uint8_t explicit, bool pressed) {
    data->events[data->len++] = (struct rm_event){
        .usage_page = page,
        .keycode = keycode,
        .implicit_modifiers = implicit,
        .explicit_modifiers = explicit,
        .pressed = pressed,
    };
}

static void save_work_handler(struct k_work *work) {
#if IS_ENABLED(CONFIG_SETTINGS)
    struct rm_data *data = CONTAINER_OF(work, struct rm_data, save_work);
    char key[32];
    snprintf(key, sizeof(key), SETTINGS_PREFIX "/%s", data->dev->name);

    int err = data->len ? settings_save_one(key, data->events, data->len * sizeof(struct rm_event))
                        : settings_delete(key);
    if (err < 0) {
        LOG_ERR("recmac: failed to save %s (err %d)", data->dev->name, err);
    }
#endif
}

static void start_recording(struct rm_data *data) {
    data->len = 0;
    held_count = 0;
    recording = data;
    LOG_INF("recmac: recording %s", data->dev->name);
}

static void stop_recording(struct rm_data *data) {
    // Close out keys still held when recording stopped, so playback doesn't leave them stuck
    for (int i = 0; i < held_count; i++) {
        append(data, held[i].usage_page, held[i].keycode, 0, 0, false);
    }
    held_count = 0;
    recording = NULL;
    LOG_INF("recmac: saved %d events to %s", data->len, data->dev->name);
    k_work_submit(&data->save_work);
}

static void play_work_handler(struct k_work *work) {
    struct k_work_delayable *dwork = k_work_delayable_from_work(work);
    struct rm_data *data = CONTAINER_OF(dwork, struct rm_data, play_work);

    if (data->play_pos >= data->len) {
        data->playing = false;
        return;
    }

    const struct rm_event *e = &data->events[data->play_pos++];
    raise_zmk_keycode_state_changed((struct zmk_keycode_state_changed){
        .usage_page = e->usage_page,
        .keycode = e->keycode,
        .implicit_modifiers = e->implicit_modifiers,
        .explicit_modifiers = e->explicit_modifiers,
        .state = e->pressed,
        .timestamp = k_uptime_get(),
    });

    k_work_reschedule(dwork, K_MSEC(CONFIG_ZMK_RECORDED_MACRO_WAIT_MS));
}

static int on_keymap_binding_pressed(struct zmk_behavior_binding *binding,
                                     struct zmk_behavior_binding_event event) {
    const struct device *dev = zmk_behavior_get_binding(binding->behavior_dev);
    struct rm_data *data = dev->data;

    switch (binding->param1) {
    case RM_REC:
        if (recording == data) {
            stop_recording(data);
        } else if (recording == NULL && !data->playing &&
                   !k_work_is_pending(&data->save_work)) {
            start_recording(data);
        }
        break;
    case RM_PLAY:
        if (recording == NULL && !data->playing && data->len > 0) {
            data->playing = true;
            data->play_pos = 0;
            k_work_reschedule(&data->play_work, K_NO_WAIT);
        }
        break;
    default:
        LOG_ERR("recmac: unknown command %d", binding->param1);
        return -ENOTSUP;
    }

    return ZMK_BEHAVIOR_OPAQUE;
}

static int on_keymap_binding_released(struct zmk_behavior_binding *binding,
                                      struct zmk_behavior_binding_event event) {
    return ZMK_BEHAVIOR_OPAQUE;
}

static const struct behavior_driver_api behavior_recorded_macro_driver_api = {
    .binding_pressed = on_keymap_binding_pressed,
    .binding_released = on_keymap_binding_released,
};

static int recorded_macro_keycode_listener(const zmk_event_t *eh) {
    struct rm_data *data = recording;
    if (data == NULL) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    const struct zmk_keycode_state_changed *ev = as_zmk_keycode_state_changed(eh);
    if (ev == NULL) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    if (ev->state) {
        // Keep room for this key's release and the releases of everything else held
        if (held_count < MAX_HELD && data->len + held_count + 2 <= MAX_EVENTS) {
            held[held_count].usage_page = ev->usage_page;
            held[held_count].keycode = ev->keycode;
            held_count++;
            append(data, ev->usage_page, ev->keycode, ev->implicit_modifiers,
                   ev->explicit_modifiers, true);
        } else {
            LOG_WRN("recmac: recording full, key dropped");
        }
    } else {
        int i = held_index(ev);
        if (i < 0) {
            // Pressed before recording started: let the release through
            return ZMK_EV_EVENT_BUBBLE;
        }
        held[i] = held[--held_count];
        append(data, ev->usage_page, ev->keycode, ev->implicit_modifiers, ev->explicit_modifiers,
               false);
    }

    return IS_ENABLED(CONFIG_ZMK_RECORDED_MACRO_PASSTHROUGH) ? ZMK_EV_EVENT_BUBBLE
                                                               : ZMK_EV_EVENT_CAPTURED;
}

ZMK_LISTENER(behavior_recorded_macro, recorded_macro_keycode_listener);
ZMK_SUBSCRIPTION(behavior_recorded_macro, zmk_keycode_state_changed);

#define RM_INST(n)                                                                                 \
    static struct rm_data rm_data_##n;                                                             \
    static int rm_init_##n(const struct device *dev) {                                             \
        rm_data_##n.dev = dev;                                                                     \
        k_work_init_delayable(&rm_data_##n.play_work, play_work_handler);                          \
        k_work_init(&rm_data_##n.save_work, save_work_handler);                                    \
        return 0;                                                                                  \
    }                                                                                              \
    BEHAVIOR_DT_INST_DEFINE(n, rm_init_##n, NULL, &rm_data_##n, NULL, POST_KERNEL,                 \
                            CONFIG_KERNEL_INIT_PRIORITY_DEFAULT,                                   \
                            &behavior_recorded_macro_driver_api);

DT_INST_FOREACH_STATUS_OKAY(RM_INST)

#if IS_ENABLED(CONFIG_SETTINGS)

#define RM_DATA_PTR(n) &rm_data_##n,
static struct rm_data *const rm_instances[] = {DT_INST_FOREACH_STATUS_OKAY(RM_DATA_PTR)};

static int recorded_macro_settings_set(const char *name, size_t len, settings_read_cb read_cb,
                                       void *cb_arg) {
    for (int i = 0; i < ARRAY_SIZE(rm_instances); i++) {
        struct rm_data *data = rm_instances[i];
        if (data->dev == NULL || !settings_name_steq(name, data->dev->name, NULL)) {
            continue;
        }

        if (len > sizeof(data->events) || len % sizeof(struct rm_event) != 0) {
            LOG_ERR("recmac: stored %s has unexpected size %d", data->dev->name, len);
            return -EINVAL;
        }

        int ret = read_cb(cb_arg, data->events, len);
        if (ret < 0) {
            return ret;
        }
        data->len = len / sizeof(struct rm_event);
        return 0;
    }

    return 0;
}

SETTINGS_STATIC_HANDLER_DEFINE(recorded_macro, SETTINGS_PREFIX, NULL, recorded_macro_settings_set,
                               NULL, NULL);

#endif /* IS_ENABLED(CONFIG_SETTINGS) */

#endif /* DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT) */
