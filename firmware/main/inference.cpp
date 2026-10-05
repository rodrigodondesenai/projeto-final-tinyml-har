#include "inference.h"
#include "har_features.h"
#include "model_data.h"
#include "model_params.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "sdkconfig.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

static const char *TAG = "HAR";
alignas(16) static uint8_t arena[CONFIG_HAR_TENSOR_ARENA_BYTES];
static tflite::MicroInterpreter *interpreter;

bool inference_init() {
    const tflite::Model *model = tflite::GetModel(g_har_model);
    if (model->version() != TFLITE_SCHEMA_VERSION) return false;
    static tflite::MicroMutableOpResolver<2> resolver;
    if (resolver.AddFullyConnected() != kTfLiteOk || resolver.AddSoftmax() != kTfLiteOk) return false;
    static tflite::MicroInterpreter instance(model, resolver, arena, sizeof(arena));
    interpreter = &instance;
    if (interpreter->AllocateTensors() != kTfLiteOk) return false;
    auto *input = interpreter->input(0);
    auto *output = interpreter->output(0);
    if (input->type != kTfLiteInt8 || output->type != kTfLiteInt8 ||
        input->dims->size != 2 || input->dims->data[0] != 1 || input->dims->data[1] != 36 ||
        output->dims->size != 2 || output->dims->data[0] != 1 || output->dims->data[1] != 6) return false;
    if (input->params.scale != HAR_INPUT_SCALE || input->params.zero_point != HAR_INPUT_ZERO ||
        output->params.scale != HAR_OUTPUT_SCALE || output->params.zero_point != HAR_OUTPUT_ZERO) return false;
    ESP_LOGI(TAG, "modelo_bytes=%u arena_usada=%u arena_reservada=%u",
             (unsigned)g_har_model_len, (unsigned)interpreter->arena_used_bytes(), (unsigned)sizeof(arena));
#if CONFIG_NN_OPTIMIZED
    ESP_LOGI(TAG, "kernels=ESP_NN_OPTIMIZED");
#else
    ESP_LOGI(TAG, "kernels=ESP_NN_ANSI_C");
#endif
    return true;
}

bool inference_run(const float *window, float probabilities[6], int8_t quantized_input[36], int64_t *elapsed_us) {
    float features[36], normalized[36];
    if (!har_extract(window, features) || !har_normalize(features, HAR_MEAN, HAR_SCALE, normalized)) return false;
    auto *input = interpreter->input(0);
    if (!har_quantize(normalized, input->params.scale, input->params.zero_point, quantized_input, 36)) return false;
    for (int i = 0; i < 36; ++i) input->data.int8[i] = quantized_input[i];
    int64_t start = esp_timer_get_time();
    if (interpreter->Invoke() != kTfLiteOk) return false;
    *elapsed_us = esp_timer_get_time() - start;
    auto *output = interpreter->output(0);
    for (int i = 0; i < 6; ++i)
        probabilities[i] = (output->data.int8[i] - output->params.zero_point) * output->params.scale;
    return true;
}
