#pragma once
#include "esp_err.h"
#ifdef __cplusplus
extern "C" {
#endif
esp_err_t mpu6050_init(void);
esp_err_t mpu6050_read(float sample[6]);
#ifdef __cplusplus
}
#endif
