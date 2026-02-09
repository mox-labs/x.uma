//! puma-crusty — Python bindings for rumi via `PyO3`.
//!
//! Exposes rumi's matcher engine to Python as opaque compiled matchers.
//! Config in → compile in Rust → evaluate in Rust → simple types out.

mod config;
mod convert;
mod matcher;

use pyo3::prelude::*;

/// Python module: `puma_crusty`
#[pymodule]
fn puma_crusty(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Config types
    m.add_class::<config::PyStringMatch>()?;
    m.add_class::<config::PyHookMatch>()?;

    // Compiled matchers
    m.add_class::<matcher::HookMatcher>()?;

    // Trace types
    m.add_class::<matcher::PyTraceResult>()?;
    m.add_class::<matcher::PyTraceStep>()?;

    Ok(())
}
