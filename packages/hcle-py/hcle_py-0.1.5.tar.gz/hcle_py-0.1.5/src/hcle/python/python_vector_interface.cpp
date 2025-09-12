#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include "hcle/environment/hcle_vector_environment.hpp"

#include <vector>

namespace py = pybind11;

void init_vector_bindings(py::module_ &m)
{
     py::class_<hcle::environment::HCLEVectorEnvironment>(m, "HCLEVectorEnvironment")
         .def(py::init<int, std::string, std::string, std::string, int, int, int, bool, bool, int, bool>(),
              py::arg("num_envs"),
              py::arg("data_root_dir"),
              py::arg("game_name"),
              py::arg("render_mode") = "rgb_array",
              py::arg("obs_height") = 84,
              py::arg("obs_width") = 84,
              py::arg("frame_skip") = 4,
              py::arg("maxpool") = false,
              py::arg("grayscale") = true,
              py::arg("stack_num") = 4,
              py::arg("color_index_grayscale") = false)
         .def_property_readonly("num_envs", &hcle::environment::HCLEVectorEnvironment::getNumEnvs)
         // --- Helper functions for Python wrapper ---
         .def("getActionSet", &hcle::environment::HCLEVectorEnvironment::getActionSet,
              "Returns the set of valid actions for the environment.")
         .def("getObservationSize", &hcle::environment::HCLEVectorEnvironment::getObservationSize,
              "Returns the total size in bytes of a single stacked observation.")
         // --- Core API ---
         .def("reset", [](hcle::environment::HCLEVectorEnvironment &self, py::array_t<uint8_t> obs_np, py::array_t<double> rewards_np, py::array_t<uint8_t> dones_np)
              {
        auto *obs_ptr = static_cast<uint8_t *>(obs_np.mutable_data());
        auto *rewards_ptr = static_cast<double *>(rewards_np.mutable_data());
        auto *dones_ptr = static_cast<uint8_t *>(dones_np.mutable_data());

        py::gil_scoped_release release;
        self.reset(obs_ptr, rewards_ptr, dones_ptr); }, py::arg("obs").noconvert(), py::arg("rewards").noconvert(), py::arg("dones").noconvert())
         .def("send", [](hcle::environment::HCLEVectorEnvironment &self, py::array_t<uint8_t> actions)
              {
                   // Create a no-copy view of the numpy array data
                   py::buffer_info actions_buf = actions.request();
                   auto *actions_ptr = static_cast<uint8_t *>(actions_buf.ptr);
                   std::vector<uint8_t> actions_vec(actions_ptr, actions_ptr + actions.size());

                   // Release GIL to allow C++ threads to run in the background
                   py::gil_scoped_release release;
                   self.send(actions_vec);
                   // GIL is re-acquired automatically
              },
              py::arg("actions").noconvert(), "Sends a batch of actions to the environments to be executed.")

         .def("recv", [](hcle::environment::HCLEVectorEnvironment &self, py::array_t<uint8_t> obs_np, py::array_t<double> rewards_np, py::array_t<uint8_t> dones_np)
              {
                   // Get pointers to the NumPy array data
                   auto *obs_ptr = static_cast<uint8_t *>(obs_np.mutable_data());
                   auto *rewards_ptr = static_cast<double *>(rewards_np.mutable_data());
                   auto *dones_ptr = static_cast<uint8_t *>(dones_np.mutable_data());

                   // Release the GIL while waiting for C++ threads to finish
                   py::gil_scoped_release release;
                   self.recv(obs_ptr, rewards_ptr, dones_ptr);
                   // GIL is re-acquired automatically
              },
              py::arg("obs").noconvert(), py::arg("rewards").noconvert(), py::arg("dones").noconvert(), "Waits for the step to complete and writes the results (obs, rewards, dones) into the provided NumPy arrays.");
}