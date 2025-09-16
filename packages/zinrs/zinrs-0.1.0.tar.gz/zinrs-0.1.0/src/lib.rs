use pyo3::prelude::*;

/// Formats the sum of two numbers as string.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

#[pyfunction]
fn is_odd(a: usize) -> PyResult<bool> {
    return Ok(a == 1);
}

/// A Python module implemented in Rust.
#[pymodule]
fn zinrs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    m.add_function(wrap_pyfunction!(is_odd, m)?)?; 
    Ok(())
}
