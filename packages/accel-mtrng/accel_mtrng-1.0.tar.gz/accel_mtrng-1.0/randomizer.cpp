#include "randomizer.h"

namespace RNG {

MersenneTwister::MersenneTwister() {
#if defined(NDEBUG)
    std::random_device rd;
    std::array<result_type, GeneratorType::state_size / 2> seed_data;
    std::generate(seed_data.begin(), seed_data.end(), std::ref(rd));
    std::seed_seq seq(seed_data.begin(), seed_data.end());
    _rng.seed(seq);
#else
    _rng.seed(GeneratorType::default_seed);
#endif
}

MersenneTwister::MersenneTwister(result_type seed) {
    _rng.seed(seed);
}

} // namespace RNG
