idf_component_register(SRCS "har_features.c" INCLUDE_DIRS "include")
target_compile_options(${COMPONENT_LIB} PRIVATE -ffp-contract=off -fno-fast-math)
