cmake_minimum_required(VERSION 3.16)
project(ar_aipet_espnow_controller LANGUAGES C CXX)

add_library(controller_core
    core/controller_protocol.c
    core/controller_state.c
)
target_include_directories(controller_core PUBLIC core)

add_executable(controller_test tests/controller_test.cpp)
target_link_libraries(controller_test PRIVATE controller_core)
target_compile_features(controller_test PRIVATE cxx_std_17)

enable_testing()
add_test(NAME controller_state_and_protocol COMMAND controller_test)
