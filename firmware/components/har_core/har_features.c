#include "har_features.h"
#include <math.h>
#include <string.h>

bool har_extract(const float *window, float *features) {
    for (int c = 0; c < HAR_CHANNELS; ++c) {
        float sum = 0.0f, squares = 0.0f;
        float low = window[c], high = window[c];
        for (int i = 0; i < HAR_WINDOW; ++i) {
            float value = window[i * HAR_CHANNELS + c];
            if (!isfinite(value)) return false;
            sum += value;
            squares += value * value;
            if (value < low) low = value;
            if (value > high) high = value;
        }
        const float mean = sum / (float)HAR_WINDOW;
        float variance = 0.0f;
        for (int i = 0; i < HAR_WINDOW; ++i) {
            const float delta = window[i * HAR_CHANNELS + c] - mean;
            variance += delta * delta;
        }
        const float energy = squares / (float)HAR_WINDOW;
        float *f = features + c * 6;
        f[0] = mean;
        f[1] = sqrtf(variance / (float)HAR_WINDOW);
        f[2] = sqrtf(energy);
        f[3] = low;
        f[4] = high;
        f[5] = energy;
        for (int j = 0; j < 6; ++j) if (!isfinite(f[j])) return false;
    }
    return true;
}

bool har_normalize(const float *features, const float *mean, const float *scale, float *out) {
    for (int i = 0; i < HAR_FEATURES; ++i) {
        if (!isfinite(scale[i]) || scale[i] <= 0.0f) return false;
        out[i] = (features[i] - mean[i]) / scale[i];
        if (!isfinite(out[i])) return false;
    }
    return true;
}

bool har_quantize(const float *values, float scale, int zero_point, int8_t *out, size_t count) {
    if (!isfinite(scale) || scale <= 0.0f || zero_point < -128 || zero_point > 127) return false;
    for (size_t i = 0; i < count; ++i) {
        if (!isfinite(values[i])) return false;
        float q = roundf(values[i] / scale) + (float)zero_point;
        if (q < -128.0f) q = -128.0f;
        if (q > 127.0f) q = 127.0f;
        out[i] = (int8_t)q;
    }
    return true;
}

void har_window_reset(har_window_t *buffer) { memset(buffer, 0, sizeof(*buffer)); }

bool har_window_push(har_window_t *buffer, const float sample[HAR_CHANNELS], float *window) {
    memcpy(buffer->samples + buffer->next * HAR_CHANNELS, sample, HAR_CHANNELS * sizeof(float));
    buffer->next = (buffer->next + 1) % HAR_WINDOW;
    if (buffer->count < HAR_WINDOW) {
        ++buffer->count;
        if (buffer->count != HAR_WINDOW) return false;
    } else {
        if (++buffer->since_emit < HAR_STRIDE) return false;
    }
    buffer->since_emit = 0;
    for (size_t i = 0; i < HAR_WINDOW; ++i)
        memcpy(window + i * HAR_CHANNELS, buffer->samples + ((buffer->next + i) % HAR_WINDOW) * HAR_CHANNELS,
               HAR_CHANNELS * sizeof(float));
    return true;
}

static int16_t signed_word(const uint8_t *p) {
    const uint16_t u = ((uint16_t)p[0] << 8) | p[1];
    return (int16_t)(u < 32768 ? (int32_t)u : (int32_t)u - 65536);
}

void har_mpu_decode(const uint8_t bytes[14], float sample[HAR_CHANNELS]) {
    // ACCEL_CONFIG=0 (+/-2g), GYRO_CONFIG=0 (+/-250 deg/s). Temperatura ignorada.
    for (int i = 0; i < 3; ++i) {
        sample[i] = (float)signed_word(bytes + 2 * i) / 16384.0f;
        sample[3 + i] = ((float)signed_word(bytes + 8 + 2 * i) / 131.0f) * 0.017453292519943295f;
    }
}
