#pragma once

// C/C+
#include <functional>

// torch
#include <torch/torch.h>

namespace snap {
// linear interp, equally weighted from left (x(xmin)=-0.5) and right
// (x(xmax)=0.5)
torch::Tensor UniformMesh(torch::Tensor x, float xmin, float xmax);

//! Compute the logical position of a cell given its index and the number of
//! cells in the range.
torch::Tensor compute_logical_position(torch::Tensor index, int64_t nrange,
                                       bool sym_interval);

using MeshGenerator = std::function<torch::Tensor(torch::Tensor, float, float)>;
}  // namespace snap
