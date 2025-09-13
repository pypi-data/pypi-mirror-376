#ifndef X3CFLUX_SYSTEMTRAITS_H
#define X3CFLUX_SYSTEMTRAITS_H

#include <math/NumericTypes.h>
#include <model/network/CumomerMethod.h>
#include <model/network/EMUMethod.h>
#include <model/network/IsotopomerMethod.h>

namespace x3cflux {

/// \brief Type of numeric system
enum SystemType {
    NONLINEAR,
    CASCADED,
};

/// \brief System properties (type of fraction, state or linear reducibility)
/// \tparam Method labeling state simulation method
/// \tparam Multi multiple or single experiment
template <typename Method, bool Multi> struct SystemTraits;

template <bool Multi> struct SystemTraits<IsotopomerMethod, Multi> {
    using FractionType = typename std::conditional_t<Multi, RealVector, Real>;
    using SystemStateType = typename std::conditional_t<Multi, RealMatrix, RealVector>;

    constexpr static SystemType TYPE = SystemType::NONLINEAR;
};

template <bool Multi> struct SystemTraits<CumomerMethod, Multi> {
    using FractionType = typename std::conditional_t<Multi, RealVector, Real>;
    using SystemStateType = typename std::conditional_t<Multi, RealMatrix, RealVector>;

    constexpr static SystemType TYPE = SystemType::CASCADED;
};

template <bool Multi> struct SystemTraits<EMUMethod, Multi> {
    using FractionType = RealVector;
    using SystemStateType = RealMatrix;

    constexpr static SystemType TYPE = SystemType::CASCADED;
};

} // namespace x3cflux

#endif // X3CFLUX_SYSTEMTRAITS_H
