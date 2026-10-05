#pragma once
#include <cstdint>
bool inference_init();
bool inference_run(const float *window, float probabilities[6], int8_t quantized_input[36], int64_t *elapsed_us);
