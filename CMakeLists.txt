cmake_minimum_required(VERSION 3.25)
project(HCSMovieForgeNative VERSION 0.1.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Option to build native third-party integration helpers if required
option(BUILD_MOVIEFORGE_NATIVE_HELPERS "Build native C/C++ integration helpers" OFF)

message(STATUS "HCS MovieForge Native Integration Layer initialized.")
