if(NOT EXISTS "${CMAKE_CURRENT_LIST_DIR}/generated/model_data.cc")
    message(FATAL_ERROR "Modelo ausente: execute python -m ml.src.export na raiz do repositorio")
endif()
idf_component_register(SRCS "app_main.cpp" "mpu6050.c" "inference.cpp" "generated/model_data.cc"
    INCLUDE_DIRS "." "generated"
    REQUIRES har_core esp_timer esp_driver_i2c esp-tflite-micro)
target_compile_options(${COMPONENT_LIB} PRIVATE -ffp-contract=off -fno-fast-math)
