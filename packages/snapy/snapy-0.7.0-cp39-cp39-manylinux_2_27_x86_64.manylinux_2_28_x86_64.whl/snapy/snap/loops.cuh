// torch
#include <ATen/TensorIterator.h>
#include <ATen/native/ReduceOpsUtils.h>

#include <ATen/native/cuda/Loops.cuh>

namespace snap {
namespace native {

template <int N>
void _left_shift(int arr[N], int k) {
  // Normalize k to [0, N-1]
  k %= N;
  if (k < 0) k += N;
  if (k == 0) return;

  // Perform k single-position left rotations
  for (int shift = 0; shift < k; ++shift) {
    int tmp = arr[0];
    arr[0] = arr[1];
    arr[1] = arr[2];
    arr[2] = tmp;
  }
}

template <typename scalar_t, typename func_t>
__global__ void reduce_kernel(int64_t numel, func_t f) {
  int x = threadIdx.x + blockIdx.x * blockDim.x;
  int y = threadIdx.y + blockIdx.y * blockDim.y;
  int z = threadIdx.z + blockIdx.z * blockDim.z;

  int tid = x + y * blockDim.x * gridDim.x +
            z * blockDim.x * blockDim.y * gridDim.x * gridDim.y;

  int bid =
      blockIdx.x + blockIdx.y * gridDim.x + blockIdx.z * gridDim.x * gridDim.y;

  // Shared memory allocation
  extern __shared__ unsigned char memory[];
  scalar_t* smem = reinterpret_cast<scalar_t*>(memory);

  if (tid < numel) {
    f(bid, smem);
  }
}

template <int Arity, typename func_t>
void gpu_kernel(at::TensorIterator& iter, const func_t& f) {
  TORCH_CHECK(iter.ninputs() + iter.noutputs() == Arity);

  std::array<char*, Arity> data;
  for (int i = 0; i < Arity; i++) {
    data[i] = (char*)iter.data_ptr(i);
  }

  auto offset_calc = ::make_offset_calculator<Arity>(iter);
  int64_t numel = iter.numel();

  at::native::launch_legacy_kernel<128, 1>(numel, [=] __device__(int idx) {
    auto offsets = offset_calc.get(idx);
    f(data.data(), offsets.data());
  });
}

template <typename scalar_t, int Arity, typename func_t>
void stencil_kernel(at::TensorIterator& iter, int dim, int buffers,
                    const func_t& f) {
  TORCH_CHECK(iter.ninputs() + iter.noutputs() == Arity);

  std::array<char*, Arity> data;
  for (int i = 0; i < Arity; i++) {
    data[i] = (char*)iter.data_ptr(i);
  }

  auto offset_calc = ::make_offset_calculator<Arity>(iter);
  int64_t numel = iter.input().numel();

  TORCH_INTERNAL_ASSERT(numel >= 0 &&
                        numel <= std::numeric_limits<int32_t>::max());
  if (numel == 0) {
    return;
  }

  ////// prepare to launch elementwise kernel  /////

  int len[3] = {1, 1, 1};
  int ndim = iter.input().dim();
  len[3 + dim - ndim] = at::native::ensure_nonempty_size(iter.input(), dim);
  _left_shift<3>(len, dim + 1 - ndim);

  dim3 block(len[2], len[1], len[0]);

  // get dimensions
  if (ndim <= 3) {
    len[3 - ndim] = at::native::ensure_nonempty_size(iter.input(), 0);
  }

  for (int i = 1; i < ndim; ++i) {
    len[3 + i - ndim] = at::native::ensure_nonempty_size(iter.input(), i);
  }
  _left_shift<3>(len, dim + 1 - ndim);

  dim3 grid(len[2] / block.x, len[1] / block.y, len[0] / block.z);

  // number of variables
  int nvar = at::native::ensure_nonempty_size(iter.output(), 0);
  size_t shared = (block.x * nvar + buffers) * sizeof(scalar_t);

  auto stream = at::cuda::getCurrentCUDAStream();

  reduce_kernel<scalar_t><<<grid, block, shared, stream>>>(
      numel, [=] __device__(int bid, scalar_t* smem) {
        auto offsets = offset_calc.get(bid);
        f(data.data(), offsets.data(), smem);
      });

  C10_CUDA_KERNEL_LAUNCH_CHECK();
  ////// kernel launched /////
}

}  // namespace native
}  // namespace snap
