#include <cmath>
#include <cstring>
#include <cinttypes>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "har_features.h"
#include "inference.h"
#include "model_params.h"
#include "mpu6050.h"
#include "sdkconfig.h"
#if CONFIG_HAR_MODE_REPLAY
#include "replay_data.h"
#endif

static const char *TAG = "HAR";
static float window[HAR_WINDOW * HAR_CHANNELS];
static har_window_t ring;

static int argmax(const float *values) {
    int result = 0;
    for (int i = 1; i < 6; ++i) if (values[i] > values[result]) result = i;
    return result;
}

#if CONFIG_HAR_MODE_LIVE
static QueueHandle_t windows_queue;
static void acquire(void *) {
    static float snapshot[HAR_WINDOW * HAR_CHANNELS];
    TickType_t last = xTaskGetTickCount();
    int64_t previous = 0;
    while (true) {
        vTaskDelayUntil(&last, pdMS_TO_TICKS(20));
        const int64_t now = esp_timer_get_time();
        if (previous && (now - previous > 30000 || now - previous < 10000)) {
            ESP_LOGW(TAG, "Jitter de aquisicao: %" PRId64 " us; janela descartada", now - previous);
            har_window_reset(&ring);
            last = xTaskGetTickCount();
        }
        previous = now;
        float sample[6];
        esp_err_t error = mpu6050_read(sample);
        if (error != ESP_OK) {
            ESP_LOGW(TAG, "Falha I2C: %s; janela descartada", esp_err_to_name(error));
            har_window_reset(&ring);
            continue;
        }
        // Eixos identidade. Alinhar fisicamente ao referencial de treino antes de validar LIVE.
        if (har_window_push(&ring, sample, snapshot) && xQueueSend(windows_queue, snapshot, 0) != pdTRUE)
            ESP_LOGW(TAG, "Fila cheia: janela descartada (aquisicao continua)");
    }
}
#endif

extern "C" void app_main(void) {
    if (!inference_init()) {
        ESP_LOGE(TAG, "Falha de inicializacao TFLM; verifique modelo, operadores e arena");
        return;
    }
#if CONFIG_HAR_MODE_REPLAY
    ESP_LOGI(TAG, "mode=REPLAY source=UCI_HAR sample_hz=50 window=128");
    int passed = 0;
    for (int r = 0; r < HAR_REPLAY_COUNT; ++r) {
        har_window_reset(&ring);
        bool ready = false;
        for (int i = 0; i < HAR_WINDOW; ++i) ready = har_window_push(&ring, HAR_REPLAY_WINDOWS[r][i], window);
        float probabilities[6], features[36];
        int8_t input[36];
        int64_t elapsed;
        if (!ready || !inference_run(window, probabilities, input, &elapsed) || !har_extract(window, features)) {
            ESP_LOGE(TAG, "replay=%d falha de pipeline", r);
            continue;
        }
        bool match = true;
        int feature_mismatches = 0, input_mismatches = 0, first_input_mismatch = -1;
        float max_feature_error = 0, max_probability_error = 0;
        for (int i = 0; i < 36; ++i) {
            float delta = std::fabs(features[i] - HAR_REPLAY_FEATURES[r][i]);
            max_feature_error = fmaxf(max_feature_error, delta);
            if (delta > 1e-5f + 1e-5f * std::fabs(HAR_REPLAY_FEATURES[r][i])) ++feature_mismatches;
            if (input[i] != HAR_REPLAY_INPUTS[r][i]) {
                ++input_mismatches;
                if (first_input_mismatch < 0) first_input_mismatch = i;
            }
        }
        if (feature_mismatches || input_mismatches) match = false;
        for (int i = 0; i < 6; ++i)
            max_probability_error = fmaxf(max_probability_error, std::fabs(probabilities[i] - HAR_REPLAY_PROBS[r][i]));
        // TFLM/ESP-NN e desktop podem diferir por arredondamento dos kernels inteiros.
        if (max_probability_error > 2.0f / 256.0f || argmax(probabilities) != argmax(HAR_REPLAY_PROBS[r])) match = false;
        const int prediction = argmax(probabilities);
        if (match) ++passed;
        ESP_LOGI(TAG, "replay=%d test_index=%d truth=%s class=%s confidence=%.6f invoke_us=%" PRId64
                 " feature_error=%.8f probability_error=%.8f parity=%s", r, HAR_REPLAY_INDICES[r],
                 HAR_CLASSES[HAR_REPLAY_LABELS[r]], HAR_CLASSES[prediction], probabilities[prediction], elapsed,
                 max_feature_error, max_probability_error, match ? "PASS" : "FAIL");
        if (!match) {
            ESP_LOGW(TAG, "replay_diag=%d feature_mismatches=%d input_mismatches=%d expected_class=%s",
                     r, feature_mismatches, input_mismatches, HAR_CLASSES[argmax(HAR_REPLAY_PROBS[r])]);
            if (first_input_mismatch >= 0)
                ESP_LOGW(TAG, "input_index=%d actual=%d expected=%d", first_input_mismatch,
                         (int)input[first_input_mismatch], (int)HAR_REPLAY_INPUTS[r][first_input_mismatch]);
            for (int c = 0; c < 6; ++c)
                ESP_LOGW(TAG, "replay_prob=%d class=%s actual=%.8f expected=%.8f",
                         r, HAR_CLASSES[c], probabilities[c], HAR_REPLAY_PROBS[r][c]);
        }
        vTaskDelay(pdMS_TO_TICKS(200));
    }
    ESP_LOGI(TAG, "REPLAY_SUMMARY passed=%d total=%d status=%s", passed, HAR_REPLAY_COUNT,
             passed == HAR_REPLAY_COUNT ? "PASS" : "FAIL");
#else
    ESP_LOGW(TAG, "mode=LIVE: transferencia UCI->MPU6050 ainda exige validacao com dados locais");
    ESP_ERROR_CHECK(mpu6050_init());
    windows_queue = xQueueCreate(2, sizeof(window));
    if (!windows_queue || xTaskCreate(acquire, "mpu_acquire", 4096, nullptr, 5, nullptr) != pdPASS) {
        ESP_LOGE(TAG, "Sem memoria para aquisicao");
        return;
    }
    while (true) {
        if (xQueueReceive(windows_queue, window, portMAX_DELAY) != pdTRUE) continue;
        float probabilities[6];
        int8_t input[36];
        int64_t elapsed;
        if (!inference_run(window, probabilities, input, &elapsed)) {
            ESP_LOGE(TAG, "Falha na inferencia");
            continue;
        }
        int prediction = argmax(probabilities);
        ESP_LOGI(TAG, "class=%s confidence=%.6f invoke_us=%" PRId64, HAR_CLASSES[prediction], probabilities[prediction], elapsed);
    }
#endif
}
