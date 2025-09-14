use chrono::{DateTime, Duration, Utc};
use pyo3::prelude::*;
use pyo3::types::*;
use r2d2::Pool;
use r2d2_sqlite::SqliteConnectionManager;
use rusqlite::params;

#[pyclass]
pub struct QueueOperation {
    pool: Pool<SqliteConnectionManager>,
}

#[pymethods]
impl QueueOperation {
    #[new]
    pub fn new(queue_path: String) -> Self {
        let manager = SqliteConnectionManager::file(queue_path.as_str());
        let pool = Pool::new(manager).unwrap();
        QueueOperation { pool }
    }

    pub fn init_db(&self) -> PyResult<()> {
        let conn = self
            .pool
            .get()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        conn.execute(
            "
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status INTEGER NOT NULL,
                content TEXT NOT NULL,
                createtime DATETIME NOT NULL,
                updatetime DATETIME NOT NULL,
                result TEXT DEFAULT NULL,
                priority INTEGER NOT NULL,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                retry_count INTEGER NOT NULL,
                expire_time DATETIME DEFAULT NULL,
                tags TEXT DEFAULT NULL,
                metadata TEXT DEFAULT NULL,
                is_deleted INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_status ON messages(status);
            CREATE INDEX IF NOT EXISTS idx_priority ON messages(priority);
            CREATE INDEX IF NOT EXISTS idx_dequeue ON messages(
                status, 
                priority DESC, 
                createtime ASC
            ) WHERE is_deleted = 0 AND status = 0;
            ",
            params![],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let pragmas = [
            "PRAGMA journal_mode=WAL",
            "PRAGMA synchronous=NORMAL",
            "PRAGMA cache_size=-20000",
            "PRAGMA mmap_size=1073741824",
            "PRAGMA temp_store=MEMORY",
            "PRAGMA busy_timeout=5000",
        ];
        for pragma in pragmas.iter() {
            let mut stmt = conn
                .prepare(pragma)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

            let mut rows = stmt
                .query([])
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

            while let Some(_) = rows
                .next()
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?
            {
            }
        }
        Ok(())
    }

    pub fn enqueue<'py>(
        &self,
        py: Python<'py>,
        message: &Bound<'py, PyDict>,
    ) -> PyResult<Bound<'py, PyString>> {
        let mut conn = self
            .pool
            .get()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let get_field = |key: &str| -> PyResult<_> {
            message.get_item(key)?.ok_or_else(|| {
                PyErr::new::<pyo3::exceptions::PyKeyError, _>(format!("{} not found", key))
            })
        };

        let id = get_field("id")?.extract::<String>()?;
        let type_ = get_field("type")?.extract::<String>()?;
        let status = get_field("status")?.extract::<i32>()?;
        let content = get_field("content")?.extract::<String>()?;
        let createtime = get_field("createtime")?.extract::<String>()?;
        let updatetime = get_field("updatetime")?.extract::<String>()?;
        let result = get_field("result")?.extract::<String>()?;
        let priority = get_field("priority")?.extract::<i32>()?;
        let source = get_field("source")?.extract::<String>()?;
        let destination = get_field("destination")?.extract::<String>()?;
        let retry_count = get_field("retry_count")?.extract::<i32>()?;
        let expire_time = get_field("expire_time")?.extract::<String>()?;
        let tags = get_field("tags")?.extract::<String>()?;
        let metadata = get_field("metadata")?.extract::<String>()?;

        let tx = conn
            .transaction()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        tx.execute(
            "
            INSERT INTO messages (
                id, type, status, content, createtime, 
                updatetime, result, priority, source, 
                destination, retry_count, expire_time, tags, metadata
            ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14)
            ",
            params![
                id,
                type_,
                status,
                content,
                createtime,
                updatetime,
                result,
                priority,
                source,
                destination,
                retry_count,
                expire_time,
                tags,
                metadata
            ],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        tx.commit()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(Bound::from(PyString::new(py, &id)))
    }

