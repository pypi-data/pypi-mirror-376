use ::file_type::format::SourceType as NativeSourceType;
use ::file_type::FileType as NativeFileType;
use pyo3::{exceptions::PyException, prelude::*};

#[pyclass]
enum SourceType {
    Default = NativeSourceType::Default as isize,
    Httpd = NativeSourceType::Httpd as isize,
    Iana = NativeSourceType::Iana as isize,
    Linguist = NativeSourceType::Linguist as isize,
    Pronom = NativeSourceType::Pronom as isize,
    Wikidata = NativeSourceType::Wikidata as isize,
}

#[pymodule]
mod file_type {
    #[pymodule_export]
    use super::filetype_from_bytes;
    #[pymodule_export]
    use super::filetype_from_extension;
    #[pymodule_export]
    use super::filetype_from_file;
    #[pymodule_export]
    use super::filetype_from_media_type;
    #[pymodule_export]
    use super::FileType;
}

#[pyclass]
struct FileType(NativeFileType);

#[pymethods]
impl FileType {
    /// Get the file type identifier.
    fn id(&self) -> usize {
        self.0.id()
    }
    /// Get the human-readable name of the file type
    fn name(&self) -> String {
        self.0.name().to_string()
    }
    /// Get the source for this file type.
    fn source_type(&self) -> SourceType {
        match self.0.source_type() {
            NativeSourceType::Default => SourceType::Default,
            NativeSourceType::Httpd => SourceType::Httpd,
            NativeSourceType::Iana => SourceType::Iana,
            NativeSourceType::Linguist => SourceType::Linguist,
            NativeSourceType::Pronom => SourceType::Pronom,
            NativeSourceType::Wikidata => SourceType::Wikidata,
        }
    }
    /// Get the file type extensions
    fn extensions(&self) -> Vec<String> {
        self.0
            .extensions()
            .iter()
            .map(|f| f.to_string())
            .collect::<Vec<_>>()
    }
}

/// Attempt to determine the FileType from a file path.
#[pyfunction]
fn filetype_from_file(path: String) -> PyResult<FileType> {
    match NativeFileType::try_from_file(path) {
        Ok(ft) => Ok(FileType(ft.clone())),
        Err(err) => Err(PyException::new_err(err.to_string())),
    }
}

/// Attempt to determine the FileType from a sequence of bytes.
#[pyfunction]
fn filetype_from_bytes(bytes: Vec<u8>) -> PyResult<FileType> {
    Ok(FileType(NativeFileType::from_bytes(bytes).clone()))
}

/// Get the file types for a given media type.
#[pyfunction]
fn filetype_from_media_type(typ: String) -> PyResult<Vec<FileType>> {
    Ok(NativeFileType::from_media_type(typ)
        .iter()
        .map(|f| FileType((*f).clone()))
        .collect::<Vec<_>>())
}

/// Get the file types for a given extension.
#[pyfunction]
fn filetype_from_extension(typ: String) -> PyResult<Vec<FileType>> {
    Ok(NativeFileType::from_extension(typ)
        .iter()
        .map(|f| FileType((*f).clone()))
        .collect::<Vec<_>>())
}
