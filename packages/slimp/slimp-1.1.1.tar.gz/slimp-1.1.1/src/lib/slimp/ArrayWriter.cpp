#include "ArrayWriter.h"

#include <cstdint>
#include <string>
#include <vector>

// WARNING: Stan must be included before Eigen so that the plugin system is
// active. https://discourse.mc-stan.org/t/includes-in-user-header/26093
#include <stan/math.hpp>

#include <Eigen/Dense>
#include <stan/callbacks/writer.hpp>
#if __has_include(<xtensor/xtensor.hpp>)
#include <xtensor/xadapt.hpp>
#include <xtensor/xslice.hpp>
#include <xtensor/xview.hpp>
#else
#include <xtensor/containers/xadapt.hpp>
#include <xtensor/views/xslice.hpp>
#include <xtensor/views/xview.hpp>
#endif

namespace slimp
{

ArrayWriter
::ArrayWriter(Array & array, size_t chain, size_t offset, size_t skip)
: _array(array), _chain(chain), _offset(offset), _skip(skip), _draw(0), _names()
{
    // Nothing else
}

void
ArrayWriter
::operator()(std::vector<std::string> const & names)
{
    // NOTE: names are informative, don't check their size    
    this->_names = names;
}

void
ArrayWriter
::operator()(std::vector<double> const & state)
{
    this->_write_1d_container(state);
}

void
ArrayWriter
::operator()(std::string const & message)
{
    this->_messages[this->_draw].push_back(message);
}

void
ArrayWriter
#if STAN_MAJOR < 2 || STAN_MAJOR == 2 && STAN_MINOR <= 36
::operator()(Eigen::Ref<Eigen::Matrix<double, -1, -1>> const & values)
#else
::operator()(Eigen::Matrix<double, -1, -1> const & values)
#endif
{
    using namespace xt::placeholders;
    
    // From Stan documentation, "The input is expected to have parameters in the
    // rows and samples in the columns".
    
    auto const draws = values.cols();
    
    auto const source = xt::view(
        xt::adapt<xt::layout_type::column_major>(
            values.data(), values.size(), xt::no_ownership(),
            std::vector<long>{values.rows(), values.cols()}),
        xt::range(this->_skip, _), xt::all());
    
    auto target = xt::view(
        this->_array, xt::range(this->_offset, _), this->_chain,
        xt::range(this->_draw, this->_draw+draws));
    
    target = source;
    
    this->_draw += draws;
}

#if !(STAN_MAJOR < 2 || STAN_MAJOR == 2 && STAN_MINOR <= 36)
void
ArrayWriter
::operator()(Eigen::Matrix<double, -1, 1> const & values)
{
    this->_write_1d_container(values);
}

void
ArrayWriter
::operator()(Eigen::Matrix<double, 1, -1> const & values)
{
    this->_write_1d_container(values);
}
#endif

std::vector<std::string> const &
ArrayWriter
::names() const
{
    return this->_names;
}

}
