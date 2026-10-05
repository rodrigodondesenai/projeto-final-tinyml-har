#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define HAR_WINDOW 128
#define HAR_CHANNELS 6
#define HAR_FEATURES 36
#define HAR_STRIDE 64
bool har_extract(const float *window, float *features);
bool har_normalize(const float *features, const float *mean, const float *scale, float *out);
bool har_quantize(const float *values, float scale, int zero_point, int8_t *out, size_t count);
typedef struct {
    float samples[HAR_WINDOW * HAR_CHANNELS];
    size_t next;
    size_t count;
    size_t since_emit;
} har_window_t;
void har_window_reset(har_window_t *buffer);
bool har_window_push(har_window_t *buffer, const float sample[HAR_CHANNELS], float *window);
void har_mpu_decode(const uint8_t bytes[14], float sample[HAR_CHANNELS]);
#ifdef __cplusplus
}
#endif
