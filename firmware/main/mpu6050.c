#include "mpu6050.h"
#include "har_features.h"
#include "driver/i2c_master.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sdkconfig.h"

static i2c_master_dev_handle_t device;
static esp_err_t write_register(uint8_t reg, uint8_t value) {
    uint8_t bytes[] = {reg, value};
    return i2c_master_transmit(device, bytes, sizeof(bytes), 20);
}

esp_err_t mpu6050_init(void) {
    i2c_master_bus_handle_t bus;
    i2c_master_bus_config_t config = {
        .i2c_port = I2C_NUM_0, .sda_io_num = CONFIG_HAR_SDA_GPIO,
        .scl_io_num = CONFIG_HAR_SCL_GPIO, .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7, .flags.enable_internal_pullup = true,
    };
    esp_err_t err = i2c_new_master_bus(&config, &bus);
    if (err != ESP_OK) return err;
    i2c_device_config_t dev = {.dev_addr_length = I2C_ADDR_BIT_LEN_7,
                              .device_address = 0x68, .scl_speed_hz = 400000};
    err = i2c_master_bus_add_device(bus, &dev, &device);
    if (err != ESP_OK) return err;
    uint8_t reg = 0x75, identity = 0;
    err = i2c_master_transmit_receive(device, &reg, 1, &identity, 1, 20);
    if (err != ESP_OK) return err;
    if (identity != 0x68) return ESP_ERR_NOT_FOUND;
    err = write_register(0x6B, 0x80);
    if (err != ESP_OK) return err;
    vTaskDelay(pdMS_TO_TICKS(100));
    // PLL gyro X, DLPF ~20 Hz (nao replica os filtros offline UCI), 1000/(19+1)=50 Hz.
    const uint8_t settings[][2] = {{0x6B, 0x01}, {0x1A, 0x04}, {0x19, 19}, {0x1B, 0}, {0x1C, 0}};
    for (unsigned i = 0; i < sizeof(settings) / sizeof(settings[0]); ++i) {
        err = write_register(settings[i][0], settings[i][1]);
        if (err != ESP_OK) return err;
    }
    vTaskDelay(pdMS_TO_TICKS(100));
    return ESP_OK;
}

esp_err_t mpu6050_read(float sample[6]) {
    uint8_t reg = 0x3B, bytes[14];
    esp_err_t err = i2c_master_transmit_receive(device, &reg, 1, bytes, sizeof(bytes), 10);
    if (err == ESP_OK) har_mpu_decode(bytes, sample);
    return err;
}