    pub fn dequeue<'py>(&self, py: Python<'py>, size: i32) -> PyResult<Bound<'py, PyList>> {
        let conn = self
            .pool
            .get()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let now: DateTime<Utc> = Utc::now();
        let iso_format = now.to_rfc3339();

        // Fixed SQL query with proper subquery alias
        let mut stmt = conn
            .prepare(
                "UPDATE messages
                SET status = 1
                WHERE id IN (
                    SELECT id
                    FROM (
                        SELECT id, ROW_NUMBER() OVER (ORDER BY priority DESC, createtime ASC) AS rn
                        FROM messages
                        WHERE is_deleted = 0
                        AND status = 0
                        AND (expire_time IS NULL OR expire_time > ?1)
                    ) AS sub
                    WHERE rn <= ?2
                )
                RETURNING *;",
            )
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let rows = PyList::empty(py);
        let mapped_rows = stmt
            .query_map(params![iso_format, size], |row| {
                let dict = PyDict::new(py);

                // Helper to convert PyErr to rusqlite::Error
                let to_rusqlite_error =
                    |e: PyErr| rusqlite::Error::ToSqlConversionFailure(Box::new(e));

                // Extract and set each field with proper error handling
                dict.set_item("id", row.get::<_, String>("id")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("type", row.get::<_, String>("type")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("status", row.get::<_, i32>("status")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("content", row.get::<_, String>("content")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("createtime", row.get::<_, String>("createtime")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("updatetime", row.get::<_, String>("updatetime")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("result", row.get::<_, Option<String>>("result")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("priority", row.get::<_, i32>("priority")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("source", row.get::<_, Option<String>>("source")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("destination", row.get::<_, Option<String>>("destination")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("retry_count", row.get::<_, i32>("retry_count")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("expire_time", row.get::<_, Option<String>>("expire_time")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("tags", row.get::<_, Option<String>>("tags")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("metadata", row.get::<_, Option<String>>("metadata")?)
                    .map_err(to_rusqlite_error)?;

                // Return the dictionary as Py<PyDict>
                Ok(dict)
            })
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        for row in mapped_rows {
            let dict =
                row.map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
            rows.append(dict)?;
        }

        Ok(rows.into())
    }

    pub fn get_queue_length(&self) -> PyResult<i32> {
        let conn = self
            .pool
            .get()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let now = Utc::now().to_rfc3339();

        // Using query_row for single result handling
        let count: i32 = conn
            .query_row(
                "SELECT COUNT(*) FROM messages 
                WHERE is_deleted = 0 
                AND status = ?1 
                AND (expire_time IS NULL OR expire_time > ?2)",
                params![0, now],
                |row| row.get(0),
            )
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(count)
    }
    pub fn get_completed_messages<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        let conn = self
            .pool
            .get()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let mut stmt = conn
            .prepare(
                "SELECT 
                    * 
                FROM 
                    messages 
                WHERE 
                    is_deleted = 0 
                    AND (status = ?1 OR status = ?2)",
            )
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let rows = PyList::empty(py);
        let mapped_rows = stmt
            .query_map(params![2, 3], |row| {
                let dict = PyDict::new(py);

                // Helper to convert PyErr to rusqlite::Error
                let to_rusqlite_error =
                    |e: PyErr| rusqlite::Error::ToSqlConversionFailure(Box::new(e));

                // Extract and set each field with proper error handling
                dict.set_item("id", row.get::<_, String>("id")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("type", row.get::<_, String>("type")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("status", row.get::<_, i32>("status")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("content", row.get::<_, String>("content")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("createtime", row.get::<_, String>("createtime")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("updatetime", row.get::<_, String>("updatetime")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("result", row.get::<_, Option<String>>("result")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("priority", row.get::<_, i32>("priority")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("source", row.get::<_, Option<String>>("source")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("destination", row.get::<_, Option<String>>("destination")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("retry_count", row.get::<_, i32>("retry_count")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("expire_time", row.get::<_, Option<String>>("expire_time")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("tags", row.get::<_, Option<String>>("tags")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("metadata", row.get::<_, Option<String>>("metadata")?)
                    .map_err(to_rusqlite_error)?;

                // Return the dictionary as Py<PyDict>
                Ok(dict)
            })
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        for row in mapped_rows {
            let dict =
                row.map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
            rows.append(dict)?;
        }

        Ok(rows.into())
    }

    pub fn get_result<'py>(&self, py: Python<'py>, id: String) -> PyResult<Bound<'py, PyDict>> {
        let conn = self
            .pool
            .get()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let mut stmt = conn
            .prepare(
                "SELECT result, status FROM messages WHERE id = ?1 AND (status = ?2 OR status = ?3)",
            )
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let mut mapped_rows = stmt
            .query_map(params![&id, 2, 3], |row| {
                let dict = PyDict::new(py);

                // Helper to convert PyErr to rusqlite::Error
                let to_rusqlite_error =
                    |e: PyErr| rusqlite::Error::ToSqlConversionFailure(Box::new(e));

                // Extract and set each field with proper error handling
                dict.set_item("id", row.get::<_, String>("id")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("type", row.get::<_, String>("type")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("status", row.get::<_, i32>("status")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("content", row.get::<_, String>("content")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("createtime", row.get::<_, String>("createtime")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("updatetime", row.get::<_, String>("updatetime")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("result", row.get::<_, Option<String>>("result")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("priority", row.get::<_, i32>("priority")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("source", row.get::<_, Option<String>>("source")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("destination", row.get::<_, Option<String>>("destination")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("retry_count", row.get::<_, i32>("retry_count")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("expire_time", row.get::<_, Option<String>>("expire_time")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("tags", row.get::<_, Option<String>>("tags")?)
                    .map_err(to_rusqlite_error)?;

                dict.set_item("metadata", row.get::<_, Option<String>>("metadata")?)
                    .map_err(to_rusqlite_error)?;

                // Return the dictionary as Py<PyDict>
                Ok(dict)
            })
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let dict = mapped_rows
            .next()
            .transpose()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(dict.unwrap().into())
    }

    pub fn update_status(&self, id: String, status: i32) -> PyResult<()> {
        let conn = self
            .pool
            .get()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        conn.execute(
            "
            UPDATE messages SET status = ?1 WHERE id = ?2
            ",
            params![status, id],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(())
    }

    pub fn update_result(&self, id: String, result: String) -> PyResult<()> {
        let conn = self
            .pool
            .get()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        conn.execute(
            "
            UPDATE messages SET result = ?1 WHERE id = ?2
            ",
            params![result, id],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(())
    }

    pub fn delete_message(&self, id: String) -> PyResult<()> {
        let conn = self
            .pool
            .get()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        conn.execute(
            "
            UPDATE messages SET is_deleted = 1 WHERE id = ?1
            ",
            params![id],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(())
    }

    pub fn clean_expired_messages(&self) -> PyResult<()> {
        let now: DateTime<Utc> = Utc::now();
        let iso_format = now.to_rfc3339();
        let conn = self
            .pool
            .get()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        conn.execute(
            "
            UPDATE messages 
            SET is_deleted = 1 
            WHERE is_deleted = 0
            AND expire_time IS NOT NULL
            AND expire_time < ?1
            ",
            params![iso_format],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(())
    }

    pub fn clean_old_messages(&self, days: i64) -> PyResult<()> {
        // 获取七天前的时间
        let now: DateTime<Utc> = Utc::now();
        let mut old_time = now - Duration::days(days);
        let iso_format = old_time.to_rfc3339();
        let conn = self
            .pool
            .get()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        conn.execute(
            "
            UPDATE messages 
            SET is_deleted = 1 
            WHERE is_deleted = 0
            AND status IN (?1, ?2)
            AND updatetime < ?3
            ",
            params![2, 3, iso_format],
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(())
    }
}
