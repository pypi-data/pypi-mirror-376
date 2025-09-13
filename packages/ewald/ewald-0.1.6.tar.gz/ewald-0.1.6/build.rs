//! We use this to automatically compile CUDA C++ code when building.

#[cfg(feature = "cuda")]
use cuda_setup::{GpuArchitecture, build_host};

fn main() {
    #[cfg(feature = "cuda")]
    build_host(
        // Select the min supported GPU architecture.
        GpuArchitecture::Rtx3,
        &["src/cuda/spme.cu"],
        "spme", // This name is currently hard-coded in the Ewald lib.
    )
}
