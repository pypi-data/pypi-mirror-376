#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // Required for automatic type conversion
#include "randomizer.h"

namespace py = pybind11;

/**
 * @brief This is the main entry point for creating the Python module.
 * The module is named 'rng_cpp', as defined in the macro.
 * The 'm' variable is the module object.
 */
PYBIND11_MODULE(accel_mtrng, m) {
    m.doc() = "High-performance C++ random number generation library for Python";

    // Expose the pre-defined seed macros as module-level constants
    m.attr("LOW_SEED") = RNG_LOW_SEED;
    m.attr("HIGH_SEED") = RNG_HIGH_SEED;

    // --- Bind the MersenneTwister Class ---
    py::class_<RNG::MersenneTwister>(m, "MersenneTwister")
        .def(py::init<>(),
             "Default constructor. Seeds from random_device in release, "
             "fixed seed in debug.")
        .def(py::init<RNG::MersenneTwister::result_type>(),
             "Constructor with a specific seed value.", py::arg("seed"))

        .def("get_int", &RNG::MersenneTwister::get_int<int>,
             "Generates a random integer in [min, max].",
             py::arg("min"), py::arg("max"))
        .def("get_int", &RNG::MersenneTwister::get_int<long long>,
             "Generates a random 64-bit integer in [min, max].",
             py::arg("min"), py::arg("max"))

        .def("get_real", &RNG::MersenneTwister::get_real<float>,
             "Generates a random float in [min, max).",
             py::arg("min"), py::arg("max"))
        .def("get_real", &RNG::MersenneTwister::get_real<double>,
             "Generates a random double in [min, max).",
             py::arg("min"), py::arg("max"))

        .def("shuffle", [](RNG::MersenneTwister &self, std::vector<int> &v) {
                self.shuffle(v);
            }, "Randomly shuffles a list of integers in-place.",
               py::arg("container"))
        .def("shuffle", [](RNG::MersenneTwister &self, std::vector<double> &v) {
                self.shuffle(v);
            }, "Randomly shuffles a list of floats in-place.",
               py::arg("container"))
        
        .def("sample", &RNG::MersenneTwister::sample<std::vector<int>>,
             "Selects k unique integers from a list.",
             py::arg("container"), py::arg("k"))
        .def("sample", &RNG::MersenneTwister::sample<std::vector<double>>,
             "Selects k unique floats from a list.",
             py::arg("container"), py::arg("k"))
        
        .def("generate_int_list",
            [](RNG::MersenneTwister &self, size_t size, int min, int max) {
                std::vector<int> result(size);
                self.generate(result, min, max);
                return result;
            }, "Generates a list of random integers.",
               py::arg("size"), py::arg("min"), py::arg("max"))
        .def("generate_real_list",
            [](RNG::MersenneTwister &self, size_t size, double min, double max) {
                std::vector<double> result(size);
                self.generate(result, min, max);
                return result;
            }, "Generates a list of random doubles.",
               py::arg("size"), py::arg("min"), py::arg("max"));


    // --- Bind the Singleton Free Functions ---
    m.def("get_int", &RNG::get_int<int>,
          "Generates a random integer using the global instance.",
          py::arg("min"), py::arg("max"));
    m.def("get_int", &RNG::get_int<long long>,
          "Generates a random 64-bit integer using the global instance.",
          py::arg("min"), py::arg("max"));

    m.def("get_real", &RNG::get_real<float>,
          "Generates a random float using the global instance.",
          py::arg("min"), py::arg("max"));
    m.def("get_real", &RNG::get_real<double>,
          "Generates a random double using the global instance.",
          py::arg("min"), py::arg("max"));

    m.def("shuffle", [](std::vector<int> &v) { RNG::shuffle(v); },
          "Randomly shuffles a list of integers in-place using the global "
          "instance.", py::arg("container"));
    m.def("shuffle", [](std::vector<double> &v) { RNG::shuffle(v); },
          "Randomly shuffles a list of floats in-place using the global "
          "instance.", py::arg("container"));
          
    m.def("sample", &RNG::sample<std::vector<int>>,
          "Selects k unique integers from a list using the global instance.",
          py::arg("container"), py::arg("k"));
    m.def("sample", &RNG::sample<std::vector<double>>,
          "Selects k unique floats from a list using the global instance.",
          py::arg("container"), py::arg("k"));

    m.def("generate_int_list",
        [](size_t size, int min, int max) {
            std::vector<int> result(size);
            RNG::generate(result, min, max);
            return result;
        }, "Generates a list of random integers using the global instance.",
           py::arg("size"), py::arg("min"), py::arg("max"));
    
    m.def("generate_real_list",
        [](size_t size, double min, double max) {
            std::vector<double> result(size);
            RNG::generate(result, min, max);
            return result;
        }, "Generates a list of random doubles using the global instance.",
           py::arg("size"), py::arg("min"), py::arg("max"));
}