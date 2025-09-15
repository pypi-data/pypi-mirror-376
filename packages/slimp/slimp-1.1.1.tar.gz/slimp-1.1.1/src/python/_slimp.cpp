// WARNING: Stan must be included before Eigen so that the plugin system is
// active. https://discourse.mc-stan.org/t/includes-in-user-header/26093
#include <stan/math.hpp>

#include <pybind11/eigen.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#define FORCE_IMPORT_ARRAY
#include <xtensor-python/pyarray.hpp>
#include <xtensor-python/pytensor.hpp>

#include "slimp/action_parameters.h"
#include "slimp/actions.h"

#include "multilevel/predict_prior.h"
#include "multilevel/predict_posterior.h"
#include "multilevel/sampler.h"

#include "multivariate/log_likelihood.h"
#include "multivariate/predict_posterior.h"
#include "multivariate/predict_prior.h"
#include "multivariate/sampler.h"

#include "univariate/log_likelihood.h"
#include "univariate/predict_posterior.h"
#include "univariate/predict_prior.h"
#include "univariate/sampler.h"

#define REGISTER_SAMPLER(name) \
    module.def(\
        #name "_sampler", \
        &slimp::sample<name##_sampler::model>);
#define REGISTER_GQ(name, quantity) \
    module.def( \
        #name "_" #quantity, \
        &slimp::generate_quantities<name##_##quantity::model>);
#define REGISTER_ALL(name) \
    REGISTER_SAMPLER(name) \
    REGISTER_GQ(name, log_likelihood); \
    REGISTER_GQ(name, predict_posterior); \
    REGISTER_GQ(name, predict_prior);

#define SET_FROM_KWARGS(kwargs, name, object, type) \
    if(kwargs.contains(#name)) { object.name = kwargs[#name].cast<type>(); }

PYBIND11_MODULE(_slimp, module)
{
    xt::import_numpy();
    
    auto action_parameters_ = module.def_submodule("action_parameters");
    
    auto adapt_pickler = std::make_pair(
        [](slimp::action_parameters::Adapt const & self){
            pybind11::dict state;
            
            state["engaged"] = self.engaged;
            state["gamma"] = self.gamma;
            state["delta"] = self.delta;
            state["kappa"] = self.kappa;
            state["t0"] = self.t0;
            state["init_buffer"] = self.init_buffer;
            state["term_buffer"] = self.term_buffer;
            state["window"] = self.window;
            state["save_metric"] = self.save_metric;
            
            return state;
        },
        [](pybind11::dict state) {
            slimp::action_parameters::Adapt self;
            
            self.engaged = state["engaged"].cast<bool>();
            self.gamma = state["gamma"].cast<double>();
            self.delta = state["delta"].cast<double>();
            self.kappa = state["kappa"].cast<double>();
            self.t0 = state["t0"].cast<double>();
            self.init_buffer = state["init_buffer"].cast<unsigned int>();
            self.term_buffer = state["term_buffer"].cast<unsigned int>();
            self.window = state["window"].cast<unsigned int>();
            self.save_metric = state["save_metric"].cast<bool>();
            
            return self;
        });
    pybind11::class_<slimp::action_parameters::Adapt>(
            action_parameters_, "Adapt")
        .def(pybind11::init<>())
        .def(pybind11::init(
            [](pybind11::kwargs kwargs) {
                slimp::action_parameters::Adapt x;
                SET_FROM_KWARGS(kwargs, engaged, x, bool)
                SET_FROM_KWARGS(kwargs, gamma, x, double)
                SET_FROM_KWARGS(kwargs, delta, x, double)
                SET_FROM_KWARGS(kwargs, kappa, x, double)
                SET_FROM_KWARGS(kwargs, t0, x, double)
                SET_FROM_KWARGS(kwargs, init_buffer, x, unsigned int)
                SET_FROM_KWARGS(kwargs, term_buffer, x, unsigned int)
                SET_FROM_KWARGS(kwargs, window, x, unsigned int)
                SET_FROM_KWARGS(kwargs, save_metric, x, bool)
                return x;}))
        .def_readwrite("engaged", &slimp::action_parameters::Adapt::engaged)
        .def_readwrite("gamma", &slimp::action_parameters::Adapt::gamma)
        .def_readwrite("delta", &slimp::action_parameters::Adapt::delta)
        .def_readwrite("kappa", &slimp::action_parameters::Adapt::kappa)
        .def_readwrite("t0", &slimp::action_parameters::Adapt::t0)
        .def_readwrite(
            "init_buffer", &slimp::action_parameters::Adapt::init_buffer)
        .def_readwrite(
            "term_buffer", &slimp::action_parameters::Adapt::term_buffer)
        .def_readwrite("window", &slimp::action_parameters::Adapt::window)
        .def_readwrite(
            "save_metric", &slimp::action_parameters::Adapt::save_metric)
        .def(pybind11::pickle(adapt_pickler.first, adapt_pickler.second));
    
    auto const hmc_pickler = std::make_pair(
        [](slimp::action_parameters::HMC const & self){
            pybind11::dict state;
            
            state["int_time"] = self.int_time;
            state["max_depth"] = self.max_depth;
            state["stepsize"] = self.stepsize;
            state["stepsize_jitter"] = self.stepsize_jitter;
            
            return state;
        },
        [](pybind11::dict state){
            slimp::action_parameters::HMC self;
            
            self.int_time = state["int_time"].cast<double>();
            self.max_depth = state["max_depth"].cast<int>();
            self.stepsize = state["stepsize"].cast<double>();
            self.stepsize_jitter = state["stepsize_jitter"].cast<double>();
            
            return self;
        });
    pybind11::class_<slimp::action_parameters::HMC>(action_parameters_, "HMC")
        .def(pybind11::init<>())
        .def(pybind11::init(
            [](pybind11::kwargs kwargs) {
                slimp::action_parameters::HMC x;
                SET_FROM_KWARGS(kwargs, int_time, x, double)
                SET_FROM_KWARGS(kwargs, max_depth, x, int)
                SET_FROM_KWARGS(kwargs, stepsize, x, double)
                SET_FROM_KWARGS(kwargs, stepsize_jitter, x, double)
                return x;}))
        .def_readwrite("int_time", &slimp::action_parameters::HMC::int_time)
        .def_readwrite("max_depth", &slimp::action_parameters::HMC::max_depth)
        .def_readwrite("stepsize", &slimp::action_parameters::HMC::stepsize)
        .def_readwrite(
            "stepsize_jitter", &slimp::action_parameters::HMC::stepsize_jitter)
        .def(pybind11::pickle(hmc_pickler.first, hmc_pickler.second));
    
    pybind11::class_<slimp::action_parameters::Sample>(
            action_parameters_, "Sample")
        .def(pybind11::init<>())
        .def(pybind11::init(
            [](pybind11::kwargs kwargs) {
                slimp::action_parameters::Sample x;
                SET_FROM_KWARGS(kwargs, num_samples, x, int)
                SET_FROM_KWARGS(kwargs, num_warmup, x, int)
                SET_FROM_KWARGS(kwargs, save_warmup, x, bool)
                SET_FROM_KWARGS(kwargs, thin, x, int)
                SET_FROM_KWARGS(
                    kwargs, adapt, x, slimp::action_parameters::Adapt)
                SET_FROM_KWARGS(kwargs, hmc, x, slimp::action_parameters::HMC)
                SET_FROM_KWARGS(kwargs, num_chains, x, size_t)
                SET_FROM_KWARGS(kwargs, seed, x, long)
                SET_FROM_KWARGS(kwargs, id, x, int)
                SET_FROM_KWARGS(kwargs, init_radius, x, double)
                SET_FROM_KWARGS(kwargs, refresh, x, int)
                SET_FROM_KWARGS(kwargs, sequential_chains, x, bool)
                SET_FROM_KWARGS(kwargs, threads_per_chain, x, unsigned int)
                return x;}))
        .def_readwrite(
            "num_samples", &slimp::action_parameters::Sample::num_samples)
        .def_readwrite(
            "num_warmup", &slimp::action_parameters::Sample::num_warmup)
        .def_readwrite(
            "save_warmup", &slimp::action_parameters::Sample::save_warmup)
        .def_readwrite("thin", &slimp::action_parameters::Sample::thin)
        .def_readwrite("adapt", &slimp::action_parameters::Sample::adapt)
        .def_readwrite("hmc", &slimp::action_parameters::Sample::hmc)
        .def_readwrite(
            "num_chains", &slimp::action_parameters::Sample::num_chains)
        .def_readwrite("seed", &slimp::action_parameters::Sample::seed)
        .def_readwrite("id", &slimp::action_parameters::Sample::id)
        .def_readwrite(
            "init_radius", &slimp::action_parameters::Sample::init_radius)
        .def_readwrite(
            "refresh", &slimp::action_parameters::Sample::refresh)
        .def_readwrite(
            "sequential_chains",
            &slimp::action_parameters::Sample::sequential_chains)
        .def_readwrite(
            "threads_per_chain",
            &slimp::action_parameters::Sample::threads_per_chain)
        .def(pybind11::pickle(
            [&](slimp::action_parameters::Sample const & self) {
                pybind11::dict state;
                
                state["num_samples"] = self.num_samples;
                state["num_warmup"] = self.num_warmup;
                state["save_warmup"] = self.save_warmup;
                state["thin"] = self.thin;
                state["adapt"] = adapt_pickler.first(self.adapt);
                state["hmc"] = hmc_pickler.first(self.hmc);
                state["num_chains"] = self.num_chains;
                state["seed"] = self.seed;
                state["id"] = self.id;
                state["init_radius"] = self.init_radius;
                state["refresh"] = self.refresh;
                state["sequential_chains"] = self.sequential_chains;
                state["threads_per_chain"] = self.threads_per_chain;
                
                return state;
            },
            [&](pybind11::dict const & state) {
                slimp::action_parameters::Sample self;
                
                self.num_samples = state["num_samples"].cast<int>();
                self.num_warmup = state["num_warmup"].cast<int>();
                self.save_warmup = state["save_warmup"].cast<bool>();
                self.thin = state["thin"].cast<int>();
                self.adapt = adapt_pickler.second(state["adapt"]);
                self.hmc = hmc_pickler.second(state["hmc"]);
                self.num_chains = state["num_chains"].cast<size_t>();
                self.seed = state["seed"].cast<long>();
                self.id = state["id"].cast<int>();
                self.init_radius = state["init_radius"].cast<double>();
                self.refresh = state["refresh"].cast<int>();
                self.sequential_chains =
                    state["sequential_chains"].cast<bool>();
                self.threads_per_chain =
                    state["threads_per_chain"].cast<unsigned int>();
                
                return self;
            }));
    
    REGISTER_ALL(univariate);
    REGISTER_ALL(multivariate);
    REGISTER_SAMPLER(multilevel);
    REGISTER_GQ(multilevel, predict_posterior);
    REGISTER_GQ(multilevel, predict_prior);
    
    module.def(
        "get_effective_sample_size",
        pybind11::overload_cast<xt::xtensor<double, 3> const &>(
            &slimp::get_effective_sample_size));
    module.def(
        "get_effective_sample_size",
        pybind11::overload_cast<xt::xtensor<double, 4> const &>(
            &slimp::get_effective_sample_size));
    module.def(
        "get_potential_scale_reduction",
        pybind11::overload_cast<xt::xtensor<double, 3> const &>(
            &slimp::get_potential_scale_reduction));
    module.def(
        "get_potential_scale_reduction",
        pybind11::overload_cast<xt::xtensor<double, 4> const &>(
            &slimp::get_potential_scale_reduction));
    module.def(
        "get_split_potential_scale_reduction",
        pybind11::overload_cast<xt::xtensor<double, 3> const &>(
            &slimp::get_split_potential_scale_reduction));
    module.def(
        "get_split_potential_scale_reduction",
        pybind11::overload_cast<xt::xtensor<double, 4> const &>(
            &slimp::get_split_potential_scale_reduction));
}
