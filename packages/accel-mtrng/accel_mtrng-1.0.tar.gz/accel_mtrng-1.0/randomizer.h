#pragma once

#include <random>
#include <array>
#include <functional>
#include <type_traits>
#include <limits>
#include <algorithm>
#include <vector>
#include <iterator>

#define RNG_LOW_SEED 1
#define RNG_HIGH_SEED std::numeric_limits<unsigned int>::max()

namespace RNG {

/**
 * @class MersenneTwister
 * @brief A wrapper around the standard C++ Mersenne Twister engine, providing a 
 * convenient interface for common random number generation tasks.
 * * This class automatically selects the 64-bit or 32-bit version of the engine
 * based on the target architecture at compile time. It also handles robust
 * seeding for release builds and deterministic seeding for debug builds.
 */
class MersenneTwister {
public:

#if defined(__x86_64__) || defined(_M_X64) || defined(__aarch64__)
    /** @brief The underlying generator type; std::mt19937_64 on 64-bit systems. */
    using GeneratorType = std::mt19937_64;
#else
    /** @brief The underlying generator type; std::mt19937 on 32-bit systems. */
    using GeneratorType = std::mt19937;
#endif
    /** @brief The result type of the generator (e.g., uint64_t or uint32_t). */
    using result_type = GeneratorType::result_type;

    /**
     * @brief Default constructor.
     * In release builds (NDEBUG defined), seeds the generator with high-quality
     * entropy from std::random_device. In debug builds, uses a fixed default seed
     * for reproducible results.
     */
    MersenneTwister();

    /**
     * @brief Constructs and seeds the generator with a specific value.
     * @param seed The value to seed the random number engine with.
     */
    explicit MersenneTwister(result_type seed);

    /**
     * @brief Generates a random integer within a specified range [min, max].
     * @tparam T An integral type (e.g., int, long, size_t).
     * @param min The minimum value of the range (inclusive).
     * @param max The maximum value of the range (inclusive).
     * @return A random integer of type T.
     */
    template <typename T>
    T get_int(T min, T max) {
        static_assert(std::is_integral_v<T>,
            "Template argument T must be an integral type.");
        using dist_type = std::uniform_int_distribution<T>;
        using param_type = typename dist_type::param_type;
        static dist_type dist;
        return dist(_rng, param_type(min, max));
    }

    /**
     * @brief Generates a random floating-point number within a specified range [min, max).
     * @tparam T A floating-point type (e.g., float, double).
     * @param min The minimum value of the range (inclusive).
     * @param max The maximum value of the range (exclusive).
     * @return A random floating-point number of type T.
     */
    template <typename T>
    T get_real(T min, T max) {
        static_assert(std::is_floating_point_v<T>,
            "Template argument T must be a floating-point type.");
        using dist_type = std::uniform_real_distribution<T>;
        using param_type = typename dist_type::param_type;
        static dist_type dist;
        return dist(_rng, param_type(min, max));
    }

    /**
     * @brief Randomly shuffles the elements of a container in-place.
     * @tparam Container The type of the container (e.g., std::vector, std::array).
     * @param container The container to shuffle.
     */
    template <typename Container>
    void shuffle(Container& container) {
        std::shuffle(container.begin(), container.end(), _rng);
    }

    /**
     * @brief Selects k unique elements from a range
     * and writes them to an output iterator.
     * @tparam InputIt The type of the input iterator.
     * @tparam OutputIt The type of the output iterator.
     * @param first The beginning of the input range.
     * @param last The end of the input range.
     * @param out The output iterator to write the results to.
     * @param k The number of elements to sample.
     */
    template<typename InputIt, typename OutputIt>
    void sample(InputIt first, InputIt last, OutputIt out, size_t k) {
        std::sample(first, last, out, k, _rng);
    }

    /**
     * @brief Selects k unique elements from a container.
     * @tparam Container The type of the input container.
     * @param container The container to sample from.
     * @param k The number of elements to sample.
     * @return A std::vector containing the k sampled elements.
     */
    template <typename Container>
    std::vector<typename Container::value_type>
    sample(const Container& container, size_t k) {
        std::vector<typename Container::value_type> result;
        if (k > 0) {
            result.reserve(k);
            sample(container.begin(), container.end(), std::back_inserter(result), k);
        }
        return result;
    }

    /**
     * @brief Fills a container with random numbers in a specified range.
     * @tparam Container The type of the container.
     * @param container The container to fill.
     * @param min The minimum value for the generated numbers.
     * @param max The maximum value for the generated numbers.
     */
    template <typename Container>
    void generate(Container& container,
        typename Container::value_type min, typename Container::value_type max) {
        using T = typename Container::value_type;
        if constexpr (std::is_integral_v<T>) {
            std::uniform_int_distribution<T> dist(min, max);
            std::generate(container.begin(), container.end(),
            [&]() { return dist(_rng); });
        } else if constexpr (std::is_floating_point_v<T>) {
            std::uniform_real_distribution<T> dist(min, max);
            std::generate(container.begin(), container.end(),
            [&]() { return dist(_rng); });
        }
    }

private:
    GeneratorType _rng;
};


namespace internal {
    /**
     * @brief Provides access to a single, shared instance of MersenneTwister.
     * @return A reference to the singleton instance.
     */
    inline MersenneTwister& get_singleton_instance() {
        static MersenneTwister instance;
        return instance;
    }
}

/** @brief Free function wrapper for get_int using the singleton instance. */
template <typename T>
T get_int(T min, T max) {
    return internal::get_singleton_instance().get_int(min, max);
}

/** @brief Free function wrapper for get_real using the singleton instance. */
template <typename T>
T get_real(T min, T max) {
    return internal::get_singleton_instance().get_real(min, max);
}

/** @brief Free function wrapper for shuffle using the singleton instance. */
template <typename Container>
void shuffle(Container& container) {
    internal::get_singleton_instance().shuffle(container);
}

/** @brief Free function wrapper for sample using the singleton instance. */
template <typename Container>
std::vector<typename Container::value_type>
sample(const Container& container, size_t k) {
    return internal::get_singleton_instance().sample(container, k);
}

/** @brief Free function wrapper for generate using the singleton instance. */
template <typename Container>
void generate(Container& container,
    typename Container::value_type min, typename Container::value_type max) {
    internal::get_singleton_instance().generate(container, min, max);
}

} // namespace RNG