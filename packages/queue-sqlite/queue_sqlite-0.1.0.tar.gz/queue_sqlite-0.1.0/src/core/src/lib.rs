mod queue_operation;
mod task_mounter;

use pyo3::prelude::*;
use queue_operation::QueueOperation;
use task_mounter::TaskMounter; // 导入结构体 // 导入结构体

#[pymodule]
fn core(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<TaskMounter>()?;
    m.add_class::<QueueOperation>()?;
    Ok(())
}
